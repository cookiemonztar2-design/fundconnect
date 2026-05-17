import sys
import os
import random
from datetime import date, timedelta

sys.path.insert(0, ".")

from entity.entities import init_db, _get_db, _hash_pw

# ── Helpers ──────────────────────────────────────────────────────────────────

def random_date_future():
    """Random future date within the next 2 years."""
    days_ahead = random.randint(30, 730)
    return (date.today() + timedelta(days=days_ahead)).isoformat()

def random_date_past():
    """Random past date within the last 2 years."""
    days_ago = random.randint(30, 730)
    return (date.today() - timedelta(days=days_ago)).isoformat()

def random_amount(min_val, max_val):
    return round(random.uniform(min_val, max_val), 2)

# ── Data pools ────────────────────────────────────────────────────────────────

FIRST_NAMES = [
    "Alice", "Bob", "Carol", "David", "Emma", "Frank", "Grace", "Henry",
    "Iris", "James", "Karen", "Liam", "Mia", "Noah", "Olivia", "Peter",
    "Quinn", "Rachel", "Sam", "Tina", "Uma", "Victor", "Wendy", "Xavier",
    "Yara", "Zoe", "Aaron", "Bella", "Chris", "Diana"
]

LAST_NAMES = [
    "Tan", "Lim", "Lee", "Ng", "Chen", "Wong", "Goh", "Chua", "Ong", "Koh",
    "Teo", "Yeo", "Low", "Toh", "Sim", "Yap", "Lau", "Phua", "Ho", "Soh",
    "Boo", "Fong", "Heng", "Khoo", "Kwek", "Pang", "Seah", "Wee", "Yong", "Zhu"
]

ACTIVITY_TITLES = [
    "Save the Coral Reefs", "Clean Ocean Initiative", "Plant a Million Trees",
    "Solar Panels for Schools", "Clean Water for Villages", "Feed the Homeless",
    "Books for Every Child", "Medical Aid for Refugees", "Animal Shelter Support",
    "Community Garden Project", "Youth Sports Program", "Elderly Care Fund",
    "Disaster Relief Fund", "Women Empowerment Program", "Mental Health Awareness",
    "Wheelchair Access Project", "Food Bank Initiative", "Street Light for Villages",
    "Digital Literacy Program", "Music for Children", "Art Therapy Fund",
    "Ocean Cleanup Drive", "Recycling Awareness Campaign", "Urban Farming Project",
    "Stray Animal Rescue", "Education Scholarship Fund", "HIV Awareness Campaign",
    "Cancer Support Group", "Blind School Support", "Deaf Community Fund",
    "Rainforest Conservation", "Wildlife Protection", "Mangrove Restoration",
    "Beach Cleanup Drive", "River Pollution Control", "Air Quality Monitoring",
    "Renewable Energy Fund", "Bicycle Lane Project", "Green Roof Initiative",
    "Zero Waste Campaign", "Plastic Free Schools", "Composting for Communities",
    "Urban Tree Planting", "Sustainable Farming", "Organic Food Initiative",
    "Clean Cooking Fuel", "Biogas for Villages", "Wind Energy Project",
    "Tidal Energy Research", "Hydroponics for Schools"
]

DESCRIPTIONS = [
    "Help us make a difference in our community by supporting this important cause.",
    "Every dollar counts towards changing lives and building a better future.",
    "Join us in our mission to create lasting positive impact for those in need.",
    "Together we can achieve what none of us can do alone.",
    "Your support will directly benefit hundreds of families in our community.",
    "This initiative has already helped thousands and needs your continued support.",
    "Be part of the change you want to see in the world.",
    "A small contribution from you can make a huge difference to someone's life.",
    "We have been working tirelessly on this cause and need your help to continue.",
    "Help us reach our goal and transform lives for the better.",
]

