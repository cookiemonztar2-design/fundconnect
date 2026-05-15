import sqlite3
import hashlib 
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "fundconnect.db")

def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    return conn

def _hash_pw(password:str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Creates all tables if they don't exist yet."""
    with _get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS user_account (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role          TEXT NOT NULL,
                status        TEXT NOT NULL DEFAULT 'Active',
                created_at    TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS user_profile (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                role       TEXT NOT NULL,
                email      TEXT NOT NULL UNIQUE,
                contact    TEXT,
                status     TEXT NOT NULL DEFAULT 'Active',
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS fra_category (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS fundraising_activity (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                title           TEXT NOT NULL,
                description     TEXT,
                target_amount   REAL NOT NULL,
                amount_raised   REAL DEFAULT 0,
                category_id     INTEGER REFERENCES fra_category(id),
                deadline        TEXT NOT NULL,
                status          TEXT NOT NULL DEFAULT 'Active',
                fundraiser_id   INTEGER REFERENCES user_account(id),
                view_count      INTEGER DEFAULT 0,
                shortlist_count INTEGER DEFAULT 0,
                created_at      TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS favourite (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                donee_id    INTEGER REFERENCES user_account(id),
                activity_id INTEGER REFERENCES fundraising_activity(id),
                created_at  TEXT DEFAULT (datetime('now')),
                UNIQUE(donee_id, activity_id)
            );

            CREATE TABLE IF NOT EXISTS system_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type  TEXT NOT NULL,
                description TEXT,
                user_id     INTEGER,
                created_at  TEXT DEFAULT (datetime('now'))
            );
        """)
        db.commit()

        if not db.execute("SELECT 1 FROM user_account LIMIT 1").fetchone():
            _seed(db)
            db.commit()


def _seed(db):
    """Insert demo accounts."""
    accounts = [
        ("admin",      "password", "User Admin"),
        ("fundraiser", "password", "Fund Raiser"),
        ("donee",      "password", "Donee"),
        ("manager",    "password", "Platform Manager"),
    ]
    for username, password, role in accounts:
        db.execute(
            "INSERT INTO user_account (username, password_hash, role) VALUES (?, ?, ?)",
            (username, _hash_pw(password), role)
        )

    cats = [
    ("Environment",     "Nature and ecological causes"),
    ("Education",       "Learning and scholarship campaigns"),
    ("Medical",         "Health and medical support"),
    ("Disaster Relief", "Emergency aid and recovery"),
    ]
    for name, desc in cats:
        db.execute(
            "INSERT INTO fra_category (name, description) VALUES (?, ?)",
            (name, desc)
        )
    
    

class UserAccountEntity:

    @staticmethod
    def create(username, password, role):
        with _get_db() as db:
            db.execute(
                "INSERT INTO user_account (username, password_hash, role) VALUES (?,?,?)",
                (username, _hash_pw(password), role)
            )
            db.commit()

    @staticmethod
    def get_by_id(account_id):
        with _get_db() as db:
            return db.execute(
                "SELECT * FROM user_account where id=?",
                (account_id,)
            ).fetchone()

    
    @staticmethod
    def verify_password(username, password):
        with _get_db() as db:
            return db.execute(
                "SELECT * FROM user_account WHERE username=? and password_hash=?",
                (username, _hash_pw(password))
            ).fetchone()

    @staticmethod
    def username_exists(username, exclude_id=None):
        with _get_db() as db:
            if exclude_id:
                return db.execute(
                    "SELECT id FROM user_account WHERE username=? and id!=?",
                    (username, exclude_id)
                ).fetchone() is not None
            return db.execute(
                "SELECT id FROM user_account WHERE username=?",
                (username,)
            ).fetchone() is not None

    @staticmethod
    def get_all(exclude_admin=True):
        with _get_db() as db:
            if exclude_admin:
                return db.execute(
                    "SELECT * FROM  user_account WHERE role != 'User Admin' ORDER BY username"
                ).fetchall()

    @staticmethod
    def search(query):
        like = f"%{query}%"
        with _get_db() as db:
            return db.execute(
                """SELECT * FROM user_account
                   WHERE role != 'User Admin'
                   AND (username LIKE ? OR role LIKE ? OR status LIKE ?)
                   ORDER BY username""",
                (like, like, like)
            ).fetchall()
            
    @staticmethod
    def set_status(account_id, status):
        with _get_db() as db:
            db.execute(
                "UPDATE user_account SET status=? WHERE id=?",
                (status, account_id)
            )
            db.commit()
    
    @staticmethod
    def update(account_id, username, role, new_password=None):
        with _get_db() as db:
            if new_password:
                db.execute(
                    "UPDATE user_account SET username=?, role=?, password_hash=? WHERE id=?",
                    (username, role, _hash_pw(new_password), account_id)
                )
            else:
                db.execute(
                    "UPDATE user_account SET username=?, role=? WHERE id=?",
                    (username, role, account_id)
                )
            db.commit()

class UserProfileEntity:

    @staticmethod
    def create(name, role, email, contact):
        with _get_db() as db:
            db.execute(
                "INSERT INTO user_profile (name, role, email, contact) VALUES (?, ?, ?, ?)",
                (name, role, email, contact)
            )
            db.commit()

    @staticmethod
    def get_by_id(profile_id):
        with _get_db() as db:
            return db.execute(
                "SELECT * FROM user_profile WHERE id=?",
                (profile_id,)
            ).fetchone()

    @staticmethod
    def get_all():
        with _get_db() as db:
            return db.execute(
                "SELECT * FROM user_profile WHERE role != 'User Admin' ORDER BY name"
            ).fetchall()

    @staticmethod
    def search(query):
        like = f"%{query}%"
        with _get_db() as db:
            return db.execute(
                """SELECT * FROM user_profile
                   WHERE role != 'User Admin'
                   AND (name LIKE ? OR role LIKE ? OR email LIKE ?)
                   ORDER BY name""",
                (like, like, like)
            ).fetchall()

    @staticmethod
    def email_exists(email, exclude_id=None):
        with _get_db() as db:
            if exclude_id:
                return db.execute(
                    "SELECT id FROM user_profile WHERE email=? AND id!=?",
                    (email, exclude_id)
                ).fetchone() is not None
            return db.execute(
                "SELECT id FROM user_profile WHERE email=?",
                (email,)
            ).fetchone() is not None

    @staticmethod
    def update(profile_id, name, role, email, contact):
        with _get_db() as db:
            db.execute(
                "UPDATE user_profile SET name=?, role=?, email=?, contact=? WHERE id=?",
                (name, role, email, contact, profile_id)
            )
            db.commit()

    @staticmethod
    def set_status(profile_id, status):
        with _get_db() as db:
            db.execute(
                "UPDATE user_profile SET status=? WHERE id=?",
                (status, profile_id)
            )
            db.commit()


class FRACategoryEntity:

    @staticmethod
    def get_all():
        with _get_db() as db:
            return db.execute(
                "SELECT * FROM fra_category ORDER BY name"
            ).fetchall()

    @staticmethod
    def get_by_id(category_id):
        with _get_db() as db:
            return db.execute(
                "SELECT * FROM fra_category WHERE id=?",
                (category_id,)
            ).fetchone()


class FRACategoryEntity:

    @staticmethod
    def get_all():
        with _get_db() as db:
            return db.execute(
                "SELECT * FROM fra_category ORDER BY name"
            ).fetchall()

    @staticmethod
    def get_by_id(category_id):
        with _get_db() as db:
            return db.execute(
                "SELECT * FROM fra_category WHERE id=?",
                (category_id,)
            ).fetchone()

    @staticmethod
    def search(query):
        like = f"%{query}%"
        with _get_db() as db:
            return db.execute(
                """SELECT * FROM fra_category
                   WHERE name LIKE ? OR description LIKE ?
                   ORDER BY name""",
                (like, like)
            ).fetchall()

    @staticmethod
    def name_exists(name, exclude_id=None):
        with _get_db() as db:
            if exclude_id:
                return db.execute(
                    "SELECT id FROM fra_category WHERE name=? AND id!=?",
                    (name, exclude_id)
                ).fetchone() is not None
            return db.execute(
                "SELECT id FROM fra_category WHERE name=?",
                (name,)
            ).fetchone() is not None

    @staticmethod
    def create(name, description):
        with _get_db() as db:
            db.execute(
                "INSERT INTO fra_category (name, description) VALUES (?, ?)",
                (name, description)
            )
            db.commit()

    @staticmethod
    def update(category_id, name, description):
        with _get_db() as db:
            db.execute(
                "UPDATE fra_category SET name=?, description=? WHERE id=?",
                (name, description, category_id)
            )
            db.commit()

    @staticmethod
    def delete(category_id):
        with _get_db() as db:
            db.execute(
                "DELETE FROM fra_category WHERE id=?",
                (category_id,)
            )
            db.commit()


class FundraisingActivityEntity:

    @staticmethod
    def get_by_id(activity_id):
        with _get_db() as db:
            return db.execute(
                """SELECT fa.*, fc.name AS category_name
                   FROM fundraising_activity fa
                   LEFT JOIN fra_category fc ON fa.category_id = fc.id
                   WHERE fa.id=?""",
                (activity_id,)
            ).fetchone()

    @staticmethod
    def get_active_by_fundraiser(fundraiser_id):
        with _get_db() as db:
            return db.execute(
                """SELECT fa.*, fc.name AS category_name
                   FROM fundraising_activity fa
                   LEFT JOIN fra_category fc ON fa.category_id = fc.id
                   WHERE fa.fundraiser_id=? AND fa.status='Active'
                   ORDER BY fa.created_at DESC""",
                (fundraiser_id,)
            ).fetchall()

    @staticmethod
    def search_active_by_fundraiser(fundraiser_id, query):
        like = f"%{query}%"
        with _get_db() as db:
            return db.execute(
                """SELECT fa.*, fc.name AS category_name
                   FROM fundraising_activity fa
                   LEFT JOIN fra_category fc ON fa.category_id = fc.id
                   WHERE fa.fundraiser_id=? AND fa.status='Active'
                   AND (fa.title LIKE ? OR fc.name LIKE ?)
                   ORDER BY fa.created_at DESC""",
                (fundraiser_id, like, like)
            ).fetchall()

    @staticmethod
    def create(title, description, target_amount, category_id, deadline, fundraiser_id):
        with _get_db() as db:
            db.execute(
                """INSERT INTO fundraising_activity
                   (title, description, target_amount, category_id, deadline, fundraiser_id)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (title, description, target_amount, category_id, deadline, fundraiser_id)
            )
            db.commit()

    @staticmethod
    def update(activity_id, title, description, target_amount, category_id, deadline):
        with _get_db() as db:
            db.execute(
                """UPDATE fundraising_activity
                   SET title=?, description=?, target_amount=?, category_id=?, deadline=?
                   WHERE id=?""",
                (title, description, target_amount, category_id, deadline, activity_id)
            )
            db.commit()

    @staticmethod
    def delete(activity_id):
        with _get_db() as db:
            db.execute(
                "DELETE FROM fundraising_activity WHERE id=?",
                (activity_id,)
            )
            db.commit()

    @staticmethod
    def increment_view_count(activity_id):
        with _get_db() as db:
            db.execute(
                "UPDATE fundraising_activity SET view_count=view_count+1 WHERE id=?",
                (activity_id,)
            )
            db.commit()
    
    @staticmethod
    def get_all_active():
        with _get_db() as db:
            return db.execute(
                """SELECT fa.*, fc.name AS category_name
                   FROM fundraising_activity fa
                   LEFT JOIN fra_category fc ON fa.category_id = fc.id
                   WHERE fa.status='Active'
                   ORDER BY fa.created_at DESC"""
            ).fetchall()

    @staticmethod
    def search_all_active(query):
        like = f"%{query}%"
        with _get_db() as db:
            return db.execute(
                """SELECT fa.*, fc.name AS category_name
                   FROM fundraising_activity fa
                   LEFT JOIN fra_category fc ON fa.category_id = fc.id
                   WHERE fa.status='Active'
                   AND (fa.title LIKE ? OR fc.name LIKE ?)
                   ORDER BY fa.created_at DESC""",
                (like, like)
            ).fetchall()

    @staticmethod
    def get_all_completed():
        with _get_db() as db:
            return db.execute(
                """SELECT fa.*, fc.name AS category_name
                   FROM fundraising_activity fa
                   LEFT JOIN fra_category fc ON fa.category_id = fc.id
                   WHERE fa.status='Completed'
                   ORDER BY fa.deadline DESC"""
            ).fetchall()

    @staticmethod
    def search_all_completed(query):
        like = f"%{query}%"
        with _get_db() as db:
            return db.execute(
                """SELECT fa.*, fc.name AS category_name
                   FROM fundraising_activity fa
                   LEFT JOIN fra_category fc ON fa.category_id = fc.id
                   WHERE fa.status='Completed'
                   AND (fa.title LIKE ? OR fc.name LIKE ?)
                   ORDER BY fa.deadline DESC""",
                (like, like)
            ).fetchall()

    @staticmethod
    def increment_shortlist_count(activity_id):
        with _get_db() as db:
            db.execute(
                "UPDATE fundraising_activity SET shortlist_count=shortlist_count+1 WHERE id=?",
                (activity_id,)
            )
            db.commit()

    @staticmethod
    def decrement_shortlist_count(activity_id):
        with _get_db() as db:
            db.execute(
                "UPDATE fundraising_activity SET shortlist_count=MAX(0, shortlist_count-1) WHERE id=?",
                (activity_id,)
            )
            db.commit()

    @staticmethod
    def get_completed_by_fundraiser(fundraiser_id):
        with _get_db() as db:
            return db.execute(
                """SELECT fa.*, fc.name AS category_name
                   FROM fundraising_activity fa
                   LEFT JOIN fra_category fc ON fa.category_id = fc.id
                   WHERE fa.fundraiser_id=? AND fa.status='Completed'
                   ORDER BY fa.deadline DESC""",
                (fundraiser_id,)
            ).fetchall()

    @staticmethod
    def search_completed_by_fundraiser(fundraiser_id, query):
        like = f"%{query}%"
        with _get_db() as db:
            return db.execute(
                """SELECT fa.*, fc.name AS category_name
                   FROM fundraising_activity fa
                   LEFT JOIN fra_category fc ON fa.category_id = fc.id
                   WHERE fa.fundraiser_id=? AND fa.status='Completed'
                   AND (fa.title LIKE ? OR fc.name LIKE ?)
                   ORDER BY fa.deadline DESC""",
                (fundraiser_id, like, like)
            ).fetchall()

    @staticmethod
    def set_status(activity_id, status):
        with _get_db() as db:
            db.execute(
                "UPDATE fundraising_activity SET status=? WHERE id=?",
                (status, activity_id)
            )
            db.commit()


class FavouriteEntity:

    @staticmethod
    def get_by_donee(donee_id):
        with _get_db() as db:
            return db.execute(
                """SELECT fa.*, fc.name AS category_name
                   FROM favourite fv
                   JOIN fundraising_activity fa ON fv.activity_id = fa.id
                   LEFT JOIN fra_category fc ON fa.category_id = fc.id
                   WHERE fv.donee_id=?
                   ORDER BY fv.created_at DESC""",
                (donee_id,)
            ).fetchall()

    @staticmethod
    def search_by_donee(donee_id, query):
        like = f"%{query}%"
        with _get_db() as db:
            return db.execute(
                """SELECT fa.*, fc.name AS category_name
                   FROM favourite fv
                   JOIN fundraising_activity fa ON fv.activity_id = fa.id
                   LEFT JOIN fra_category fc ON fa.category_id = fc.id
                   WHERE fv.donee_id=?
                   AND (fa.title LIKE ? OR fc.name LIKE ?)
                   ORDER BY fv.created_at DESC""",
                (donee_id, like, like)
            ).fetchall()

    @staticmethod
    def get_ids_by_donee(donee_id):
        """Returns a set of activity_ids the donee has favourited."""
        with _get_db() as db:
            rows = db.execute(
                "SELECT activity_id FROM favourite WHERE donee_id=?",
                (donee_id,)
            ).fetchall()
        return {r["activity_id"] for r in rows}

    @staticmethod
    def exists(donee_id, activity_id):
        with _get_db() as db:
            return db.execute(
                "SELECT 1 FROM favourite WHERE donee_id=? AND activity_id=?",
                (donee_id, activity_id)
            ).fetchone() is not None

    @staticmethod
    def add(donee_id, activity_id):
        with _get_db() as db:
            db.execute(
                "INSERT INTO favourite (donee_id, activity_id) VALUES (?, ?)",
                (donee_id, activity_id)
            )
            db.commit()

    @staticmethod
    def remove(donee_id, activity_id):
        with _get_db() as db:
            db.execute(
                "DELETE FROM favourite WHERE donee_id=? AND activity_id=?",
                (donee_id, activity_id)
            )
            db.commit()


class SystemLogEntity:

    @staticmethod
    def add(event_type, description, user_id=None):
        with _get_db() as db:
            db.execute(
                "INSERT INTO system_log (event_type, description, user_id) VALUES (?, ?, ?)",
                (event_type, description, user_id)
            )
            db.commit()

    @staticmethod
    def get_recent(days, limit=20):
        with _get_db() as db:
            return db.execute(
                f"""SELECT * FROM system_log
                    WHERE created_at >= datetime('now', '-{int(days)} days')
                    ORDER BY created_at DESC LIMIT ?""",
                (limit,)
            ).fetchall()

    @staticmethod
    def count_event(event_type, days):
        with _get_db() as db:
            return db.execute(
                f"""SELECT COUNT(*) FROM system_log
                    WHERE event_type=?
                    AND created_at >= datetime('now', '-{int(days)} days')""",
                (event_type,)
            ).fetchone()[0]

    @staticmethod
    def count_new_rows(table, days):
        with _get_db() as db:
            return db.execute(
                f"""SELECT COUNT(*) FROM {table}
                    WHERE created_at >= datetime('now', '-{int(days)} days')"""
            ).fetchone()[0]

    @staticmethod
    def total_raised():
        with _get_db() as db:
            return db.execute(
                "SELECT COALESCE(SUM(amount_raised), 0) FROM fundraising_activity"
            ).fetchone()[0]

    @staticmethod
    def count_active_fras():
        with _get_db() as db:
            return db.execute(
                "SELECT COUNT(*) FROM fundraising_activity WHERE status='Active'"
            ).fetchone()[0]