from flask import Flask, render_template, jsonify
import requests, os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = Flask(__name__)

def fetch_zexum_survey():
    TOKEN = os.environ.get("ZEXUM_TOKEN")
    if not TOKEN:
        raise Exception("ZEXUM_TOKEN environment variable not set")
    API_URL = "https://api.zexumglobalresearch.net/api/getsurvey"
    MAX_RETRIES = 2
    RETRY_DELAY_SEC = 1
    TIMEOUT_SEC = 30

    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_DELAY_SEC,
        status_forcelist=[429,500,502,503,504],
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

@app.route("/get-zexum-survey")
def get_zexum_survey_route():
    try:
        survey_data = fetch_zexum_survey()
        return {"status":"success","data":survey_data},200
    except Exception as e:
        return {"status":"error","message":str(e)},500

@app.route("/view-surveys")
def view_surveys():
    return render_template("surveys.html")

@app.route("/")
def home():
    return render_template("surveys.html")

if __name__=="__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
