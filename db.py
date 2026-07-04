# db.py
# Barcha so'rovlar PARAMETRLASHTIRILGAN (SQL-injection'dan 100% himoyalangan).
# Hech qachon foydalanuvchi matnini f-string / % orqali SQL ichiga qo'ymang.

import sqlite3
import os
import time
from contextlib import contextmanager
from config import DB_PATH, log

os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")   # bir vaqtda o'qish/yozishga chidamli
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
        conn.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user   INTEGER NOT NULL,
            to_user     INTEGER NOT NULL,
            reaction    TEXT NOT NULL CHECK(reaction IN ('like','skip')),
            created_at  INTEGER NOT NULL,
            UNIQUE(from_user, to_user),
            FOREIGN KEY(from_user) REFERENCES users(user_id),
            FOREIGN KEY(to_user) REFERENCES users(user_id)
        );
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_a      INTEGER NOT NULL,
            user_b      INTEGER NOT NULL,
            created_at  INTEGER NOT NULL,
            UNIQUE(user_a, user_b)
        );
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter    INTEGER NOT NULL,
            reported    INTEGER NOT NULL,
            reason      TEXT,
            created_at  INTEGER NOT NULL
        );
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key    TEXT PRIMARY KEY,
            value  TEXT
        );
        """)
    log.info(f"Baza tayyor: {DB_PATH}")


# ---------- SETTINGS (admin panel orqali o'zgartiriladigan sozlamalar) ----------

def get_setting(key: str, default: str = None):
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default


def set_setting(key: str, value: str):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, value))


def get_required_channels() -> list[str]:
    """Bir nechta majburiy kanal/guruh bo'lishi mumkin, vergul bilan ajratilgan saqlanadi."""
    raw = get_setting("required_channels", "")
    return [c.strip() for c in raw.split(",") if c.strip()]


def add_required_channel(channel: str):
    channels = get_required_channels()
    if channel not in channels:
        channels.append(channel)
    set_setting("required_channels", ",".join(channels))


def remove_required_channel(channel: str):
    channels = [c for c in get_required_channels() if c != channel]
    set_setting("required_channels", ",".join(channels))


# ---------- USERS ----------

def upsert_user_field(user_id: int, **fields):
    if not fields:
        return
    cols = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [user_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE users SET {cols} WHERE user_id = ?", values)


def create_or_update_profile(user_id, username, full_name, age, gender,
                              region, district, bio, photo_id):
    now = int(time.time())
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO users (user_id, username, full_name, age, gender,
                                region, district, bio, photo_id, created_at, last_seen)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                full_name=excluded.full_name,
                age=excluded.age,
                gender=excluded.gender,
                region=excluded.region,
                district=excluded.district,
                bio=excluded.bio,
                photo_id=excluded.photo_id,
                is_active=1,
                last_seen=excluded.last_seen
        """, (user_id, username, full_name, age, gender, region, district,
              bio, photo_id, now, now))


def get_user(user_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def touch_last_seen(user_id: int):
    with get_conn() as conn:
        conn.execute("UPDATE users SET last_seen = ? WHERE user_id = ?", (int(time.time()), user_id))


def deactivate_profile(user_id: int):
    with get_conn() as conn:
        conn.execute("UPDATE users SET is_active = 0 WHERE user_id = ?", (user_id,))


def ban_user(user_id: int, banned: bool = True):
    with get_conn() as conn:
        conn.execute("UPDATE users SET is_banned = ? WHERE user_id = ?", (1 if banned else 0, user_id))


def set_vip(user_id: int, until_ts: int):
    with get_conn() as conn:
        conn.execute("UPDATE users SET is_vip = 1, vip_until = ? WHERE user_id = ?", (until_ts, user_id))


def is_vip_active(user):
    return bool(user.get("is_vip")) and user.get("vip_until", 0) > int(time.time())


# ---------- BROWSING ----------

def get_next_profile(current_user_id: int, gender_filter: str, region_filter: str = None):
    """
    current_user ko'rmagan, faol, ban qilinmagan, qarama-qarshi jinsdagi keyingi profil.
    VIP foydalanuvchilar uchun region_filter=None -> butun O'zbekiston bo'yicha qidiradi.
    Oddiy foydalanuvchilar uchun faqat o'z regioni bo'yicha.
    """
    with get_conn() as conn:
        query = """
            SELECT * FROM users
            WHERE user_id != ?
              AND gender = ?
              AND is_active = 1
              AND is_banned = 0
              AND user_id NOT IN (
                  SELECT to_user FROM likes WHERE from_user = ?
              )
        """
        params = [current_user_id, gender_filter, current_user_id]
        if region_filter:
            query += " AND region = ?"
            params.append(region_filter)
        query += " ORDER BY RANDOM() LIMIT 1"
        row = conn.execute(query, params).fetchone()
        return dict(row) if row else None


def record_reaction(from_user: int, to_user: int, reaction: str):
    now = int(time.time())
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO likes (from_user, to_user, reaction, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(from_user, to_user) DO UPDATE SET reaction=excluded.reaction
        """, (from_user, to_user, reaction, now))

        is_match = False
        if reaction == "like":
            mutual = conn.execute("""
                SELECT 1 FROM likes WHERE from_user = ? AND to_user = ? AND reaction = 'like'
            """, (to_user, from_user)).fetchone()
            if mutual:
                a, b = sorted([from_user, to_user])
                conn.execute("""
                    INSERT OR IGNORE INTO matches (user_a, user_b, created_at)
                    VALUES (?, ?, ?)
                """, (a, b, now))
                is_match = True
        return is_match


def add_report(reporter: int, reported: int, reason: str = ""):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO reports (reporter, reported, reason, created_at)
            VALUES (?, ?, ?, ?)
        """, (reporter, reported, reason, int(time.time())))


# ---------- ADMIN STATS ----------

def get_stats():
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
        active = conn.execute("SELECT COUNT(*) c FROM users WHERE is_active=1 AND is_banned=0").fetchone()["c"]
        male = conn.execute("SELECT COUNT(*) c FROM users WHERE gender='male'").fetchone()["c"]
        female = conn.execute("SELECT COUNT(*) c FROM users WHERE gender='female'").fetchone()["c"]
        matches = conn.execute("SELECT COUNT(*) c FROM matches").fetchone()["c"]
        banned = conn.execute("SELECT COUNT(*) c FROM users WHERE is_banned=1").fetchone()["c"]
        vip = conn.execute("SELECT COUNT(*) c FROM users WHERE is_vip=1 AND vip_until > ?",
                            (int(time.time()),)).fetchone()["c"]
        return {
            "total": total, "active": active, "male": male, "female": female,
            "matches": matches, "banned": banned, "vip": vip,
        }


def get_all_active_user_ids():
    with get_conn() as conn:
        rows = conn.execute("SELECT user_id FROM users WHERE is_banned = 0").fetchall()
        return [r["user_id"] for r in rows]
