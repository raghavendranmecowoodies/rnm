import json
import base64

# Read cookies
with open('linkedin_cookies.json', 'r') as f:
    cookies = json.load(f)

# Convert to base64 string
cookies_str = json.dumps(cookies)
cookies_base64 = base64.b64encode(cookies_str.encode()).decode()

print("=" * 80)
print("Copy this ENTIRE value for LINKEDIN_COOKIES_BASE64:")
print("=" * 80)
print(cookies_base64)
print("=" * 80)