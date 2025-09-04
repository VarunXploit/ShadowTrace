import os
import tweepy
from tweepy.errors import Unauthorized

tok = os.environ.get("TWITTER_BEARER_TOKEN")
print("TOKEN present?", bool(tok))

if not tok:
    print("No token in env. Set with PowerShell:")
    print('$env:TWITTER_BEARER_TOKEN="YOUR_TOKEN"')
else:
    try:
        client = tweepy.Client(bearer_token=tok, wait_on_rate_limit=True)
        r = client.get_user(username="twitter")
        if r.data:
            print("✅ API reachable; got user:", r.data.username)
        else:
            print("⚠️ API call succeeded but no user data returned.")
    except Unauthorized as e:
        print("❌ UNAUTHORIZED (401):", e)
    except Exception as e:
        print("❌ Other error:", e)
