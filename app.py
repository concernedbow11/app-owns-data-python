from flask import Flask, render_template, jsonify
import requests
from msal import ConfidentialClientApplication

from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
WORKSPACE_ID = os.getenv("WORKSPACE_ID")
REPORT_ID = os.getenv("REPORT_ID")
AUTHORITY_URL = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]
POWER_BI_API = "https://api.powerbi.com/v1.0/myorg"

app = Flask(__name__)

# MSAL Client
msal_app = ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY_URL,
    client_credential=CLIENT_SECRET,
)


# Function to get an Azure AD access token
def get_access_token():
    result = msal_app.acquire_token_for_client(scopes=SCOPE)
    if "access_token" in result:                            
        return result["access_token"]
    else:
        raise Exception(f"Failed to get access token: {result}")


# Function to get Power BI Embed Token
def get_embed_token():
    access_token = get_access_token()

    # API URL to generate an embed token
    url = f"{POWER_BI_API}/groups/{WORKSPACE_ID}/reports/{REPORT_ID}/GenerateToken"

    headers = {"Authorization": f"Bearer {access_token}"}
    body = {"accessLevel": "view"}

    response = requests.post(url, headers=headers, json=body)

    if response.status_code == 200:
        response_json = response.json()
        if "token" in response_json:
            return response_json["token"]
        else:
            raise Exception(f"'token' not found in the response: {response_json}")
    else:
        raise Exception(f"Failed to get embed token: {response.status_code} {response.text}")


@app.route("/")
def home():
    try:
        # Get Embed Token and Report Embed URL
        embed_token = get_embed_token()
        

        # API to get report details
        report_url = f"{POWER_BI_API}/groups/{WORKSPACE_ID}/reports/{REPORT_ID}"
        access_token = get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        report_response = requests.get(report_url, headers=headers)

        if report_response.status_code == 200:
            report_data = report_response.json()
            embed_url = report_data["embedUrl"]
        else:
            raise Exception(f"Failed to get report details: {report_response.json()}")

        return render_template(
            "index.html",
            embed_url=embed_url,
            embed_token=embed_token,
            access_token=access_token,
            report_id=REPORT_ID,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
