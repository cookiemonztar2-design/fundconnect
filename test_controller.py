import sys
sys.path.insert(0, ".")

from entity.entities import init_db
from control.controllers import AuthController

init_db()

# Test 1: valid login
result = AuthController.login("fundraiser", "password", "Fund Raiser")
print("Test 1 - Valid login:", result)

# Test 2: wrong password
result = AuthController.login("fundraiser", "wrongpassword", "Fund Raiser")
print("Test 2 - Wrong password:", result)

# Test 3: wrong role
result = AuthController.login("fundraiser", "password", "Donee")
print("Test 3 - Wrong role:", result)

# Test 4: empty username
result = AuthController.login("", "password", "Fund Raiser")
print("Test 4 - Empty username:", result)