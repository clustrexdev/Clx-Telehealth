import json
import requests
from datetime import date, time, datetime, timedelta
from zoneinfo import ZoneInfo
from module.const import TOKEN, TOKEN_EXP_TIMESTAMP, CLIENT_ID, CLIENT_SECRET, ATHENA_BASE_URL


def form_urlencoded_content_type():
    return {
        "Content-Type": "application/x-www-form-urlencoded"
    }


def get_headers():
    try:
        return {
            "Authorization": "Bearer " + get_token()
        }
    except Exception as e:
        raise e


def post_headers():
    try:
        return get_headers() | form_urlencoded_content_type()
    except Exception as e:
        raise e


def get_request(url: str):
    try:
        response = requests.get(url, headers=get_headers())
        return json.loads(response.text), response.status_code
    except Exception as e:
        return {"error": str(e)}, 500


def post_request(url: str, headers: dict|None = None):
    try:
        if headers is None:
            headers = post_headers()
        response = requests.post(url, headers=headers)
        return json.loads(response.text), response.status_code
    except Exception as e:
        return {"error": str(e)}, 500


def is_valid_token():
    global TOKEN_EXP_TIMESTAMP
    try:
        timestamp_ist = None
        current_ist = datetime.now(ZoneInfo("Asia/Kolkata"))

        if TOKEN_EXP_TIMESTAMP is not None:
            timestamp_ist = datetime.fromtimestamp(TOKEN_EXP_TIMESTAMP, tz=ZoneInfo("Asia/Kolkata")) - timedelta(minutes=2)
        
        if TOKEN_EXP_TIMESTAMP is None or current_ist >= timestamp_ist:
            token_validation_url = f"{ATHENA_BASE_URL}/oauth2/v1/introspect"
            payload = {
                "token": TOKEN,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET
            }
            response = requests.post(token_validation_url, headers=form_urlencoded_content_type(), data=payload)
            if response.status_code == 200:
                data: dict = json.loads(response.text)
                if data.get("active"):
                    TOKEN_EXP_TIMESTAMP = data.get('exp')
                    print("Token Expiration Timestamp Updated")
                    return True
                else:
                    return False
            else:
                print(f"is_valid_token() - {token_validation_url} - {response.status_code}\nResponse: {response.text}")
                return False
        return True
    except Exception as e:
        print(f"Error in is_valid_token(): {str(e)}")
        raise e


def get_token():
    global TOKEN
    try:
        if TOKEN is None or not is_valid_token():
            print("New Token Generated")
            token_generation_url = f"{ATHENA_BASE_URL}/oauth2/v1/token"
            payload = {
                "grant_type": "client_credentials",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "scope": "athena/service/Athenanet.MDP.*"
            }
            response = requests.post(token_generation_url, headers=form_urlencoded_content_type(), data=payload)
            if response.status_code == 200:
                data: dict = json.loads(response.text)
                TOKEN = data.get("access_token")
                print("Token Updated")
                token_validation_status = "Valid" if is_valid_token() else "Invalid"
                print(f"Token Validation Status - {token_validation_status}")
            else:
                print(f"get_token() - {token_generation_url} - {response.status_code}\nResponse: {response.text}")
        return TOKEN
    except Exception as e:
        print(f"Error in get_token(): {str(e)}")
        raise e

