import requests

BASE_URL = "https://skill-loop-backend.onrender.com"

# Step 1: Public endpoint test
r = requests.get(f"{BASE_URL}/api/public")
print("[Public]", r.status_code, r.json())

# Step 2: Login to get JWT token
login_payload = {
    "username": "your_username",   # replace with a valid username
    "password": "your_password"    # replace with a valid password
}

r = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)
if r.status_code == 200:
    token = r.json().get("access_token")
    print("[Login] Success! Token obtained.")
else:
    print("[Login] Failed:", r.status_code, r.text)
    token = None

# Step 3: Access protected routes using token
if token:
    headers = {"Authorization": f"Bearer {token}"}

    protected_routes = [
        "/api/users",
        "/api/skills",
        "/api/matches",
        "/api/sessions",
        "/api/credits"
    ]

    for route in protected_routes:
        r = requests.get(f"{BASE_URL}{route}", headers=headers)
        print(f"[{route}]", r.status_code, r.json())
