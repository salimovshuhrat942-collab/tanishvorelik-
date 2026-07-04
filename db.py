# db.py
import sqlite3
import os
import time
from contextlib import contextmanager
from config import DB_PATH, log

os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id      INTEGER PRIMARY KEY,
            username     TEXT,
            full_name    TEXT NOT NULL,
            age          INTEGER NOT NULL,
            gender       TEXT NOT NULL CHECK(gender IN ('male','female')),
            region       TEXT NOT NULL,
            district     TEXT NOT NULL,
            bio          TEXT DEFAULT '',
            photo_id     TEXT,
            is_active    INTEGER DEFAULT 1,
            is_banned    INTEGER DEFAULT 0,
            is_vip       INTEGER DEFAULT 0,
            vip_until    INTEGER DEFAULT 0,
            created_at   INTEGER NOT NULL,
            last_seen    INTEGER NOT NULL
        );
        """)
        # ... (qolgan jadval yaratish kodlari o'zgarishsiz qoladi)
        conn.execute("CREATE TABLE IF NOT EXISTS likes (id INTEGER PRIMARY KEY AUTOINCREMENT, from_user INTEGER NOT NULL, to_user INTEGER NOT NULL, reaction TEXT NOT NULL CHECK(reaction IN ('like','skip')), created_at INTEGER NOT NULL, UNIQUE(from_user, to_user), FOREIGN KEY(from_user) REFERENCES users(user_id), FOREIGN KEY(to_user) REFERENCES users(user_id));")
        conn.execute("CREATE TABLE IF NOT EXISTS matches (id INTEGER PRIMARY KEY AUTOINCREMENT, user_a INTEGER NOT NULL, user_b INTEGER NOT NULL, created_at INTEGER NOT NULL, UNIQUE(user_a, user_b));")
        conn.execute("CREATE TABLE IF NOT EXISTS reports (id INTEGER PRIMARY KEY AUTOINCREMENT, reporter INTEGER NOT NULL, reported INTEGER NOT NULL, reason TEXT, created_at INTEGER NOT NULL);")
        conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);")
    log.info(f"Baza tayyor: {DB_PATH}")

# ---------- SETTINGS ----------
def get_setting(key: str, default: str = None):
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

def set_setting(key: str, value: str):
    with get_conn() as conn:
        conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))

def get_required_channels() -> list[str]:
    raw = get_setting("required_channels", "")
    return [c.strip() for c in raw.split(",") if c.strip()]

def add_required_channel(channel: str):
    channels = get_required_channels()
    if channel not in channels: channels.append(channel)
    set_setting("required_channels", ",".join(channels))

def remove_required_channel(channel: str):
    channels = [c for c in get_required_channels() if c != channel]
    set_setting("required_channels", ",".join(channels))

# ---------- USERS ----------

def get_user(user_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

# TUG'RILANGAN VIP FUNKSIYALARI
def set_vip(user_id: int, until_ts: int):
    """Foydalanuvchiga VIP maqomini berish."""
    with get_conn() as conn:
        conn.execute("""
            UPDATE users 
            SET is_vip = 1, vip_until = ? 
            WHERE user_id = ?
        """, (until_ts, user_id))
    log.info(f"User {user_id} ga VIP berildi, muddati: {until_ts}")

def is_vip_active(user: dict) -> bool:
    """Foydalanuvchi VIP ekanligini va vaqti o'tmaganini tekshirish."""
    if not user: return False
    is_vip = bool(user.get("is_vip", 0))
    vip_until = user.get("vip_until", 0)
    return is_vip and (vip_until > int(time.time()))

# ---------- BROWSING & ACTIONS ----------
def ban_user(user_id: int, banned: bool = True):
    with get_conn() as conn:
        conn.execute("UPDATE users SET is_banned = ? WHERE user_id = ?", (1 if banned else 0, user_id))

def get_stats():
    with get_conn() as conn:
        now = int(time.time())
        total = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
        active = conn.execute("SELECT COUNT(*) c FROM users WHERE is_active=1 AND is_banned=0").fetchone()["c"]
        male = conn.execute("SELECT COUNT(*) c FROM users WHERE gender='male'").fetchone()["c"]
        female = conn.execute("SELECT COUNT(*) c FROM users WHERE gender='female'").fetchone()["c"]
        matches = conn.execute("SELECT COUNT(*) c FROM matches").fetchone()["c"]
        banned = conn.execute("SELECT COUNT(*) c FROM users WHERE is_banned=1").fetchone()["c"]
        vip = conn.execute("SELECT COUNT(*) c FROM users WHERE is_vip=1 AND vip_until > ?", (now,)).fetchone()["c"]
        return {"total": total, "active": active, "male": male, "female": female, "matches": matches, "banned": banned, "vip": vip}

def get_all_active_user_ids():
    with get_conn() as conn:
        rows = conn.execute("SELECT user_id FROM users WHERE is_banned = 0").fetchall()
        return [r["user_id"] for r in rows]
