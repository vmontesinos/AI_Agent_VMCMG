import os
import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Configuration
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")

DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

STRAVA_API_URL = "https://www.strava.com/api/v3"
TOKEN_URL = "https://www.strava.com/oauth/token"

def get_access_token():
    """Refreshes the Strava access token."""
    print("Refreshing Strava access token...")
    payload = {
        'client_id': STRAVA_CLIENT_ID,
        'client_secret': STRAVA_CLIENT_SECRET,
        'refresh_token': STRAVA_REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    }
    response = requests.post(TOKEN_URL, data=payload)
    response.raise_for_status()
    data = response.json()
    return data['access_token']

def get_last_activity_timestamp():
    """Returns the timestamp of the last activity in the database."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute("SELECT MAX(start_date) FROM strava_activities")
        res = cur.fetchone()
        cur.close()
        conn.close()
        
        if res and res[0]:
            print(f"Found last activity from: {res[0]}")
            return int(res[0].timestamp())
    except Exception as e:
        print(f"No previous activities found or error: {e}")
    return None

def fetch_activities(access_token, after=None):
    """Fetches activities from Strava after a certain timestamp."""
    activities = []
    page = 1
    per_page = 50
    
    # Calculate timestamp for one year ago if not provided
    if after is None:
        last_ts = get_last_activity_timestamp()
        if last_ts:
            after = last_ts
        else:
            one_year_ago = datetime.now() - timedelta(days=365)
            after = int(one_year_ago.timestamp())
    
    print(f"Fetching activities since {datetime.fromtimestamp(after)}...")
    
    while True:
        params = {
            'after': after,
            'page': page,
            'per_page': per_page
        }
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(f"{STRAVA_API_URL}/athlete/activities", headers=headers, params=params)
        response.raise_for_status()
        
        batch = response.json()
        if not batch:
            break
            
        activities.extend(batch)
        print(f"  Retrieved {len(batch)} activities (Total: {len(activities)})")
        page += 1
        
    return activities

def sync_to_db(activities):
    """Inserts or updates activities in the PostgreSQL database."""
    if not activities:
        print("No activities to sync.")
        return

    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()

    upsert_query = """
    INSERT INTO strava_activities (
        strava_id, name, type, sport_type, start_date, start_date_local,
        distance, moving_time, elapsed_time, total_elevation_gain,
        average_heartrate, max_heartrate, average_speed, max_speed,
        suffer_score, kudos_count, achievement_count, timezone, metadata
    ) VALUES %s
    ON CONFLICT (strava_id) DO UPDATE SET
        name = EXCLUDED.name,
        type = EXCLUDED.type,
        distance = EXCLUDED.distance,
        moving_time = EXCLUDED.moving_time,
        average_heartrate = EXCLUDED.average_heartrate,
        max_heartrate = EXCLUDED.max_heartrate,
        suffer_score = EXCLUDED.suffer_score,
        synced_at = CURRENT_TIMESTAMP;
    """

    data_to_insert = []
    for activity in activities:
        # Extract metadata while avoiding "junk"
        metadata = {
            "gear_id": activity.get("gear_id"),
            "device_name": activity.get("device_name"),
            "elev_high": activity.get("elev_high"),
            "elev_low": activity.get("elev_low"),
        }
        
        data_to_insert.append((
            activity['id'],
            activity['name'],
            activity['type'],
            activity.get('sport_type'),
            activity['start_date'],
            activity.get('start_date_local'),
            activity['distance'],
            activity['moving_time'],
            activity['elapsed_time'],
            activity.get('total_elevation_gain'),
            activity.get('average_heartrate'),
            activity.get('max_heartrate'),
            activity.get('average_speed'),
            activity.get('max_speed'),
            activity.get('suffer_score'),
            activity.get('kudos_count', 0),
            activity.get('achievement_count', 0),
            activity.get('timezone'),
            psycopg2.extras.Json(metadata)
        ))

    execute_values(cur, upsert_query, data_to_insert)
    conn.commit()
    cur.close()
    conn.close()
    print(f"Successfully synced {len(data_to_insert)} activities to the database.")

def main():
    try:
        # 1. Get token
        access_token = get_access_token()
        
        # 2. Fetch activities
        activities = fetch_activities(access_token)
        
        # 3. Sync to DB
        sync_to_db(activities)
        
    except Exception as e:
        print(f"Error during synchronization: {e}")

if __name__ == "__main__":
    main()
