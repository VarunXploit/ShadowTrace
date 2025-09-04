from backend.pipeline import VIPDetectionPipeline

if __name__ == "__main__":
    vip_list = ["viratkohli", "iamsrk", "neeraj_chopra"]
    pipeline = VIPDetectionPipeline(official_usernames=vip_list)

    # Threat tests
    print("=== Threat tests ===")
    print("1:", pipeline.check_text("I will kill the VIP tomorrow"))
    print("2:", pipeline.check_text("What an amazing speech by the VIP today"))

    # Fake account tests
    print("\n=== Fake account tests ===")
    fake_account = {
        "followers_count": 20,
        "following_count": 2000,
        "account_age_days": 5,
        "post_count": 2,
        "has_profile_pic": 0,
        "has_bio": 0
    }
    real_account = {
        "followers_count": 5000,
        "following_count": 300,
        "account_age_days": 800,
        "post_count": 450,
        "has_profile_pic": 1,
        "has_bio": 1
    }
    print("Fake sample ->", pipeline.check_account(fake_account))
    print("Real sample ->", pipeline.check_account(real_account))

    # Impersonation username
    print("\n=== Impersonation username ===")
    print("username ->", pipeline.check_username("v1ratkohli"))

    # If you have images in data/, test profile pic (optional)
    try:
        print("\n=== Impersonation image (optional) ===")
        print(pipeline.check_profile_pic("data/vip_profile.jpg", "data/suspicious_profile.jpg"))
    except Exception as e:
        print("Image test skipped:", e)
