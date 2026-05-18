import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date
from entity.entities import UserAccountEntity, UserProfileEntity, FRACategoryEntity, FundraisingActivityEntity, FavouriteEntity, SystemLogEntity

def _ok(data=None, message=None):
    return {"success": True, "data": data, "message": message}

def _err(message):
    return {"success": False, "data": None, "message": message}

class AuthController:

    @staticmethod
    def login(username, password, selected_role):
        if not username or not password:
            return _err("Username and password are required.")

        account = UserAccountEntity.verify_password(username, password)

        if not account:
            return _err("Invalid username or password.")

        if account["status"] == "Suspended":
            return _err("Your account has been suspended.")

        if account["role"] != selected_role:
            return _err("The selected role does not match this account.")

        return _ok(
            data={
                "id":       account["id"],
                "username": account["username"],
                "role":     account["role"],
            },
            message="Login successful."
        )

        @staticmethod
        def logout():
            return _ok(message="Logged out successfully.")

class UserAccountController:

    @staticmethod
    def list_accounts(query=None):
        if query:
            rows = UserAccountEntity.search(query)
        else:
            rows = UserAccountEntity.get_all()
        return _ok(data=[dict(r) for r in rows])

    @staticmethod
    def view_account(account_id):
        account = UserAccountEntity.get_by_id(account_id)
        if not account:
            return _err("Account not found.")
        return _ok(data=dict(account))

    @staticmethod
    def create_account(username, password, role):
        if not username or not username.strip():
            return _err("Username is required.")
        if not password:
            return _err("Password is required.")
        if len(password) < 6:
            return _err("Password must be at least 6 characters.")
        if UserAccountEntity.username_exists(username.strip()):
            return _err("Username already exists.")

        UserAccountEntity.create(username.strip(), password, role)
        return _ok(message=f"Account '{username}' created successfully.")

    @staticmethod
    def update_account(account_id, username, role, new_password=None):
        if not UserAccountEntity.get_by_id(account_id):
            return _err("Account not found.")
        if not username or not username.strip():
            return _err("Username is required.")
        if UserAccountEntity.username_exists(username.strip(), exclude_id=account_id):
            return _err("Username already taken.")
        if new_password and len(new_password) < 6:
            return _err("Password must be at least 6 characters.")

        UserAccountEntity.update(account_id, username.strip(), role, new_password or None)
        return _ok(message="Account updated successfully.")

    @staticmethod
    def suspend_account(account_id):
        account = UserAccountEntity.get_by_id(account_id)
        if not account:
            return _err("Account not found.")
        new_status = "Active" if account["status"] == "Suspended" else "Suspended"
        UserAccountEntity.set_status(account_id, new_status)
        verb = "restored" if new_status == "Active" else "suspended"
        return _ok(message=f"Account {verb} successfully.")

    @staticmethod
    def delete_account(account_id, current_user_id):
        if account_id == current_user_id:
            return _err("You cannot delete your own account.")
        account = UserAccountEntity.get_by_id(account_id)
        if not account:
            return _err("Account not found.")
        if account["role"] == "User Admin":
            return _err("User Admin accounts cannot be deleted.")
        UserAccountEntity.delete(account_id)
        return _ok(message="Account deleted successfully.")

class UserProfileController:

    @staticmethod
    def list_profiles(query=None):
        if query:
            rows = UserProfileEntity.search(query)
        else:
            rows = UserProfileEntity.get_all()
        return _ok(data=[dict(r) for r in rows])

    @staticmethod
    def view_profile(profile_id):
        profile = UserProfileEntity.get_by_id(profile_id)
        if not profile:
            return _err("Profile not found.")
        return _ok(data=dict(profile))

    @staticmethod
    def create_profile(name, role, email, contact):
        if not name or not name.strip():
            return _err("Name is required.")
        if not email or not email.strip():
            return _err("Email is required.")
        if UserProfileEntity.email_exists(email.strip()):
            return _err("A profile with this email already exists.")

        UserProfileEntity.create(name.strip(), role, email.strip(), contact.strip() if contact else "")
        return _ok(message=f"Profile for {name} created successfully.")

    @staticmethod
    def update_profile(profile_id, name, role, email, contact):
        if not UserProfileEntity.get_by_id(profile_id):
            return _err("Profile not found.")
        if not name or not name.strip():
            return _err("Name is required.")
        if not email or not email.strip():
            return _err("Email is required.")
        if UserProfileEntity.email_exists(email.strip(), exclude_id=profile_id):
            return _err("Another profile with this email already exists.")

        UserProfileEntity.update(profile_id, name.strip(), role, email.strip(), contact.strip() if contact else "")
        return _ok(message="Profile updated successfully.")

    @staticmethod
    def suspend_profile(profile_id):
        profile = UserProfileEntity.get_by_id(profile_id)
        if not profile:
            return _err("Profile not found.")
        new_status = "Active" if profile["status"] == "Suspended" else "Suspended"
        UserProfileEntity.set_status(profile_id, new_status)
        verb = "restored" if new_status == "Active" else "suspended"
        return _ok(message=f"Profile {verb} successfully.")

    @staticmethod
    def delete_profile(profile_id):
        profile = UserProfileEntity.get_by_id(profile_id)
        if not profile:
            return _err("Profile not found.")
        if profile["role"] == "User Admin":
            return _err("User Admin profiles cannot be deleted.")
        UserProfileEntity.delete(profile_id)
        return _ok(message="Profile deleted successfully.")

