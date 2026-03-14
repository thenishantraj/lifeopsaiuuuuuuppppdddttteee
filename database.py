import sqlite3
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import os

DB_PATH = os.environ.get("DATABASE_PATH", "lifeops_v2.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

class LifeOpsDatabase:
    def __init__(self):
        self._init_db()

    def _init_db(self):
        conn = get_conn()
        c = conn.cursor()

        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            joined_at TEXT NOT NULL,
            last_login TEXT,
            theme TEXT DEFAULT 'light',
            notifications_email INTEGER DEFAULT 1,
            notifications_push INTEGER DEFAULT 1,
            notifications_weekly INTEGER DEFAULT 1,
            font_size TEXT DEFAULT 'Medium'
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS action_items (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            task TEXT NOT NULL,
            category TEXT NOT NULL,
            source TEXT DEFAULT 'User',
            priority TEXT DEFAULT 'medium',
            completed INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            dosage TEXT,
            frequency TEXT,
            time_of_day TEXT,
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            last_taken TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            due_day INTEGER NOT NULL,
            category TEXT DEFAULT 'Other',
            paid_this_month INTEGER DEFAULT 0,
            auto_pay INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            last_paid TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT,
            pinned INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS study_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            productivity_score INTEGER DEFAULT 5,
            date TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS health_logs (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            date TEXT NOT NULL,
            symptoms TEXT,
            sleep_quality INTEGER,
            energy_level INTEGER,
            water_intake INTEGER,
            mood INTEGER,
            weight REAL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS daily_checkins (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            date TEXT NOT NULL,
            completed INTEGER DEFAULT 1,
            UNIQUE(user_id, date),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS ai_analyses (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            health_result TEXT,
            finance_result TEXT,
            study_result TEXT,
            coordination_result TEXT,
            score INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")

        conn.commit()
        conn.close()

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, email: str, password: str, name: str) -> bool:
        try:
            conn = get_conn()
            user_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO users (id, email, password_hash, name, joined_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, email.lower().strip(), self._hash_password(password), name, datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False

    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        conn = get_conn()
        row = conn.execute(
            "SELECT * FROM users WHERE email=? AND password_hash=?",
            (email.lower().strip(), self._hash_password(password))
        ).fetchone()
        if row:
            conn.execute("UPDATE users SET last_login=? WHERE id=?", (datetime.now().isoformat(), row["id"]))
            conn.commit()
            result = dict(row)
            conn.close()
            return result
        conn.close()
        return None

    def get_user(self, user_id: str) -> Optional[Dict]:
        conn = get_conn()
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def update_user_settings(self, user_id: str, settings: Dict) -> bool:
        try:
            conn = get_conn()
            fields = []
            values = []
            allowed = ['name', 'theme', 'notifications_email', 'notifications_push', 'notifications_weekly', 'font_size']
            for k, v in settings.items():
                if k in allowed:
                    fields.append(f"{k}=?")
                    values.append(v)
            if not fields:
                return False
            values.append(user_id)
            conn.execute(f"UPDATE users SET {', '.join(fields)} WHERE id=?", values)
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        conn = get_conn()
        row = conn.execute("SELECT password_hash FROM users WHERE id=?", (user_id,)).fetchone()
        if row and row["password_hash"] == self._hash_password(old_password):
            conn.execute("UPDATE users SET password_hash=? WHERE id=?", (self._hash_password(new_password), user_id))
            conn.commit()
            conn.close()
            return True
        conn.close()
        return False

    def add_action_item(self, user_id: str, task: str, category: str, source: str = "User", priority: str = "medium") -> str:
        conn = get_conn()
        item_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO action_items (id, user_id, task, category, source, priority, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (item_id, user_id, task, category, source, priority, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        self._record_checkin(user_id)
        return item_id

    def get_pending_actions(self, user_id: str) -> List[Dict]:
        conn = get_conn()
        rows = conn.execute(
            "SELECT * FROM action_items WHERE user_id=? AND completed=0 ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_all_actions(self, user_id: str) -> List[Dict]:
        conn = get_conn()
        rows = conn.execute(
            "SELECT * FROM action_items WHERE user_id=? ORDER BY created_at DESC LIMIT 100",
            (user_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def mark_action_complete(self, user_id: str, action_id: str):
        conn = get_conn()
        conn.execute(
            "UPDATE action_items SET completed=1, completed_at=? WHERE id=? AND user_id=?",
            (datetime.now().isoformat(), action_id, user_id)
        )
        conn.commit()
        conn.close()

    def delete_action(self, user_id: str, action_id: str):
        conn = get_conn()
        conn.execute("DELETE FROM action_items WHERE id=? AND user_id=?", (action_id, user_id))
        conn.commit()
        conn.close()

    def add_medicine(self, user_id: str, name: str, dosage: str, frequency: str, time_of_day: str) -> str:
        conn = get_conn()
        med_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO medicines (id, user_id, name, dosage, frequency, time_of_day, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (med_id, user_id, name, dosage, frequency, time_of_day, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        return med_id

    def get_all_medicines(self, user_id: str) -> List[Dict]:
        conn = get_conn()
        rows = conn.execute(
            "SELECT * FROM medicines WHERE user_id=? AND active=1 ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_todays_medicines(self, user_id: str) -> List[Dict]:
        return self.get_all_medicines(user_id)

    def update_medicine_taken(self, user_id: str, med_id: str):
        conn = get_conn()
        conn.execute(
            "UPDATE medicines SET last_taken=? WHERE id=? AND user_id=?",
            (datetime.now().isoformat(), med_id, user_id)
        )
        conn.commit()
        conn.close()

    def delete_medicine(self, user_id: str, med_id: str):
        conn = get_conn()
        conn.execute("UPDATE medicines SET active=0 WHERE id=? AND user_id=?", (med_id, user_id))
        conn.commit()
        conn.close()

    def add_bill(self, user_id: str, name: str, amount: float, due_day: int, category: str) -> str:
        conn = get_conn()
        bill_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO bills (id, user_id, name, amount, due_day, category, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (bill_id, user_id, name, amount, due_day, category, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        return bill_id

    def get_all_bills(self, user_id: str) -> List[Dict]:
        conn = get_conn()
        rows = conn.execute(
            "SELECT * FROM bills WHERE user_id=? ORDER BY due_day ASC",
            (user_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_monthly_bills(self, user_id: str) -> List[Dict]:
        return self.get_all_bills(user_id)

    def mark_bill_paid(self, user_id: str, bill_id: str):
        conn = get_conn()
        conn.execute(
            "UPDATE bills SET paid_this_month=1, last_paid=? WHERE id=? AND user_id=?",
            (datetime.now().isoformat(), bill_id, user_id)
        )
        conn.commit()
        conn.close()

    def delete_bill(self, user_id: str, bill_id: str):
        conn = get_conn()
        conn.execute("DELETE FROM bills WHERE id=? AND user_id=?", (bill_id, user_id))
        conn.commit()
        conn.close()

    def add_note(self, user_id: str, title: str, content: str, tags: str = "") -> str:
        conn = get_conn()
        note_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        conn.execute(
            "INSERT INTO notes (id, user_id, title, content, tags, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (note_id, user_id, title, content, tags, now, now)
        )
        conn.commit()
        conn.close()
        return note_id

    def get_notes(self, user_id: str) -> List[Dict]:
        conn = get_conn()
        rows = conn.execute(
            "SELECT * FROM notes WHERE user_id=? ORDER BY pinned DESC, updated_at DESC",
            (user_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_note(self, user_id: str, note_id: str):
        conn = get_conn()
        conn.execute("DELETE FROM notes WHERE id=? AND user_id=?", (note_id, user_id))
        conn.commit()
        conn.close()

    def toggle_pin_note(self, user_id: str, note_id: str):
        conn = get_conn()
        conn.execute(
            "UPDATE notes SET pinned = 1 - pinned WHERE id=? AND user_id=?",
            (note_id, user_id)
        )
        conn.commit()
        conn.close()

    def add_study_session(self, user_id: str, duration_minutes: int, subject: str, productivity_score: int, notes: str = "") -> str:
        conn = get_conn()
        session_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO study_sessions (id, user_id, subject, duration_minutes, productivity_score, date, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_id, user_id, subject, duration_minutes, productivity_score, datetime.now().strftime("%Y-%m-%d"), notes)
        )
        conn.commit()
        conn.close()
        self._record_checkin(user_id)
        return session_id

    def get_study_sessions(self, user_id: str, limit: int = 20) -> List[Dict]:
        conn = get_conn()
        rows = conn.execute(
            "SELECT * FROM study_sessions WHERE user_id=? ORDER BY date DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_weekly_study_summary(self, user_id: str) -> Dict:
        conn = get_conn()
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        rows = conn.execute(
            "SELECT * FROM study_sessions WHERE user_id=? AND date >= ?",
            (user_id, week_ago)
        ).fetchall()
        conn.close()
        sessions = [dict(r) for r in rows]
        total_min = sum(s['duration_minutes'] for s in sessions)
        avg_score = sum(s['productivity_score'] for s in sessions) / len(sessions) if sessions else 0
        return {
            "total_minutes": total_min,
            "sessions": len(sessions),
            "avg_score": round(avg_score, 1),
            "sessions_data": sessions
        }

    def add_health_log(self, user_id: str, date: str, symptoms: str, sleep_quality: int, energy_level: int, water_intake: int, mood: int = 5, weight: float = 0) -> str:
        conn = get_conn()
        log_id = str(uuid.uuid4())
        conn.execute(
            "INSERT OR REPLACE INTO health_logs (id, user_id, date, symptoms, sleep_quality, energy_level, water_intake, mood, weight) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (log_id, user_id, date, symptoms, sleep_quality, energy_level, water_intake, mood, weight)
        )
        conn.commit()
        conn.close()
        self._record_checkin(user_id)
        return log_id

    def get_health_logs(self, user_id: str, days: int = 7) -> List[Dict]:
        conn = get_conn()
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        rows = conn.execute(
            "SELECT * FROM health_logs WHERE user_id=? AND date >= ? ORDER BY date DESC",
            (user_id, cutoff)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def save_ai_analysis(self, user_id: str, results: Dict) -> str:
        conn = get_conn()
        analysis_id = str(uuid.uuid4())
        score = results.get("validation_report", {}).get("overall_score", 80)
        conn.execute(
            "INSERT INTO ai_analyses (id, user_id, created_at, health_result, finance_result, study_result, coordination_result, score) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (analysis_id, user_id, datetime.now().isoformat(),
             results.get("health", ""), results.get("finance", ""),
             results.get("study", ""), results.get("coordination", ""), score)
        )
        conn.commit()
        conn.close()
        return analysis_id

    def get_recent_analyses(self, user_id: str, limit: int = 5) -> List[Dict]:
        conn = get_conn()
        rows = conn.execute(
            "SELECT id, created_at, score FROM ai_analyses WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def _record_checkin(self, user_id: str):
        try:
            conn = get_conn()
            today = datetime.now().strftime("%Y-%m-%d")
            conn.execute(
                "INSERT OR IGNORE INTO daily_checkins (id, user_id, date) VALUES (?, ?, ?)",
                (str(uuid.uuid4()), user_id, today)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def get_consistency_streak(self, user_id: str) -> int:
        conn = get_conn()
        rows = conn.execute(
            "SELECT date FROM daily_checkins WHERE user_id=? ORDER BY date DESC LIMIT 90",
            (user_id,)
        ).fetchall()
        conn.close()
        dates = [r["date"] for r in rows]
        if not dates:
            return 0
        streak = 0
        check_date = datetime.now().date()
        for d in dates:
            try:
                d_obj = datetime.strptime(d, "%Y-%m-%d").date()
                if d_obj == check_date or d_obj == check_date - timedelta(days=1):
                    streak += 1
                    check_date = d_obj - timedelta(days=1)
                else:
                    break
            except Exception:
                break
        return streak

    def get_user_statistics(self, user_id: str) -> Dict:
        conn = get_conn()
        total = conn.execute("SELECT COUNT(*) as c FROM action_items WHERE user_id=?", (user_id,)).fetchone()["c"]
        completed = conn.execute("SELECT COUNT(*) as c FROM action_items WHERE user_id=? AND completed=1", (user_id,)).fetchone()["c"]
        meds = conn.execute("SELECT COUNT(*) as c FROM medicines WHERE user_id=? AND active=1", (user_id,)).fetchone()["c"]
        bills = conn.execute("SELECT COUNT(*) as c FROM bills WHERE user_id=?", (user_id,)).fetchone()["c"]
        notes = conn.execute("SELECT COUNT(*) as c FROM notes WHERE user_id=?", (user_id,)).fetchone()["c"]
        sessions = conn.execute("SELECT COUNT(*) as c FROM study_sessions WHERE user_id=?", (user_id,)).fetchone()["c"]
        analyses = conn.execute("SELECT COUNT(*) as c FROM ai_analyses WHERE user_id=?", (user_id,)).fetchone()["c"]
        conn.close()
        return {
            "total_actions": total,
            "completed_actions": completed,
            "medicines_count": meds,
            "bills_count": bills,
            "notes_count": notes,
            "study_sessions": sessions,
            "ai_analyses": analyses,
            "completion_rate": round((completed / total * 100) if total > 0 else 0, 1)
        }
