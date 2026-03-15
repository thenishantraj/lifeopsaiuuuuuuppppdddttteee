import sqlite3
import hashlib
import uuid
from datetime import datetime, timedelta
import os

DB_PATH = os.environ.get("DATABASE_PATH", "lifeops_v2.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _safe_count(conn, sql, params=()):
    """Execute a COUNT query and safely return the integer result."""
    try:
        row = conn.execute(sql, params).fetchone()
        if row is None:
            return 0
        try:
            return int(row["c"])
        except (KeyError, IndexError, TypeError):
            return int(row[0])
    except Exception:
        return 0


class LifeOpsDatabase:

    def __init__(self):
        self._init_db()

    def _init_db(self):
        conn = get_conn()
        c = conn.cursor()

        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id                   TEXT PRIMARY KEY,
            email                TEXT UNIQUE NOT NULL,
            password_hash        TEXT NOT NULL,
            name                 TEXT NOT NULL,
            joined_at            TEXT NOT NULL,
            last_login           TEXT,
            theme                TEXT    DEFAULT 'light',
            notifications_email  INTEGER DEFAULT 1,
            notifications_push   INTEGER DEFAULT 1,
            notifications_weekly INTEGER DEFAULT 1,
            font_size            TEXT    DEFAULT 'Medium',
            is_verified          INTEGER DEFAULT 0
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS action_items (
            id           TEXT PRIMARY KEY,
            user_id      TEXT NOT NULL,
            task         TEXT NOT NULL,
            category     TEXT NOT NULL,
            source       TEXT    DEFAULT 'User',
            priority     TEXT    DEFAULT 'medium',
            completed    INTEGER DEFAULT 0,
            created_at   TEXT NOT NULL,
            completed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id          TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL,
            name        TEXT NOT NULL,
            dosage      TEXT,
            frequency   TEXT,
            time_of_day TEXT,
            active      INTEGER DEFAULT 1,
            created_at  TEXT NOT NULL,
            last_taken  TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id              TEXT PRIMARY KEY,
            user_id         TEXT NOT NULL,
            name            TEXT NOT NULL,
            amount          REAL NOT NULL,
            due_day         INTEGER NOT NULL,
            category        TEXT    DEFAULT 'Other',
            paid_this_month INTEGER DEFAULT 0,
            auto_pay        INTEGER DEFAULT 0,
            created_at      TEXT NOT NULL,
            last_paid       TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id         TEXT PRIMARY KEY,
            user_id    TEXT NOT NULL,
            title      TEXT NOT NULL,
            content    TEXT NOT NULL,
            tags       TEXT,
            pinned     INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS study_sessions (
            id                 TEXT PRIMARY KEY,
            user_id            TEXT NOT NULL,
            subject            TEXT NOT NULL,
            duration_minutes   INTEGER NOT NULL,
            productivity_score INTEGER DEFAULT 5,
            date               TEXT NOT NULL,
            notes              TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS health_logs (
            id            TEXT PRIMARY KEY,
            user_id       TEXT NOT NULL,
            date          TEXT NOT NULL,
            symptoms      TEXT,
            sleep_quality INTEGER,
            energy_level  INTEGER,
            water_intake  INTEGER,
            mood          INTEGER,
            weight        REAL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS daily_checkins (
            id      TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            date    TEXT NOT NULL,
            UNIQUE(user_id, date),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS ai_analyses (
            id                  TEXT PRIMARY KEY,
            user_id             TEXT NOT NULL,
            created_at          TEXT NOT NULL,
            health_result       TEXT,
            finance_result      TEXT,
            study_result        TEXT,
            coordination_result TEXT,
            score               INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")

        conn.commit()
        self._run_migrations(conn)
        conn.close()

    def _run_migrations(self, conn):
        try:
            rows = conn.execute("PRAGMA table_info(users)").fetchall()
            existing = [row[1] for row in rows]
            if "is_verified" not in existing:
                conn.execute(
                    "ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 0"
                )
                conn.commit()
        except Exception:
            pass

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def email_exists(self, email):
        try:
            conn = get_conn()
            row = conn.execute(
                "SELECT id FROM users WHERE email=?", (email.lower().strip(),)
            ).fetchone()
            conn.close()
            return row is not None
        except Exception:
            return False

    def create_user_unverified(self, email, password, name):
        try:
            conn = get_conn()
            uid = str(uuid.uuid4())
            now = datetime.now().isoformat()
            conn.execute(
                """INSERT INTO users
                       (id, email, password_hash, name, joined_at, is_verified)
                   VALUES (?, ?, ?, ?, ?, 0)
                   ON CONFLICT(email) DO UPDATE SET
                       password_hash = excluded.password_hash,
                       name          = excluded.name,
                       is_verified   = 0""",
                (uid, email.lower().strip(), self._hash_password(password), name, now),
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def verify_user_email(self, email):
        try:
            conn = get_conn()
            conn.execute(
                "UPDATE users SET is_verified=1 WHERE email=?",
                (email.lower().strip(),),
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def delete_unverified_user(self, email):
        try:
            conn = get_conn()
            conn.execute(
                "DELETE FROM users WHERE email=? AND is_verified=0",
                (email.lower().strip(),),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def create_user(self, email, password, name):
        try:
            conn = get_conn()
            uid = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO users
                   (id, email, password_hash, name, joined_at, is_verified)
                   VALUES (?, ?, ?, ?, ?, 1)""",
                (uid, email.lower().strip(), self._hash_password(password),
                 name, datetime.now().isoformat()),
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def authenticate_user(self, email, password):
        try:
            conn = get_conn()
            row = conn.execute(
                "SELECT * FROM users WHERE email=? AND password_hash=?",
                (email.lower().strip(), self._hash_password(password)),
            ).fetchone()
            if row is None:
                conn.close()
                return None
            user = dict(row)
            if not user.get("is_verified", 0):
                conn.close()
                return "unverified"
            conn.execute(
                "UPDATE users SET last_login=? WHERE id=?",
                (datetime.now().isoformat(), user["id"]),
            )
            conn.commit()
            conn.close()
            return user
        except Exception:
            return None

    def get_user(self, user_id):
        try:
            conn = get_conn()
            row = conn.execute(
                "SELECT * FROM users WHERE id=?", (user_id,)
            ).fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception:
            return None

    def update_user_settings(self, user_id, settings):
        try:
            conn = get_conn()
            allowed = [
                "name", "theme", "notifications_email",
                "notifications_push", "notifications_weekly", "font_size",
            ]
            fields, values = [], []
            for k, v in settings.items():
                if k in allowed:
                    fields.append(k + "=?")
                    values.append(v)
            if not fields:
                conn.close()
                return False
            values.append(user_id)
            conn.execute(
                "UPDATE users SET " + ", ".join(fields) + " WHERE id=?", values
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def change_password(self, user_id, old_password, new_password):
        try:
            conn = get_conn()
            row = conn.execute(
                "SELECT password_hash FROM users WHERE id=?", (user_id,)
            ).fetchone()
            if row is None:
                conn.close()
                return False
            try:
                stored = row["password_hash"]
            except (KeyError, IndexError):
                stored = row[0]
            if stored != self._hash_password(old_password):
                conn.close()
                return False
            conn.execute(
                "UPDATE users SET password_hash=? WHERE id=?",
                (self._hash_password(new_password), user_id),
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def reset_password_by_email(self, email, new_password):
        try:
            conn = get_conn()
            result = conn.execute(
                "UPDATE users SET password_hash=? WHERE email=? AND is_verified=1",
                (self._hash_password(new_password), email.lower().strip()),
            )
            changed = result.rowcount > 0
            conn.commit()
            conn.close()
            return changed
        except Exception:
            return False

    def is_email_verified(self, email):
        try:
            conn = get_conn()
            row = conn.execute(
                "SELECT is_verified FROM users WHERE email=?",
                (email.lower().strip(),),
            ).fetchone()
            conn.close()
            if row is None:
                return False
            try:
                return bool(row["is_verified"])
            except (KeyError, IndexError):
                return bool(row[0])
        except Exception:
            return False

    def add_action_item(self, user_id, task, category, source="User", priority="medium"):
        try:
            conn = get_conn()
            item_id = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO action_items
                   (id, user_id, task, category, source, priority, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (item_id, user_id, task, category, source, priority,
                 datetime.now().isoformat()),
            )
            conn.commit()
            conn.close()
            self._record_checkin(user_id)
            return item_id
        except Exception:
            return None

    def get_pending_actions(self, user_id):
        try:
            conn = get_conn()
            rows = conn.execute(
                "SELECT * FROM action_items WHERE user_id=? AND completed=0 "
                "ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def get_all_actions(self, user_id):
        try:
            conn = get_conn()
            rows = conn.execute(
                "SELECT * FROM action_items WHERE user_id=? "
                "ORDER BY created_at DESC LIMIT 100",
                (user_id,),
            ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def mark_action_complete(self, user_id, action_id):
        try:
            conn = get_conn()
            conn.execute(
                "UPDATE action_items SET completed=1, completed_at=? "
                "WHERE id=? AND user_id=?",
                (datetime.now().isoformat(), action_id, user_id),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def delete_action(self, user_id, action_id):
        try:
            conn = get_conn()
            conn.execute(
                "DELETE FROM action_items WHERE id=? AND user_id=?",
                (action_id, user_id),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def add_medicine(self, user_id, name, dosage, frequency, time_of_day):
        try:
            conn = get_conn()
            mid = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO medicines
                   (id, user_id, name, dosage, frequency, time_of_day, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (mid, user_id, name, dosage, frequency, time_of_day,
                 datetime.now().isoformat()),
            )
            conn.commit()
            conn.close()
            return mid
        except Exception:
            return None

    def get_all_medicines(self, user_id):
        try:
            conn = get_conn()
            rows = conn.execute(
                "SELECT * FROM medicines WHERE user_id=? AND active=1 "
                "ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def get_todays_medicines(self, user_id):
        return self.get_all_medicines(user_id)

    def update_medicine_taken(self, user_id, med_id):
        try:
            conn = get_conn()
            conn.execute(
                "UPDATE medicines SET last_taken=? WHERE id=? AND user_id=?",
                (datetime.now().isoformat(), med_id, user_id),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def delete_medicine(self, user_id, med_id):
        try:
            conn = get_conn()
            conn.execute(
                "UPDATE medicines SET active=0 WHERE id=? AND user_id=?",
                (med_id, user_id),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def add_bill(self, user_id, name, amount, due_day, category):
        try:
            conn = get_conn()
            bid = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO bills
                   (id, user_id, name, amount, due_day, category, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (bid, user_id, name, amount, due_day, category,
                 datetime.now().isoformat()),
            )
            conn.commit()
            conn.close()
            return bid
        except Exception:
            return None

    def get_all_bills(self, user_id):
        try:
            conn = get_conn()
            rows = conn.execute(
                "SELECT * FROM bills WHERE user_id=? ORDER BY due_day ASC",
                (user_id,),
            ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def get_monthly_bills(self, user_id):
        return self.get_all_bills(user_id)

    def mark_bill_paid(self, user_id, bill_id):
        try:
            conn = get_conn()
            conn.execute(
                "UPDATE bills SET paid_this_month=1, last_paid=? "
                "WHERE id=? AND user_id=?",
                (datetime.now().isoformat(), bill_id, user_id),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def delete_bill(self, user_id, bill_id):
        try:
            conn = get_conn()
            conn.execute(
                "DELETE FROM bills WHERE id=? AND user_id=?", (bill_id, user_id)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def add_note(self, user_id, title, content, tags=""):
        try:
            conn = get_conn()
            nid = str(uuid.uuid4())
            now = datetime.now().isoformat()
            conn.execute(
                """INSERT INTO notes
                   (id, user_id, title, content, tags, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (nid, user_id, title, content, tags, now, now),
            )
            conn.commit()
            conn.close()
            return nid
        except Exception:
            return None

    def get_notes(self, user_id):
        try:
            conn = get_conn()
            rows = conn.execute(
                "SELECT * FROM notes WHERE user_id=? "
                "ORDER BY pinned DESC, updated_at DESC",
                (user_id,),
            ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def delete_note(self, user_id, note_id):
        try:
            conn = get_conn()
            conn.execute(
                "DELETE FROM notes WHERE id=? AND user_id=?", (note_id, user_id)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def toggle_pin_note(self, user_id, note_id):
        try:
            conn = get_conn()
            conn.execute(
                "UPDATE notes SET pinned = 1 - pinned WHERE id=? AND user_id=?",
                (note_id, user_id),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def add_study_session(self, user_id, duration_minutes, subject,
                          productivity_score, notes=""):
        try:
            conn = get_conn()
            sid = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO study_sessions
                   (id, user_id, subject, duration_minutes,
                    productivity_score, date, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (sid, user_id, subject, duration_minutes, productivity_score,
                 datetime.now().strftime("%Y-%m-%d"), notes),
            )
            conn.commit()
            conn.close()
            self._record_checkin(user_id)
            return sid
        except Exception:
            return None

    def get_study_sessions(self, user_id, limit=20):
        try:
            conn = get_conn()
            rows = conn.execute(
                "SELECT * FROM study_sessions WHERE user_id=? "
                "ORDER BY date DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def get_weekly_study_summary(self, user_id):
        try:
            conn = get_conn()
            week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            rows = conn.execute(
                "SELECT * FROM study_sessions WHERE user_id=? AND date >= ?",
                (user_id, week_ago),
            ).fetchall()
            conn.close()
            sessions = [dict(r) for r in rows]
            total_min = sum(s["duration_minutes"] for s in sessions)
            avg_score = (
                sum(s["productivity_score"] for s in sessions) / len(sessions)
                if sessions else 0
            )
            return {
                "total_minutes": total_min,
                "sessions": len(sessions),
                "avg_score": round(avg_score, 1),
                "sessions_data": sessions,
            }
        except Exception:
            return {"total_minutes": 0, "sessions": 0,
                    "avg_score": 0.0, "sessions_data": []}

    def add_health_log(self, user_id, date, symptoms, sleep_quality,
                       energy_level, water_intake, mood=5, weight=0):
        try:
            conn = get_conn()
            lid = str(uuid.uuid4())
            conn.execute(
                """INSERT OR REPLACE INTO health_logs
                   (id, user_id, date, symptoms, sleep_quality,
                    energy_level, water_intake, mood, weight)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (lid, user_id, date, symptoms, sleep_quality,
                 energy_level, water_intake, mood, weight),
            )
            conn.commit()
            conn.close()
            self._record_checkin(user_id)
            return lid
        except Exception:
            return None

    def get_health_logs(self, user_id, days=7):
        try:
            conn = get_conn()
            cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            rows = conn.execute(
                "SELECT * FROM health_logs WHERE user_id=? AND date >= ? "
                "ORDER BY date DESC",
                (user_id, cutoff),
            ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def save_ai_analysis(self, user_id, results):
        try:
            conn = get_conn()
            aid = str(uuid.uuid4())
            score = results.get("validation_report", {}).get("overall_score", 80)
            conn.execute(
                """INSERT INTO ai_analyses
                   (id, user_id, created_at, health_result, finance_result,
                    study_result, coordination_result, score)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (aid, user_id, datetime.now().isoformat(),
                 results.get("health", ""), results.get("finance", ""),
                 results.get("study", ""), results.get("coordination", ""), score),
            )
            conn.commit()
            conn.close()
            return aid
        except Exception:
            return None

    def get_recent_analyses(self, user_id, limit=5):
        try:
            conn = get_conn()
            rows = conn.execute(
                "SELECT id, created_at, score FROM ai_analyses WHERE user_id=? "
                "ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def _record_checkin(self, user_id):
        try:
            conn = get_conn()
            today = datetime.now().strftime("%Y-%m-%d")
            conn.execute(
                "INSERT OR IGNORE INTO daily_checkins (id, user_id, date) "
                "VALUES (?, ?, ?)",
                (str(uuid.uuid4()), user_id, today),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def get_consistency_streak(self, user_id):
        try:
            conn = get_conn()
            rows = conn.execute(
                "SELECT date FROM daily_checkins WHERE user_id=? "
                "ORDER BY date DESC LIMIT 90",
                (user_id,),
            ).fetchall()
            conn.close()
            dates = []
            for r in rows:
                try:
                    dates.append(r["date"])
                except (KeyError, IndexError):
                    dates.append(r[0])
            if not dates:
                return 0
            streak = 0
            check = datetime.now().date()
            for d in dates:
                try:
                    d_obj = datetime.strptime(d, "%Y-%m-%d").date()
                    if d_obj == check or d_obj == check - timedelta(days=1):
                        streak += 1
                        check = d_obj - timedelta(days=1)
                    else:
                        break
                except Exception:
                    break
            return streak
        except Exception:
            return 0

    def get_user_statistics(self, user_id):
        try:
            conn = get_conn()
            total     = _safe_count(conn,
                "SELECT COUNT(*) as c FROM action_items WHERE user_id=?",
                (user_id,))
            completed = _safe_count(conn,
                "SELECT COUNT(*) as c FROM action_items WHERE user_id=? AND completed=1",
                (user_id,))
            meds      = _safe_count(conn,
                "SELECT COUNT(*) as c FROM medicines WHERE user_id=? AND active=1",
                (user_id,))
            bills     = _safe_count(conn,
                "SELECT COUNT(*) as c FROM bills WHERE user_id=?",
                (user_id,))
            notes     = _safe_count(conn,
                "SELECT COUNT(*) as c FROM notes WHERE user_id=?",
                (user_id,))
            sessions  = _safe_count(conn,
                "SELECT COUNT(*) as c FROM study_sessions WHERE user_id=?",
                (user_id,))
            analyses  = _safe_count(conn,
                "SELECT COUNT(*) as c FROM ai_analyses WHERE user_id=?",
                (user_id,))
            conn.close()
            return {
                "total_actions":     total,
                "completed_actions": completed,
                "medicines_count":   meds,
                "bills_count":       bills,
                "notes_count":       notes,
                "study_sessions":    sessions,
                "ai_analyses":       analyses,
                "completion_rate":   round(
                    (completed / total * 100) if total > 0 else 0, 1
                ),
            }
        except Exception:
            return {
                "total_actions": 0, "completed_actions": 0,
                "medicines_count": 0, "bills_count": 0, "notes_count": 0,
                "study_sessions": 0, "ai_analyses": 0, "completion_rate": 0.0,
            }
