import requests
from flask import Flask, redirect, request

APP_ID = "2087625342102822"
CLIENT_SECRET = "bf8530f8aed0a8feede19b93974e6416"
REDIRECT_URI = "https://democrat-yelp-hefty.ngrok-free.dev/callback"

app = Flask(__name__)


@app.route("/login")
def login():
    url = (
        "https://api.instagram.com/oauth/authorize"
        f"?client_id={APP_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&scope=instagram_business_basic"
        "&response_type=code"
    )
    return redirect(url)


@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return f"Error: {request.args.get('error_description', 'no code')}", 400

    # Step 1: exchange code for short-lived token
    r = requests.post("https://api.instagram.com/oauth/access_token", data={
        "client_id": APP_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code,
    })
    if not r.ok:
        return f"Token exchange failed: {r.text}", 400

    short_token = r.json()["access_token"]
    user_id = r.json()["user_id"]

    # Step 2: exchange for long-lived token (~60 days)
    r2 = requests.get("https://graph.instagram.com/access_token", params={
        "grant_type": "ig_exchange_token",
        "client_secret": CLIENT_SECRET,
        "access_token": short_token,
    })
    if not r2.ok:
        return f"Long-lived exchange failed: {r2.text}", 400

    long_token = r2.json()["access_token"]
    expires_in = r2.json()["expires_in"]

    # Step 3: fetch profile
    profile = requests.get(
        f"https://graph.instagram.com/{user_id}",
        params={"fields": "id,username,account_type,media_count", "access_token": long_token}
    ).json()

    return {
        "long_lived_token": long_token,
        "expires_in_days": expires_in // 86400,
        "profile": profile,
    }


if __name__ == "__main__":
    app.run(debug=True, port=5000)
