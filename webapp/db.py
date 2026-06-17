"""
SQLite 数据库层：表初始化 + 用例/执行记录 CRUD。
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "webapp.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS testcases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT '',
            method TEXT DEFAULT 'GET',
            path TEXT DEFAULT '',
            headers TEXT DEFAULT '',
            body TEXT DEFAULT '',
            expected_status INTEGER DEFAULT 200,
            expected_contains TEXT DEFAULT '',
            category TEXT DEFAULT 'smoke',
            extract_path TEXT DEFAULT '',
            save_as TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS test_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_filename TEXT NOT NULL,
            total INTEGER DEFAULT 0,
            passed INTEGER DEFAULT 0,
            failed INTEGER DEFAULT 0,
            skipped INTEGER DEFAULT 0,
            duration REAL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
    """)
    conn.commit()
    conn.close()


# ── 用例 CRUD ──

def case_row_to_dict(row) -> dict:
    if not row:
        return None
    return dict(row)


def list_testcases(category: str = None) -> list:
    conn = get_db()
    if category:
        rows = conn.execute(
            "SELECT * FROM testcases WHERE category=? ORDER BY id", (category,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM testcases ORDER BY id").fetchall()
    conn.close()
    return [case_row_to_dict(r) for r in rows]


def get_testcase_by_case_id(case_id: str) -> dict:
    conn = get_db()
    row = conn.execute("SELECT * FROM testcases WHERE case_id=?", (case_id,)).fetchone()
    conn.close()
    return case_row_to_dict(row)


def get_testcase_by_id(id: int) -> dict:
    conn = get_db()
    row = conn.execute("SELECT * FROM testcases WHERE id=?", (id,)).fetchone()
    conn.close()
    return case_row_to_dict(row)


def create_testcase(data: dict) -> int:
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO testcases
           (case_id, description, method, path, headers, body,
            expected_status, expected_contains, category, extract_path, save_as)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (
            data["case_id"],
            data.get("description", ""),
            data.get("method", "GET"),
            data.get("path", ""),
            data.get("headers", ""),
            data.get("body", ""),
            data.get("expected_status", 200),
            data.get("expected_contains", ""),
            data.get("category", "smoke"),
            data.get("extract_path", ""),
            data.get("save_as", ""),
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_testcase(id: int, data: dict) -> bool:
    conn = get_db()
    conn.execute(
        """UPDATE testcases SET
           case_id=?, description=?, method=?, path=?, headers=?, body=?,
           expected_status=?, expected_contains=?, category=?,
           extract_path=?, save_as=?,
           updated_at=datetime('now','localtime')
           WHERE id=?""",
        (
            data["case_id"],
            data.get("description", ""),
            data.get("method", "GET"),
            data.get("path", ""),
            data.get("headers", ""),
            data.get("body", ""),
            data.get("expected_status", 200),
            data.get("expected_contains", ""),
            data.get("category", "smoke"),
            data.get("extract_path", ""),
            data.get("save_as", ""),
            id,
        ),
    )
    conn.commit()
    conn.close()
    return True


def delete_testcase(id: int):
    conn = get_db()
    conn.execute("DELETE FROM testcases WHERE id=?", (id,))
    conn.commit()
    conn.close()


# ── 运行记录 ──

def create_test_run(report_filename: str, total: int, passed: int,
                    failed: int, skipped: int, duration: float) -> int:
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO test_runs
           (report_filename, total, passed, failed, skipped, duration)
           VALUES (?,?,?,?,?,?)""",
        (report_filename, total, passed, failed, skipped, duration),
    )
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid


def list_test_runs(limit: int = 20) -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM test_runs ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [case_row_to_dict(r) for r in rows]


def get_test_run(id: int) -> dict:
    conn = get_db()
    row = conn.execute("SELECT * FROM test_runs WHERE id=?", (id,)).fetchone()
    conn.close()
    return case_row_to_dict(row)