class FundraisingActivityController:

    @staticmethod
    def get_categories():
        rows = FRACategoryEntity.get_all()
        return _ok(data=[dict(r) for r in rows])

    @staticmethod
    def list_activities(fundraiser_id, query=None):
        if query:
            rows = FundraisingActivityEntity.search_active_by_fundraiser(fundraiser_id, query)
        else:
            rows = FundraisingActivityEntity.get_active_by_fundraiser(fundraiser_id)
        return _ok(data=[dict(r) for r in rows])

    @staticmethod
    def view_activity(activity_id, fundraiser_id):
        activity = FundraisingActivityEntity.get_by_id(activity_id)
        if not activity:
            return _err("Activity not found.")
        if activity["fundraiser_id"] != fundraiser_id:
            return _err("You do not have permission to view this activity.")
        return _ok(data=dict(activity))

    @staticmethod
    def create_activity(fundraiser_id, title, description, target_amount_str, category_id, deadline):
        # Validate fields
        if not title or not title.strip():
            return _err("Title is required.")
        if not target_amount_str:
            return _err("Target amount is required.")
        try:
            target_amount = float(target_amount_str)
            if target_amount <= 0:
                return _err("Target amount must be a positive number.")
        except ValueError:
            return _err("Target amount must be a valid number.")
        if not deadline:
            return _err("Deadline is required.")
        if deadline <= str(date.today()):
            return _err("Deadline must be a future date.")

        FundraisingActivityEntity.create(
            title.strip(),
            description.strip() if description else "",
            target_amount,
            category_id,
            deadline,
            fundraiser_id
        )
        return _ok(message=f"Activity '{title}' created successfully.")

    @staticmethod
    def update_activity(activity_id, fundraiser_id, title, description, target_amount_str, category_id, deadline):
        activity = FundraisingActivityEntity.get_by_id(activity_id)
        if not activity or activity["fundraiser_id"] != fundraiser_id:
            return _err("Activity not found.")
        if not title or not title.strip():
            return _err("Title is required.")
        if not target_amount_str:
            return _err("Target amount is required.")
        try:
            target_amount = float(target_amount_str)
            if target_amount <= 0:
                return _err("Target amount must be a positive number.")
        except ValueError:
            return _err("Target amount must be a valid number.")
        if not deadline:
            return _err("Deadline is required.")
        if deadline <= str(date.today()):
            return _err("Deadline must be a future date.")

        FundraisingActivityEntity.update(
            activity_id,
            title.strip(),
            description.strip() if description else "",
            target_amount,
            category_id,
            deadline
        )
        return _ok(message="Activity updated successfully.")

    @staticmethod
    def delete_activity(activity_id, fundraiser_id):
        activity = FundraisingActivityEntity.get_by_id(activity_id)
        if not activity or activity["fundraiser_id"] != fundraiser_id:
            return _err("Activity not found.")
        FundraisingActivityEntity.delete(activity_id)
        return _ok(message="Activity deleted successfully.")

    @staticmethod
    def list_completed(fundraiser_id, category_id=None, date_from=None, date_to=None):
        # If any filter is provided, use the search method
        if category_id or date_from or date_to:
            rows = FundraisingActivityEntity.search_completed_by_fundraiser(
                fundraiser_id,
                category_id=category_id or None,
                date_from=date_from or None,
                date_to=date_to or None,
            )
        else:
            rows = FundraisingActivityEntity.get_completed_by_fundraiser(fundraiser_id)
        return _ok(data=[dict(r) for r in rows])

    @staticmethod
    def view_completed(activity_id, fundraiser_id):
        activity = FundraisingActivityEntity.get_by_id(activity_id)
        if not activity:
            return _err("Activity not found.")
        if activity["fundraiser_id"] != fundraiser_id:
            return _err("You do not have permission to view this activity.")
        if activity["status"] != "Completed":
            return _err("This activity is not completed.")
        return _ok(data=dict(activity))

    @staticmethod
    def mark_completed(activity_id, fundraiser_id):
        activity = FundraisingActivityEntity.get_by_id(activity_id)
        if not activity or activity["fundraiser_id"] != fundraiser_id:
            return _err("Activity not found.")
        if activity["status"] == "Completed":
            return _err("Activity is already completed.")
        FundraisingActivityEntity.set_status(activity_id, "Completed")
        return _ok(message="Activity marked as completed.")


