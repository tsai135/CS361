import os
import re
import sqlite3
import secrets
from datetime import datetime

from flask import Flask, jsonify, request
from werkzeug.security import generate_password_hash

APP_PORT = 5001
DB_FILE = os.environ.get("ACCOUNTS_DB_FILE", "accounts.db")

# Leave an explicit "secure path" option:
# - True  => store password_hash using werkzeug (recommended)
# - False => store plaintext password (NOT recommended; only for early demos)
USE_PASSWORD_HASHING = True

# "valid set of alphanumeric characters"
ALNUM_RE = re.compile(r"^[A-Za-z0-9]+$")


def create_app() -> Flask:
    app = Flask(__name__)
    init_db()

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "service": "accounts", "time_utc": datetime.utcnow().isoformat()}), 200

    @app.post("/accounts")
    def create_account():
        data = request.get_json(silent=True) or {}
        username = (data.get("username") or "").strip()
        password = (data.get("password") or "").strip()

        # Validate presence
        if not username or not password:
            return error_response(
                http_status=400,
                code="MISSING_FIELDS",
                message="Request must include non-empty 'username' and 'password'.",
            )

        # Validate alphanumeric constraints
        if not ALNUM_RE.match(username):
            return error_response(
                http_status=400,
                code="INVALID_USERNAME",
                message="Username must contain only alphanumeric characters (A-Z, a-z, 0-9).",
            )

        if not ALNUM_RE.match(password):
            return error_response(
                http_status=400,
                code="INVALID_PASSWORD",
                message="Password must contain only alphanumeric characters (A-Z, a-z, 0-9).",
            )

        # Create user id
        user_id = "u_" + secrets.token_hex(8)

        # Store password securely by default
        password_hash = generate_password_hash(password) if USE_PASSWORD_HASHING else None
        password_plain = password if not USE_PASSWORD_HASHING else None

        try:
            with db_conn() as conn:
                cur = conn.cursor()
                # Uniqueness guaranteed by UNIQUE constraint + handling IntegrityError
                cur.execute(
                    """
                    INSERT INTO accounts (user_id, username, password_hash, password_plain, created_at_utc)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, username, password_hash, password_plain, datetime.utcnow().isoformat()),
                )
                conn.commit()
        except sqlite3.IntegrityError:
            return error_response(
                http_status=409,
                code="USERNAME_EXISTS",
                message="Username already exists.",
            )
        except Exception:
            # Keep error stable for clients; avoid leaking internals
            return error_response(
                http_status=500,
                code="INTERNAL_ERROR",
                message="Something went wrong while creating the account.",
            )

        # IMPORTANT: never return passwords
        return jsonify(
            {
                "ok": True,
                "user_id": user_id,
                "username": username,
                "message": "Account created.",
            }
        ), 201

    return app


def init_db() -> None:
    with db_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT,
                password_plain TEXT,
                created_at_utc TEXT NOT NULL
            )
            """
        )
        conn.commit()


def db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def error_response(http_status: int, code: str, message: str):
    return (
        jsonify({"ok": False, "error": {"code": code, "message": message}}),
        http_status,
    )


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=APP_PORT, debug=True)