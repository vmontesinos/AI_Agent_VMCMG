import os
from dotenv import load_dotenv

def get_auth_url():
    load_dotenv()
    client_id = os.getenv("STRAVA_CLIENT_ID")
    if not client_id:
        print("Error: STRAVA_CLIENT_ID not found in .env file")
        return
    
    redirect_uri = "https://n0.vmcmg.com/rest/oauth2-credential/callback"
    scope = "read,activity:read_all"
    url = f"https://www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&approval_prompt=force&scope={scope}"
    
    print("\n1. Copy and paste this URL into your browser:")
    print(f"\n{url}\n")
    print("2. Authorize the app.")
    print("3. You will be redirected to localhost. Copy the 'code' parameter from the URL.")
    print("   Example: http://localhost/?state=&code=abcdef123456...&scope=read,activity:read_all")
    print("4. Paste that code into your .env file as STRAVA_AUTH_CODE.")

if __name__ == "__main__":
    get_auth_url()
