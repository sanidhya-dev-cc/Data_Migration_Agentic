import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

missing = [name for name, val in [
    ("AZURE_OPENAI_API_KEY", API_KEY),
    ("AZURE_OPENAI_ENDPOINT", ENDPOINT),
    ("AZURE_OPENAI_DEPLOYMENT", DEPLOYMENT),
] if not val]

if missing:
    print("Missing environment variables:", ", ".join(missing))
    print("Make sure they are set in your environment or in a .env file next to Test.py")
    raise SystemExit(1)

url = f"{ENDPOINT.rstrip('/')}/openai/deployments/{DEPLOYMENT}/chat/completions?api-version={API_VERSION}"
headers = {"Content-Type": "application/json", "api-key": API_KEY}
payload = {
    "messages": [
        {"role": "system", "content": "You are a simple checker."},
        {"role": "user", "content": "Say 'ok' if you can receive this request."}
    ],
    "max_tokens": 10
}

print("Sending request to:", url)
print("API key set:", bool(API_KEY))

try:
    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    print("HTTP status:", resp.status_code)
    try:
        body = resp.json()
        print(json.dumps(body, indent=2))
    except Exception:
        print("Response text:", resp.text)

    if resp.status_code == 200:
        print("Credentials appear to work.")
    else:
        print("Request failed — check endpoint, deployment name, API key and api-version.")
        if resp.status_code in (401, 403):
            print("Authentication error: verify API key and deployment permissions.")
        elif resp.status_code == 404:
            print("Not found: check deployment name and API version.")
except requests.exceptions.RequestException as e:
    print("Request error:", e)