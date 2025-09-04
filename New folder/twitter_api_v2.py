# twitter_api_v2.py

import re
from datetime import datetime, timezone
from fastapi import FastAPI, Query
import tweepy

app = FastAPI(title="Twitter Fake Account Detector V2")

# -----------------------------
# 1. Twitter API Client Setup
# -----------------------------
BEARER_TOKEN = "YOUR_BEARER_TOKEN_HERE"   # Replace with your token
client = tweepy.Client(bearer_token=BEARER_TOKEN, wait_on_rate_limit=True)


# -----------------------------
# 2. Fetch Twitter User Data
# -----------------------------
def fetch_twitter_user(username: str) -> dict:
    try:
        resp = client.get_user(
            username=username,
            user_fields=["created_at", "description", "public_metrics", "verified", "profile_image_url"]
        )
        if resp.data is None:
            return {"error": "User not found."}

        u = resp.data
        metrics = u.public_metrics or {}

        return {
            "username": u.username,
            "display_name": u.name,
            "bio": u.description or "",
            "follower_count": metrics.get("followers_count", 0),
            "following_count": metrics.get("following_count", 0),
            "tweet_count": metrics.get("tweet_count", 0),
            "verified": u.verified,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "profile_image_url": u.profile_image_url,
        }
    except Exception as e:
        return {"error": f"Tweepy failed: {e}"}


# -----------------------------
# 3. Feature Extraction
# -----------------------------
def calculate_features(data: dict, vip_name: str = None) -> dict:
    features = {}

    followers = data.get("follower_count", 0)
    following = data.get("following_count", 0)
    tweets = data.get("tweet_count", 0)
    username = data.get("username", "") or ""
    bio = data.get("bio", "") or ""
    created_iso = data.get("created_at")
    verified = data.get("verified", False)

    # Ratio
    features["follower_following_ratio"] = round(followers / max(1, following), 3) if following > 0 else float(followers)

    # Username has numbers
    features["username_has_numbers"] = bool(re.search(r"\d", username))

    # Bio short
    features["bio_is_short"] = len(bio.strip()) < 10

    # Account age
    if created_iso:
        try:
            created_dt = datetime.fromisoformat(created_iso.replace("Z", "+00:00"))
            features["account_age_days"] = (datetime.now(timezone.utc) - created_dt).days
        except Exception:
            features["account_age_days"] = -1
    else:
        features["account_age_days"] = -1

    # Tweets per day
    if features["account_age_days"] > 0:
        features["tweets_per_day"] = round(tweets / features["account_age_days"], 3)
    else:
        features["tweets_per_day"] = 0.0

    # Verified
    features["is_verified"] = bool(verified)

    # Username contains VIP name
    if vip_name:
        features["username_contains_vip"] = vip_name.lower() in username.lower()
    else:
        features["username_contains_vip"] = False

    return features


# -----------------------------
# 4. Suspicion Scoring
# -----------------------------
def calculate_score(features: dict) -> (int, str, list):
    score = 0
    reasons = []

    # Rule 1: Ratio
    ratio = features.get("follower_following_ratio", 1.0)
    if ratio < 0.2:
        score += 4; reasons.append("Very low follower/following ratio.")
    elif ratio < 0.5:
        score += 2; reasons.append("Low follower/following ratio.")

    # Rule 2: Username numbers
    if features.get("username_has_numbers", False):
        score += 2; reasons.append("Username contains numbers.")

    # Rule 3: Bio
    if features.get("bio_is_short", False):
        score += 2; reasons.append("Bio empty or too short.")

    # Rule 4: Account age
    age_days = features.get("account_age_days", -1)
    if age_days >= 0:
        if age_days < 30:
            score += 4; reasons.append(f"Very new account ({age_days} days old).")
        elif age_days < 90:
            score += 2; reasons.append(f"Relatively new account ({age_days} days old).")
    else:
        score += 1; reasons.append("Unknown account age.")

    # Rule 5: Tweets per day
    tpd = features.get("tweets_per_day", 0.0)
    if tpd > 50:
        score += 3; reasons.append(f"Very high posting rate ({tpd} tweets/day).")
    elif tpd == 0 and age_days >= 90:
        score += 1; reasons.append("Inactive despite not being new.")

    # Rule 6: VIP name similarity
    if features.get("username_contains_vip", False):
        score += 3; reasons.append("Username contains VIP name → possible impersonation.")

    # Rule 7: Verified reduces suspicion
    if features.get("is_verified", False):
        score -= 6; reasons.append("Verified account (strong authenticity).")

    # Final label
    if score >= 10:
        label = "Likely Fake"
    elif score >= 5:
        label = "Suspicious"
    else:
        label = "Likely Real"

    return max(0, score), label, reasons


# -----------------------------
# 5. FastAPI Endpoint
# -----------------------------
@app.get("/analyze/twitter")
def analyze_twitter(username: str = Query(..., description="Twitter handle without @"),
                    vip_name: str = Query(None, description="VIP name for impersonation check")):
    data = fetch_twitter_user(username)
    if "error" in data:
        return {"status": "error", "message": data["error"]}

    features = calculate_features(data, vip_name)
    score, label, reasons = calculate_score(features)

    return {
        "platform": "Twitter",
        "username": username,
        "data": data,
        "features": features,
        "suspicion_score": score,
        "label": label,
        "reasons": reasons,
    }
