import requests


def exchange_instagram_token(app_id: str, client_secret: str, short_lived_token: str) -> dict:
    # EAA tokens = Facebook/Business API → use graph.facebook.com
    # IGA/IGQ tokens = Instagram Basic Display API → use graph.instagram.com
    if short_lived_token.startswith("EAA"):
        url = "https://graph.facebook.com/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": client_secret,
            "fb_exchange_token": short_lived_token,
        }
    else:
        url = "https://graph.instagram.com/access_token"
        params = {
            "grant_type": "ig_exchange_token",
            "client_secret": client_secret,
            "access_token": short_lived_token,
        }

    response = requests.get(url, params=params)
    if not response.ok:
        print("Error:", response.status_code, response.text)
        response.raise_for_status()
    return response.json()


def check_token(token: str) -> dict:
    url = "https://graph.instagram.com/me"
    params = {"fields": "id,name,username", "access_token": token}
    response = requests.get(url, params=params)
    if not response.ok:
        print("Token check error:", response.status_code, response.text)
        response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    APP_ID = "2087625342102822"
    CLIENT_SECRET = "bf8530f8aed0a8feede19b93974e6416"
    SHORT_LIVED_TOKEN = "IGAAdqrybwrSZABZAGJfOWI4bDEwX2VpWi1NMzdYQzR1US1pWHdISG5xNm9DWmRac29rSzQtMTVqQU5IaHBfdC1TZAGdjT241MUxHS3hOZAXdyVjM5RkVZAc0ZA0TVl0STFYYi1jMkRsdzVhSFoxQzAzei1QMy1UWVlNWjZALYzVVTTRFUQZDZD"

    print("=== Token Check ===")
    info = check_token(SHORT_LIVED_TOKEN)
    print(info)

    print("\n=== Profile ===")
    r = requests.get(
        "https://graph.instagram.com/me",
        params={"fields": "id,username,account_type,media_count", "access_token": SHORT_LIVED_TOKEN}
    )
    print(r.json())

    print("\n=== Recent Media ===")
    r = requests.get(
        "https://graph.instagram.com/me/media",
        params={"fields": "id,caption,media_type,timestamp,permalink", "access_token": SHORT_LIVED_TOKEN}
    )
    print(r.json())
