"""Проверки SQLite на временной БД: рабочая heatmap.db не затрагивается."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from database import connection
from main import app


class SQLiteAppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "test.db"
        self.engine = connection.create_sqlite_engine(self.path)
        self.addCleanup(self.engine.dispose)
        override = patch.object(connection, "engine", self.engine)
        override.start()
        self.addCleanup(override.stop)
        self.client = self.enterContext(TestClient(app, follow_redirects=False))

    def create_user(self, username="Иван", email="ivan@example.com"):
        response = self.client.post("/user", data={"username": username, "email": email})
        self.assertEqual(response.status_code, 303)
        return response

    def create_order(self, user_id=1, name="Учебный заказ"):
        response = self.client.post("/order", data={"name": name, "user_id": user_id})
        self.assertEqual(response.status_code, 303)
        return response

    def test_startup_creates_tables_and_pages(self):
        self.assertTrue(self.path.exists())
        with self.engine.connect() as db:
            tables = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).scalars().all()
        self.assertIn("users", tables)
        self.assertIn("orders", tables)
        for url in ("/", "/users", "/order", "/docs", "/openapi.json"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_user_crud_and_non_reused_ids(self):
        self.create_user()
        self.create_user()
        self.assertIn("Иван", self.client.get("/users").text)
        response = self.client.put("/user/2", json={"username": "Пётр", "email": "petr@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"id": 2, "username": "Пётр", "email": "petr@example.com"})
        self.assertIn("Пётр", self.client.get("/user/2").text)
        self.assertEqual(self.client.delete("/user/2").json()["id"], 2)
        self.create_user()
        self.assertEqual(self.client.get("/user/2").status_code, 404)
        self.assertEqual(self.client.get("/user/3").status_code, 200)

    def test_order_crud_reassignment_and_user_protection(self):
        self.create_user()
        self.create_user("Анна", "anna@example.com")
        self.create_order()
        response = self.client.delete("/user/1")
        self.assertEqual(response.status_code, 409)
        self.assertIn("заказы", response.json()["detail"])
        response = self.client.put("/order/1", json={"name": "Другой заказ", "user_id": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"id": 1, "name": "Другой заказ", "user_id": 2})
        self.assertIn("Анна", self.client.get("/order/1").text)
        self.assertEqual(self.client.delete("/user/1").status_code, 200)
        self.assertEqual(self.client.delete("/order/1").json()["id"], 1)
        self.assertEqual(self.client.delete("/user/2").status_code, 200)
        self.assertEqual(self.client.get("/order/1").status_code, 404)

    def test_form_edit_and_delete(self):
        self.create_user()
        self.create_order()
        for url in ("/user/1?edit=true", "/order/1?edit=true"):
            self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.post("/user/1/edit", data={"username": "Новое имя", "email": "new@example.com"}).status_code, 303)
        order_page = self.client.get("/order/1").text
        self.assertIn("Новое имя", order_page)
        self.assertIn("new@example.com", order_page)
        self.assertEqual(self.client.post("/order/1/edit", data={"name": "Из формы", "user_id": 1}).status_code, 303)
        self.assertIn("Из формы", self.client.get("/order/1").text)
        response = self.client.post("/user/1/delete", headers={"accept": "text/html"})
        self.assertEqual(response.status_code, 409)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertEqual(self.client.post("/order/1/delete").status_code, 303)
        self.assertEqual(self.client.post("/user/1/delete").status_code, 303)

    def test_invalid_data_and_missing_records(self):
        self.assertEqual(self.client.post("/user", data={"username": "Иван", "email": "invalid"}).status_code, 422)
        self.assertEqual(self.client.post("/user", data={"username": "   ", "email": "ivan@example.com"}).status_code, 422)
        self.assertEqual(self.client.post("/order", data={"name": "Заказ", "user_id": 999}).status_code, 404)
        self.create_user()
        self.create_order()
        self.assertEqual(self.client.put("/order/1", json={"name": "Заказ", "user_id": 999}).status_code, 404)
        self.assertEqual(self.client.put("/order/1", json={"name": "Заказ", "user_id": 0}).status_code, 422)
        for url in ("/user/999", "/order/999"):
            self.assertEqual(self.client.get(url).status_code, 404)
            self.assertEqual(self.client.delete(url).status_code, 404)
        self.assertIn("Иван", self.client.get("/order/1").text)

    def test_database_itself_rejects_broken_foreign_keys(self):
        self.create_user()
        self.create_order()
        with self.engine.connect() as db:
            self.assertEqual(db.execute(text("PRAGMA foreign_keys")).scalar_one(), 1)
        with self.assertRaises(IntegrityError):
            with self.engine.begin() as db:
                db.execute(text("INSERT INTO orders (name, user_id) VALUES ('broken', 999)"))
        with self.assertRaises(IntegrityError):
            with self.engine.begin() as db:
                db.execute(text("DELETE FROM users WHERE id = 1"))
        self.assertEqual(self.client.get("/order/1").status_code, 200)

    def test_records_survive_a_new_process(self):
        self.create_user()
        self.create_order()
        script = '''
from fastapi.testclient import TestClient
from main import app
with TestClient(app, follow_redirects=False) as client:
    assert "Иван" in client.get("/user/1").text
    assert "Учебный заказ" in client.get("/order/1").text
    assert client.delete("/user/1").status_code == 409
    assert client.post("/user", data={"username": "Анна", "email": "anna@example.com"}).status_code == 303
    assert client.get("/user/2").status_code == 200
'''
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=Path(__file__).resolve().parents[1],
            env={**os.environ, "HEATMAP_DB_PATH": str(self.path)},
            text=True, capture_output=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Анна", self.client.get("/user/2").text)


if __name__ == "__main__":
    unittest.main()
