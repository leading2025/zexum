from flask import Flask, render_template, jsonify
import requests, os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = Flask(__name__)

def fetch_zexum_survey():
    """
    Call Zexum survey API with token authentication, retries, and timeout.
    Returns API response (JSON) or raises exception on failure.
    """
    TOKEN = os.environ.get("ZEXUM_TOKEN")
    if not TOKEN:
        raise Exception("ZEXUM_TOKEN environment variable not set")

    API_URL = "https://api.zexumglobalresearch.net/api/getsurvey"
    MAX_RETRIES = 2        # 2 retries = 3 total attempts
    RETRY_DELAY_SEC = 1    # 1 second backoff
    TIMEOUT_SEC = 190      # match client original

    # Retry strategy
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_DELAY_SEC,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)

    headers = {"token": TOKEN}

    try:
        response = http.get(API_URL, headers=headers, timeout=TIMEOUT_SEC)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Zexum API call failed: {str(e)}") from e
    finally:
        http.close()

def process_survey_data(raw_data):
    """
    Extract UID, remove duplicates, keep only valid survey links.
    """
    surveys = raw_data.get('data', {}).get('data', [])
    processed = []
    seen_uids = set()

    for s in surveys:
        link = s.get('link', '').replace('\\', '')
        uid = None
        if 'uid=' in link:
            uid = link.split('uid=')[1].split('&')[0].strip()
        
        if uid and uid not in seen_uids:
            seen_uids.add(uid)
            s['uid'] = uid
            s['link'] = link
            processed.append(s)
    
    return processed

@app.route("/get-zexum-survey")
def get_zexum_survey_route():
    try:
        survey_data = fetch_zexum_survey()
        survey_data['data']['data'] = process_survey_data(survey_data)
        return {"status":"success","data":survey_data}, 200
    except Exception as e:
        return {"status":"error","message":str(e)}, 500

@app.route("/view-surveys")
def view_surveys():
    return render_template("survey.html")

@app.route("/")
def home():
    return render_template("survey.html")

if __name__=="__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
