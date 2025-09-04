from backend.pipeline import VIPDetectionPipeline

if __name__ == "__main__":
    pipeline = VIPDetectionPipeline(
        official_usernames=["cristiano", "leomessi", "kendalljenner"]
    )

    print("\n=== VIP Detection Interactive Tester ===")
    print("Type 'exit' anytime to quit.\n")

    while True:
        mode = input("\nChoose mode (text/account) > ").strip().lower()
        if mode == "exit":
            break

        # Threat text detection
        if mode == "text":
            text = input("Enter a comment/post: ").strip()
            result = pipeline.check_text(text)

            if result["is_threat"]:
                if result.get("keyword_hit", False):
                    print(f"⚠️ THREAT DETECTED (keyword match) → \"{text}\"")
                else:
                    print(f"⚠️ THREAT DETECTED → Probability: {result['probability']:.2f}")
            else:
                print(f"✅ Safe text → Probability: {result['probability']:.2f}")

        # Account verification
        elif mode == "account":
            username = input("Enter account name/username: ").strip()
            result = pipeline.check_account({"Name": username})
            if result["is_fake"]:
                print(f"❌ {username} is a FAKE account")
            else:
                print(f"✅ {username} is a VERIFIED VIP account")

        else:
            print("⚠️ Invalid choice. Type 'text', 'account', or 'exit'.")