class DoneeController:

    @staticmethod
    def browse_activities(query=None):
        if query:
            rows = FundraisingActivityEntity.search_all_active(query)
        else:
            rows = FundraisingActivityEntity.get_all_active()
        return _ok(data=[dict(r) for r in rows])

    @staticmethod
    def view_activity(activity_id, donee_id):
        activity = FundraisingActivityEntity.get_by_id(activity_id)
        if not activity or activity["status"] != "Active":
            return _err("Activity not found.")
        FundraisingActivityEntity.increment_view_count(activity_id)
        is_fav = FavouriteEntity.exists(donee_id, activity_id)
        return _ok(data={**dict(activity), "is_favourite": is_fav})

    @staticmethod
    def get_favourites(donee_id, query=None):
        if query:
            rows = FavouriteEntity.search_by_donee(donee_id, query)
        else:
            rows = FavouriteEntity.get_by_donee(donee_id)
        return _ok(data=[dict(r) for r in rows])

    @staticmethod
    def get_favourite_ids(donee_id):
        return FavouriteEntity.get_ids_by_donee(donee_id)

    @staticmethod
    def toggle_favourite(donee_id, activity_id):
        activity = FundraisingActivityEntity.get_by_id(activity_id)
        if not activity:
            return _err("Activity not found.")
        if FavouriteEntity.exists(donee_id, activity_id):
            FavouriteEntity.remove(donee_id, activity_id)
            FundraisingActivityEntity.decrement_shortlist_count(activity_id)
            return _ok(message="Removed from favourites.")
        else:
            FavouriteEntity.add(donee_id, activity_id)
            FundraisingActivityEntity.increment_shortlist_count(activity_id)
            return _ok(message="Saved to favourites!")

    @staticmethod
    def browse_history(query=None):
        if query:
            rows = FundraisingActivityEntity.search_all_completed(query)
        else:
            rows = FundraisingActivityEntity.get_all_completed()
        return _ok(data=[dict(r) for r in rows])

    @staticmethod
    def view_history(activity_id):
        activity = FundraisingActivityEntity.get_by_id(activity_id)
        if not activity or activity["status"] != "Completed":
            return _err("Completed activity not found.")
        return _ok(data=dict(activity))


class FRACategoryController:

    @staticmethod
    def list_categories(query=None):
        if query:
            rows = FRACategoryEntity.search(query)
        else:
            rows = FRACategoryEntity.get_all()
        return _ok(data=[dict(r) for r in rows])

    @staticmethod
    def view_category(category_id):
        cat = FRACategoryEntity.get_by_id(category_id)
        if not cat:
            return _err("Category not found.")
        return _ok(data=dict(cat))

    @staticmethod
    def create_category(name, description):
        if not name or not name.strip():
            return _err("Category name is required.")
        if FRACategoryEntity.name_exists(name.strip()):
            return _err("A category with this name already exists.")
        FRACategoryEntity.create(name.strip(), description.strip() if description else "")
        return _ok(message=f"Category '{name}' created successfully.")

    @staticmethod
    def update_category(category_id, name, description):
        if not FRACategoryEntity.get_by_id(category_id):
            return _err("Category not found.")
        if not name or not name.strip():
            return _err("Category name is required.")
        if FRACategoryEntity.name_exists(name.strip(), exclude_id=category_id):
            return _err("A category with this name already exists.")
        FRACategoryEntity.update(category_id, name.strip(), description.strip() if description else "")
        return _ok(message="Category updated successfully.")

    @staticmethod
    def delete_category(category_id):
        if not FRACategoryEntity.get_by_id(category_id):
            return _err("Category not found.")
        FRACategoryEntity.delete(category_id)
        return _ok(message="Category deleted successfully.")

class ReportController:

    PERIODS = {
        "daily":   (1,  "Daily Report"),
        "weekly":  (7,  "Weekly Report"),
        "monthly": (30, "Monthly Report"),
    }

    @staticmethod
    def generate(period):
        if period not in ReportController.PERIODS:
            return _err("Invalid report period.")

        days, label = ReportController.PERIODS[period]

        stats = {
            "Logins":           SystemLogEntity.count_event("login", days),
            "New Users":        SystemLogEntity.count_new_rows("user_account", days),
            "FRAs Created":     SystemLogEntity.count_new_rows("fundraising_activity", days),
            "Active FRAs":      SystemLogEntity.count_active_fras(),
            "Total Raised ($)": f"{SystemLogEntity.total_raised():,.2f}",
        }
        logs = [dict(r) for r in SystemLogEntity.get_recent(days)]

        return _ok(data={
            "label": label,
            "period": period,
            "stats": stats,
            "logs": logs,
        })

