from backend.pipeline import VIPDetectionPipeline

if __name__ == "__main__":
    pipeline = VIPDetectionPipeline(official_usernames=[])

    print("\n=== VIP Account Verifier ===")
    print("Type 'exit' anytime to quit.\n")

    while True:
        username = input("Enter account name/username to check: ").strip()
        if username.lower() == "exit":
            break

        result = pipeline.check_account({"Name": username})
        if result["is_fake"]:
            print(f"❌ {username} is a FAKE account")
        else:
            print(f"✅ {username} is a VERIFIED VIP account")
