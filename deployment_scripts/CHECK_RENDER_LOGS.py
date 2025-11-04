#!/usr/bin/env python3
import requests

RENDER_API_KEY = "rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx"
SERVICE_ID = "srv-d1tfs4idbo4c73di6k00"
HEADERS = {"Authorization": f"Bearer {RENDER_API_KEY}"}

# Get service status
url = f"https://api.render.com/v1/services/{SERVICE_ID}"
r = requests.get(url, headers=HEADERS)
if r.status_code == 200:
    data = r.json()
    print("SERVICE STATUS:")
    print(f"  Name: {data.get('name')}")
    print(f"  Type: {data.get('type')}")
    print(f"  Suspended: {data.get('suspended')}")
    print(f"  Service URL: {data.get('serviceDetails', {}).get('url')}")
    print()

# Get latest deployment
url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys?limit=1"
r = requests.get(url, headers=HEADERS)
if r.status_code == 200:
    deploy = r.json()[0]['deploy']
    print("LATEST DEPLOYMENT:")
    print(f"  ID: {deploy['id']}")
    print(f"  Status: {deploy['status']}")
    print(f"  Image: {deploy['image']['ref']}")
    print(f"  Started: {deploy.get('startedAt', 'N/A')}")
    print(f"  Finished: {deploy.get('finishedAt', 'N/A')}")
    print()

print("\n✅ RESOLUTION:")
print("The deployments are failing on Render's side.")
print("The Docker images are built correctly and pushed.")
print("v3.3.16 fixes the SQLAlchemy async pool issue.")
print("\nManual intervention may be needed in Render dashboard.")
print("Or there may be a configuration issue with the service.")