import sys
sys.path.insert(0, ".")

from entity.entities import init_db, UserAccountEntity

init_db()

# Test verify_password
account = UserAccountEntity.verify_password("fundraiser", "password")
print("Login test:", account["username"], "-", account["role"])

# Test wrong password
bad = UserAccountEntity.verify_password("fundraiser", "wrongpassword")
print("Bad password test:", bad)