import pandas as pd
import random
from faker import Faker

fake = Faker()

# -------- Threat Posts Dataset --------
def create_threat_dataset(n=1000):
    toxic_keywords = ["kill", "hate", "destroy", "scam", "fake", "attack", "ban"]
    normal_keywords = ["love", "great", "happy", "support", "thanks", "amazing", "respect"]

    data = []
    for i in range(n):
        if random.random() < 0.3:  # 30% toxic
            text = f"{random.choice(toxic_keywords)} {fake.name()} in speech today"
            label = 1
        else:
            text = f"{random.choice(normal_keywords)} {fake.name()} at event"
            label = 0
        data.append([f"p{i}", text, label])

    return pd.DataFrame(data, columns=["post_id", "text", "is_threat"])


# -------- Fake Accounts Dataset --------
def create_account_dataset(n=500):
    data = []
    for i in range(n):
        is_fake = 1 if random.random() < 0.3 else 0
        if is_fake:
            followers = random.randint(0, 50)
            following = random.randint(1000, 5000)
            account_age = random.randint(1, 30)
            posts = random.randint(0, 5)
            has_pic = random.choice([0, 1])
            has_bio = random.choice([0, 1])
        else:
            followers = random.randint(500, 20000)
            following = random.randint(10, 5000)
            account_age = random.randint(100, 2000)
            posts = random.randint(10, 2000)
            has_pic = 1
            has_bio = 1

        data.append([
            f"user{i}", followers, following, account_age, posts,
            has_pic, has_bio, is_fake
        ])

    return pd.DataFrame(data, columns=[
        "user_id", "followers_count", "following_count", "account_age_days",
        "post_count", "has_profile_pic", "has_bio", "is_fake"
    ])


if __name__ == "__main__":
    # Generate datasets
    threat_df = create_threat_dataset(1000)
    account_df = create_account_dataset(500)

    # Save to data/ folder
    threat_df.to_csv("data/threat_dataset.csv", index=False)
    account_df.to_csv("data/fake_accounts.csv", index=False)

    print("✅ Datasets created in data/:")
    print(" - threat_dataset.csv")
    print(" - fake_accounts.csv")