def seed_test_data():
    init_db()

    with _get_db() as db:

        # ── Get existing data ─────────────────────────────────────────────────
        categories = db.execute("SELECT id FROM fra_category").fetchall()
        category_ids = [c["id"] for c in categories]

        fundraiser_accounts = db.execute(
            "SELECT id FROM user_account WHERE role='Fund Raiser'"
        ).fetchall()
        fundraiser_ids = [f["id"] for f in fundraiser_accounts]

        donee_accounts = db.execute(
            "SELECT id FROM user_account WHERE role='Donee'"
        ).fetchall()
        donee_ids = [d["id"] for d in donee_accounts]

        print(f"Found {len(category_ids)} categories")
        print(f"Found {len(fundraiser_ids)} fundraisers")
        print(f"Found {len(donee_ids)} donees")

        # ── 100 Fund Raiser accounts ──────────────────────────────────────────
        print("\nCreating 100 Fund Raiser accounts...")
        new_fundraiser_ids = []
        for i in range(1, 101):
            username = f"fundraiser_{i}"
            if not db.execute("SELECT 1 FROM user_account WHERE username=?", (username,)).fetchone():
                db.execute(
                    "INSERT INTO user_account (username, password_hash, role) VALUES (?, ?, ?)",
                    (username, _hash_pw("password"), "Fund Raiser")
                )
                new_fundraiser_ids.append(db.execute("SELECT last_insert_rowid()").fetchone()[0])
        db.commit()
        fundraiser_ids += new_fundraiser_ids
        print(f"  Done — total fundraisers: {len(fundraiser_ids)}")

        # ── 100 Donee accounts ────────────────────────────────────────────────
        print("Creating 100 Donee accounts...")
        new_donee_ids = []
        for i in range(1, 101):
            username = f"donee_{i}"
            if not db.execute("SELECT 1 FROM user_account WHERE username=?", (username,)).fetchone():
                db.execute(
                    "INSERT INTO user_account (username, password_hash, role) VALUES (?, ?, ?)",
                    (username, _hash_pw("password"), "Donee")
                )
                new_donee_ids.append(db.execute("SELECT last_insert_rowid()").fetchone()[0])
        db.commit()
        donee_ids += new_donee_ids
        print(f"  Done — total donees: {len(donee_ids)}")

        # ── 100 Active fundraising activities ─────────────────────────────────
        print("Creating 100 active fundraising activities...")
        activity_ids = []
        used_titles = set()
        for i in range(100):
            title = random.choice(ACTIVITY_TITLES)
            # Make title unique
            while title in used_titles:
                title = random.choice(ACTIVITY_TITLES) + f" {random.randint(1, 999)}"
            used_titles.add(title)

            target = random_amount(1000, 50000)
            raised = random_amount(0, target)
            db.execute(
                """INSERT INTO fundraising_activity
                   (title, description, target_amount, amount_raised, category_id,
                    deadline, status, fundraiser_id, view_count, shortlist_count)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    title,
                    random.choice(DESCRIPTIONS),
                    target,
                    raised,
                    random.choice(category_ids),
                    random_date_future(),
                    "Active",
                    random.choice(fundraiser_ids),
                    random.randint(0, 500),
                    random.randint(0, 100),
                )
            )
            activity_ids.append(db.execute("SELECT last_insert_rowid()").fetchone()[0])
        db.commit()
        print(f"  Done — {len(activity_ids)} active activities created")

        # ── 100 Completed fundraising activities ──────────────────────────────
        print("Creating 100 completed fundraising activities...")
        completed_ids = []
        for i in range(100):
            title = random.choice(ACTIVITY_TITLES)
            while title in used_titles:
                title = random.choice(ACTIVITY_TITLES) + f" {random.randint(1, 999)}"
            used_titles.add(title)

            target = random_amount(1000, 50000)
            raised = random_amount(target * 0.5, target)
            db.execute(
                """INSERT INTO fundraising_activity
                   (title, description, target_amount, amount_raised, category_id,
                    deadline, status, fundraiser_id, view_count, shortlist_count)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    title,
                    random.choice(DESCRIPTIONS),
                    target,
                    raised,
                    random.choice(category_ids),
                    random_date_past(),
                    "Completed",
                    random.choice(fundraiser_ids),
                    random.randint(50, 1000),
                    random.randint(10, 200),
                )
            )
            completed_ids.append(db.execute("SELECT last_insert_rowid()").fetchone()[0])
        db.commit()
        print(f"  Done — {len(completed_ids)} completed activities created")

        # ── 100 Favourites ────────────────────────────────────────────────────
        print("Creating 100 favourites...")
        all_activity_ids = activity_ids + completed_ids
        favs_created = 0
        attempts = 0
        while favs_created < 100 and attempts < 500:
            donee_id = random.choice(donee_ids)
            activity_id = random.choice(all_activity_ids)
            attempts += 1
            existing = db.execute(
                "SELECT 1 FROM favourite WHERE donee_id=? AND activity_id=?",
                (donee_id, activity_id)
            ).fetchone()
            if not existing:
                db.execute(
                    "INSERT INTO favourite (donee_id, activity_id) VALUES (?, ?)",
                    (donee_id, activity_id)
                )
                favs_created += 1
        db.commit()
        print(f"  Done — {favs_created} favourites created")

    print("\nAll test data created successfully!")
    print("All accounts use password: password")


if __name__ == "__main__":
    seed_test_data()