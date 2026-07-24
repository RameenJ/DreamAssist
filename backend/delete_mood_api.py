import requests

# Your JWT token from the app logs
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJheWFuLmFobWVkQGdtYWlsLmNvbSIsImV4cCI6MTc3MjczNjc5N30.mg671lwNQNCLW-W8KJa9la153ZEMNM-brgN1rP7ppKs"

# Delete today's mood
response = requests.delete(
    "http://localhost:8000/users/me/mood-log/today",
    headers={"Authorization": f"Bearer {token}"}
)

print(f"Status Code: {response.status_code}")
if response.status_code == 204:
    print("✅ Today's mood has been successfully deleted!")
else:
    print(f"Response: {response.text}")
