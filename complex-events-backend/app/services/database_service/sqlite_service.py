import json
import os
import sqlite3
import uuid
from datetime import datetime
from typing import Any
from flask import Flask

current_app: Flask | None = None

DOCUMENTS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    collection TEXT NOT NULL,
    doc TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
)
"""


class SQLiteCursor:
    def __init__(self, docs: list[dict[str, Any]]):
        self.docs = docs
        self._skip = 0
        self._limit = None

    def skip(self, num: int):
        self._skip = max(0, int(num))
        return self

    def limit(self, num: int):
        if num is None:
            return self
        self._limit = int(num)
        return self

    def __iter__(self):
        docs = self.docs[self._skip :]
        if self._limit is not None:
            docs = docs[: self._limit]
        return iter(docs)

    def __len__(self):
        docs = self.docs[self._skip :]
        return len(docs) if self._limit is None else len(docs[: self._limit])


class UpdateResult:
    def __init__(self, matched_count: int = 0, modified_count: int = 0, upserted_id: str | None = None):
        self.matched_count = matched_count
        self.modified_count = modified_count
        self.upserted_id = upserted_id


class SQLiteCollection:
    def __init__(self, name: str):
        self.name = name

    def find(self, query: dict | None = None):
        docs = self._apply_query(query)
        return SQLiteCursor(docs)

    def find_one(self, query: dict | None = None):
        docs = self._apply_query(query)
        return docs[0] if docs else None

    def count_documents(self, query: dict | None = None):
        return len(self._apply_query(query))

    def insert_one(self, doc: dict[str, Any]):
        if not isinstance(doc, dict):
            raise ValueError("Document must be a dict")
        if "id" not in doc or doc.get("id") is None:
            doc["id"] = uuid.uuid4().hex
        now = datetime.utcnow().isoformat()
        doc.setdefault("created_at", now)
        doc["updated_at"] = now
        self._save_doc(doc)
        return type("InsertResult", (), {"inserted_id": doc["id"]})()

    def update_one(self, filter_query: dict, update_doc: dict, upsert: bool = False):
        docs = self._apply_query(filter_query)
        result = UpdateResult()
        if docs:
            doc = docs[0]
            update_fields = self._extract_update_fields(update_doc)
            modified = False
            for key, value in update_fields.items():
                if doc.get(key) != value:
                    doc[key] = value
                    modified = True
            if modified:
                self._save_doc(doc)
            result.matched_count = 1
            result.modified_count = 1 if modified else 0
        elif upsert:
            new_doc = {}
            if isinstance(filter_query, dict):
                new_doc.update(filter_query)
            update_fields = self._extract_update_fields(update_doc)
            new_doc.update(update_fields)
            if "id" not in new_doc or new_doc.get("id") is None:
                new_doc["id"] = uuid.uuid4().hex
            now = datetime.utcnow().isoformat()
            new_doc.setdefault("created_at", now)
            new_doc["updated_at"] = now
            self._save_doc(new_doc)
            result.upserted_id = new_doc["id"]
            result.matched_count = 0
            result.modified_count = 1
        return result

    def _extract_update_fields(self, update_doc: dict) -> dict[str, Any]:
        if not isinstance(update_doc, dict):
            return {}
        if "$set" in update_doc and isinstance(update_doc["$set"], dict):
            return update_doc["$set"]
        return update_doc

    def _apply_query(self, query: dict | None = None) -> list[dict[str, Any]]:
        docs = self._load_all_documents()
        if not query:
            return docs
        return [doc for doc in docs if self._matches(doc, query)]

    def _load_all_documents(self) -> list[dict[str, Any]]:
        conn = get_connection()
        cursor = conn.execute(
            "SELECT doc FROM documents WHERE collection = ? ORDER BY rowid",
            (self.name,),
        )
        rows = cursor.fetchall()
        conn.close()
        result: list[dict[str, Any]] = []
        for row in rows:
            try:
                result.append(json.loads(row[0]))
            except json.JSONDecodeError:
                continue
        return result

    def _save_doc(self, doc: dict[str, Any]):
        doc_json = json.dumps(doc, ensure_ascii=False)
        now = datetime.utcnow().isoformat()
        conn = get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO documents (id, collection, doc, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (
                str(doc["id"]),
                self.name,
                doc_json,
                doc.get("created_at", now),
                now,
            ),
        )
        conn.commit()
        conn.close()

    def _matches(self, doc: dict[str, Any], query: dict[str, Any]) -> bool:
        for key, expected in query.items():
            if key == "$or" and isinstance(expected, list):
                if not any(self._matches(doc, sub_query) for sub_query in expected):
                    return False
                continue
            if key == "$and" and isinstance(expected, list):
                if not all(self._matches(doc, sub_query) for sub_query in expected):
                    return False
                continue
            value = self._get_nested_value(doc, key)
            if isinstance(expected, dict):
                if "$exists" in expected:
                    exists = value is not None
                    if bool(expected["$exists"]) != exists:
                        return False
                if "$ne" in expected and value == expected["$ne"]:
                    return False
                if "$in" in expected and value not in expected["$in"]:
                    return False
                if "$nin" in expected and value in expected["$nin"]:
                    return False
                if all(k not in ["$exists", "$ne", "$in", "$nin"] for k in expected):
                    if isinstance(value, dict):
                        if not self._matches(value, expected):
                            return False
                    elif value != expected:
                        return False
            else:
                if value != expected:
                    return False
        return True

    def _get_nested_value(self, doc: dict[str, Any], key: str) -> Any:
        if "." in key:
            current = doc
            for part in key.split("."):
                if not isinstance(current, dict) or part not in current:
                    return None
                current = current[part]
            return current
        return doc.get(key)


def _ensure_current_app(app: Flask):
    global current_app
    current_app = app


def get_connection():
    if current_app is None:
        raise RuntimeError("SQLite service has not been initialized with an application")
    db_path = current_app.config.get("SQLITE_DB_PATH")
    if not db_path:
        raise RuntimeError("SQLITE_DB_PATH is not configured")
    if not os.path.isabs(db_path):
        project_root = os.path.abspath(os.path.join(current_app.root_path, ".."))
        db_path = os.path.normpath(os.path.join(project_root, db_path))
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute(DOCUMENTS_TABLE_SCHEMA)
    conn.commit()
    return conn


def check_sqlite_status(app: Flask) -> bool:
    _ensure_current_app(app)
    try:
        conn = get_connection()
        conn.execute("SELECT 1")
        conn.close()
        current_app.logger.info("SQLite Connect Status: SUCCESS")
        return True
    except Exception as e:
        app.logger.error(f"SQLite Connect Status: FAILED, {str(e)}")
        return False


def get_collection(name: str) -> SQLiteCollection:
    if current_app is None:
        raise RuntimeError("SQLite service has not been initialized with an application")
    return SQLiteCollection(name)


def get_reports_collection():
    return get_collection(current_app.config.get("SQLITE_REPORTS_COLLECTION", "reports"))


def get_extract_result_collection():
    return get_collection(current_app.config.get("SQLITE_EXTRACT_RESULT_COLLECTION", "extract_results"))


def get_event_link_collection():
    return get_collection(current_app.config.get("SQLITE_EVENT_LINK_COLLECTION", "event_links"))


def get_sub_graph_collection():
    return get_collection(current_app.config.get("SQLITE_SUB_GRAPH_COLLECTION", "sub_graph"))


def get_event_link_rules_collection():
    return get_collection(current_app.config.get("SQLITE_EVENT_LINK_RULES_COLLECTION", "event_link_rules"))
