import os
import requests
from dotenv import load_dotenv

def exchange_code():
    load_dotenv()
    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")
    auth_code = os.getenv("STRAVA_AUTH_CODE")
    
    if not all([client_id, client_secret, auth_code]):
        print("Error: STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, and STRAVA_AUTH_CODE must be in .env")
        return

    print("Exchanging code for tokens...")
    url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': auth_code,
        'grant_type': 'authorization_code'
    }
    
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        data = response.json()
        print("\nSUCCESS!")
        print(f"Refresh Token: {data['refresh_token']}")
        print(f"Access Token: {data['access_token']}")
        print("\n--> Update your .env file with this STRAVA_REFRESH_TOKEN.")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    exchange_code()
