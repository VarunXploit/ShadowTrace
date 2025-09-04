# twitter_pipeline.py
import tweepy
from datetime import datetime, timezone
from dateutil import parser as date_parser
from backend.pipeline import VIPDetectionPipeline

# load config
from twitter_config import BEARER_TOKEN

# --- init clients & pipeline ---
if not BEARER_TOKEN:
    raise RuntimeError("Set TWITTER_BEARER_TOKEN env var (see twitter_config.py)")

client = tweepy.Client(bearer_token=BEARER_TOKEN, wait_on_rate_limit=True)
# initialize the pipeline with known VIP usernames (lowercase)
VIP_USERNAMES = ["cristiano", "leomessi", "kendalljenner"]   # adapt to your list
pipeline = VIPDetectionPipeline(official_usernames=VIP_USERNAMES)

# --- helper functions ---
def days_between(dt):
    now = datetime.now(timezone.utc)
    return (now - dt).days

def analyze_twitter_username(username, max_tweets=100):
    """
    Main analyzer:
      - fetch user by username,
      - fetch recent tweets,
      - compute heuristics,
      - run pipeline checks (threats + impersonation).
    Returns summary dict.
    """
    username = username.lstrip("@")
    # 1) get user object with needed fields
    user_resp = client.get_user(username=username,
                                user_fields=["created_at","public_metrics","verified","description","name"])
    if user_resp.data is None:
        return {"error": "User not found"}

    user = user_resp.data
    uid = user.id
    verified = bool(user.verified)
    created_at = user.created_at  # datetime
    metrics = user.public_metrics or {}
    followers = metrics.get("followers_count", 0)
    following = metrics.get("following_count", 0)
    tweet_count_total = metrics.get("tweet_count", 0)

    acc_age_days = days_between(created_at) if created_at else None

    # 2) fetch recent tweets (v2 GET /users/:id/tweets)
    tweets = []
    try:
        resp = client.get_users_tweets(id=uid,
                                      max_results=100,
                                      tweet_fields=["created_at","public_metrics","referenced_tweets","text"],
                                      expansions=None)
        if resp and resp.data:
            tweets = resp.data
    except Exception as e:
        # API may restrict past tweets; fall back to empty tweets list
        tweets = []

    # 3) compute tweet-level heuristics
    total = len(tweets)
    retweet_count = 0
    threat_tweets = []
    original_count = 0
    last_dates = []
    for t in tweets:
        # referenced_tweets indicates retweet / quote / reply in v2
        ref = getattr(t, "referenced_tweets", None)
        is_retweet = False
        if ref:
            # ref is a list of dict-like objects
            # if any referenced tweet type == 'retweeted' treat as retweet
            for r in ref:
                if r.type == "retweeted" or r.get("type","") == "retweeted":
                    is_retweet = True
        if is_retweet:
            retweet_count += 1
        else:
            original_count += 1

        # track last 10 tweet dates for frequency
        if getattr(t, "created_at", None):
            last_dates.append(t.created_at)

        # threat detection on tweet text
        text = getattr(t, "text", "")
        res = pipeline.check_text(text)
        if res.get("is_threat"):
            threat_tweets.append({"text": text, "prob": res.get("probability"), "keyword_hit": res.get("keyword_hit")})

    retweet_ratio = (retweet_count / total) if total > 0 else 0
    tweets_per_day = None
    if acc_age_days and acc_age_days > 0:
        tweets_per_day = tweet_count_total / acc_age_days

    # 4) heuristics summary for account authenticity
    suspicious_reasons = []
    account_status = "Needs manual review"

    # rule: verified => likely real
    if verified:
        account_status = "Verified (likely real)"
    else:
        # rule: new account with VIP substring in username OR display name
        lower_username = username.lower()
        lower_name = (getattr(user, "name", "") or "").lower()
        vip_in_name = any(vip.lower() in lower_username or vip.lower() in lower_name for vip in VIP_USERNAMES)
        if acc_age_days is not None and acc_age_days < 90 and vip_in_name:
            suspicious_reasons.append("new account with VIP-like name")
            account_status = "Suspicious: new account with VIP-like name"
        elif followers < 100 and following > 500:
            suspicious_reasons.append("low followers, following high")
            account_status = "Suspicious: low followers and high following"
        elif retweet_ratio > 0.8 and original_count < 5:
            suspicious_reasons.append("mostly retweets, few originals")
            account_status = "Suspicious: amplification/retweet cluster"
        else:
            account_status = "Likely real (no strong heuristics)"

    # 5) impersonation check: check both username and display name
    imp_user = pipeline.check_username(username)
    imp_display = pipeline.check_username(getattr(user, "name", ""))

    # 6) prepare result
    result = {
        "username": username,
        "display_name": getattr(user, "name", ""),
        "verified": verified,
        "followers": followers,
        "following": following,
        "tweet_count_total": tweet_count_total,
        "account_age_days": acc_age_days,
        "tweets_fetched": total,
        "retweet_count": retweet_count,
        "retweet_ratio": round(retweet_ratio, 3),
        "tweets_per_day": round(tweets_per_day, 3) if tweets_per_day is not None else None,
        "account_status": account_status,
        "suspicious_reasons": suspicious_reasons,
        "impersonation_username": imp_user,
        "impersonation_displayname": imp_display,
        "threat_tweets": threat_tweets
    }
    return result

# --- CLI runner ---
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python twitter_pipeline.py <twitter_username>")
        sys.exit(1)
    uname = sys.argv[1]
    out = analyze_twitter_username(uname)
    import json
    print(json.dumps(out, indent=2, default=str))
