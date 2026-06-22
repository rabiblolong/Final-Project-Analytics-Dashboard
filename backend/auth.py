"""
backend/auth.py
Simple SQLite-based authentication (no external auth server needed).
Uses werkzeug for password hashing.
"""
import sqlite3, os, uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'users.db')


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    """Create users table if not exists."""
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id       TEXT PRIMARY KEY,
                email    TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name     TEXT NOT NULL,
                created  TEXT NOT NULL
            )
        """)
        c.commit()


def register_user(email: str, password: str, name: str) -> dict:
    """
    Register new user.
    Returns {'ok': True, 'user': {...}} or {'ok': False, 'error': '...'}
    """
    email = email.strip().lower()
    if not email or '@' not in email:
        return {'ok': False, 'error': 'Email tidak valid.'}
    if len(password) < 6:
        return {'ok': False, 'error': 'Sandi minimal 6 karakter.'}
    if not name.strip():
        return {'ok': False, 'error': 'Nama tidak boleh kosong.'}

    try:
        uid = str(uuid.uuid4())
        pw_hash = generate_password_hash(password)
        created = datetime.now().isoformat()
        with _conn() as c:
            c.execute(
                "INSERT INTO users (id, email, password, name, created) VALUES (?,?,?,?,?)",
                (uid, email, pw_hash, name.strip(), created)
            )
            c.commit()
        return {'ok': True, 'user': {'id': uid, 'email': email, 'name': name.strip()}}
    except sqlite3.IntegrityError:
        return {'ok': False, 'error': 'Email sudah terdaftar.'}
    except Exception as e:
        return {'ok': False, 'error': f'Gagal registrasi: {str(e)}'}


def login_user(email: str, password: str) -> dict:
    """
    Verify credentials.
    Returns {'ok': True, 'user': {...}} or {'ok': False, 'error': '...'}
    """
    email = email.strip().lower()
    try:
        with _conn() as c:
            row = c.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if not row:
            return {'ok': False, 'error': 'Email tidak ditemukan.'}
        if not check_password_hash(row['password'], password):
            return {'ok': False, 'error': 'Sandi salah.'}
        return {'ok': True, 'user': {'id': row['id'], 'email': row['email'], 'name': row['name']}}
    except Exception as e:
        return {'ok': False, 'error': f'Gagal login: {str(e)}'}


def get_user_by_id(uid: str) -> dict | None:
    try:
        with _conn() as c:
            row = c.execute("SELECT id, email, name FROM users WHERE id=?", (uid,)).fetchone()
        return dict(row) if row else None
    except:
        return None


# Initialise on import
init_db()