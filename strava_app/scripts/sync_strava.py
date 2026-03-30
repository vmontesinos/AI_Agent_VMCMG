import os
import logging
import requests
import psycopg2
from psycopg2.extras import execute_values, Json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# Configuration
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")

DB_NAME = os.getenv("DB_NAME", "entrenador_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

STRAVA_API_URL = "https://www.strava.com/api/v3"
TOKEN_URL = "https://www.strava.com/oauth/token"


def _strava_session():
    """Returns a requests.Session with retry logic for Strava API calls."""
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def get_access_token():
    """Refreshes the Strava access token."""
    log.info("Refreshing Strava access token...")
    payload = {
        "client_id": STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "refresh_token": STRAVA_REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }
    session = _strava_session()
    response = session.post(TOKEN_URL, data=payload, timeout=30)
    response.raise_for_status()
    return response.json()["access_token"]


def get_last_activity_timestamp(conn):
    """Returns the Unix timestamp of the most recent activity in the DB."""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(start_date) FROM strava_activities")
            res = cur.fetchone()
        if res and res[0]:
            log.info("Last activity found: %s", res[0])
            return int(res[0].timestamp())
    except psycopg2.Error as e:
        log.warning("Could not read last activity timestamp: %s", e)
    return None


def fetch_activities(access_token, conn, after=None):
    """Fetches activities from Strava after a given timestamp."""
    if after is None:
        last_ts = get_last_activity_timestamp(conn)
        if last_ts:
            after = last_ts
        else:
            after = int((datetime.now() - timedelta(days=365)).timestamp())

    log.info("Fetching activities since %s...", datetime.fromtimestamp(after))

    session = _strava_session()
    headers = {"Authorization": f"Bearer {access_token}"}
    activities = []
    page = 1

    while True:
        response = session.get(
            f"{STRAVA_API_URL}/athlete/activities",
            headers=headers,
            params={"after": after, "page": page, "per_page": 50},
            timeout=30,
        )
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break
        activities.extend(batch)
        log.info("  Page %d: %d activities (total: %d)", page, len(batch), len(activities))
        page += 1

    return activities


def sync_to_db(activities, conn):
    """Inserts or updates activities in PostgreSQL."""
    if not activities:
        log.info("No activities to sync.")
        return

    upsert_query = """
    INSERT INTO strava_activities (
        strava_id, name, type, sport_type, start_date, start_date_local,
        distance, moving_time, elapsed_time, total_elevation_gain,
        average_heartrate, max_heartrate, average_speed, max_speed,
        suffer_score, kudos_count, achievement_count, timezone, metadata
    ) VALUES %s
    ON CONFLICT (strava_id) DO UPDATE SET
        name                 = EXCLUDED.name,
        type                 = EXCLUDED.type,
        sport_type           = EXCLUDED.sport_type,
        distance             = EXCLUDED.distance,
        moving_time          = EXCLUDED.moving_time,
        elapsed_time         = EXCLUDED.elapsed_time,
        total_elevation_gain = EXCLUDED.total_elevation_gain,
        average_heartrate    = EXCLUDED.average_heartrate,
        max_heartrate        = EXCLUDED.max_heartrate,
        average_speed        = EXCLUDED.average_speed,
        max_speed            = EXCLUDED.max_speed,
        suffer_score         = EXCLUDED.suffer_score,
        kudos_count          = EXCLUDED.kudos_count,
        achievement_count    = EXCLUDED.achievement_count,
        timezone             = EXCLUDED.timezone,
        metadata             = EXCLUDED.metadata,
        synced_at            = CURRENT_TIMESTAMP;
    """

    data_to_insert = []
    for activity in activities:
        metadata = {
            "gear_id":     activity.get("gear_id"),
            "device_name": activity.get("device_name"),
            "elev_high":   activity.get("elev_high"),
            "elev_low":    activity.get("elev_low"),
        }
        data_to_insert.append((
            activity["id"],
            activity["name"],
            activity["type"],
            activity.get("sport_type"),
            activity["start_date"],
            activity.get("start_date_local"),
            activity["distance"],
            activity["moving_time"],
            activity["elapsed_time"],
            activity.get("total_elevation_gain"),
            activity.get("average_heartrate"),
            activity.get("max_heartrate"),
            activity.get("average_speed"),
            activity.get("max_speed"),
            activity.get("suffer_score"),
            activity.get("kudos_count", 0),
            activity.get("achievement_count", 0),
            activity.get("timezone"),
            Json(metadata),
        ))

    with conn.cursor() as cur:
        execute_values(cur, upsert_query, data_to_insert)
    conn.commit()
    log.info("Successfully synced %d activities.", len(data_to_insert))


def main():
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        access_token = get_access_token()
        activities = fetch_activities(access_token, conn)
        sync_to_db(activities, conn)
    except psycopg2.Error as e:
        log.error("Database error: %s", e)
        raise
    except requests.RequestException as e:
        log.error("Strava API error: %s", e)
        raise
    except Exception as e:
        log.error("Unexpected error during synchronization: %s", e)
        raise
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
