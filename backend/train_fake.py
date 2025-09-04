import os
import sys
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix

DATA_SYNTH = os.path.join("data", "fake_accounts.csv")
DATA_REAL = os.path.join("data", "real_vip_accounts.csv")   # your real dataset
MODELS_DIR = "models"
SCALER_PATH = os.path.join(MODELS_DIR, "fake_scaler.joblib")
CLF_PATH = os.path.join(MODELS_DIR, "fake_model.joblib")
REPORT_PATH = os.path.join(MODELS_DIR, "fake_report.txt")

def load_and_merge():
    if not os.path.exists(DATA_SYNTH):
        print("[ERROR] fake_accounts.csv not found")
        sys.exit(1)

    fake_df = pd.read_csv(DATA_SYNTH)

    if os.path.exists(DATA_REAL):
        real_df = pd.read_csv(DATA_REAL)
        if "is_fake" not in real_df.columns:
            real_df["is_fake"] = 0
        merged = pd.concat([fake_df, real_df], ignore_index=True)
    else:
        merged = fake_df

    return merged

def main():
    os.makedirs(MODELS_DIR, exist_ok=True)

    df = load_and_merge()

    # Features
    features = ["followers_count", "following_count", "account_age_days",
                "post_count", "has_profile_pic", "has_bio"]

    X = df[features]
    y = df["is_fake"]

    # Normalize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train/Test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, stratify=y, random_state=42
    )

    # Classifier (Random Forest)
    clf = RandomForestClassifier(
        n_estimators=200, max_depth=10, random_state=42, class_weight="balanced"
    )
    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)

    report = classification_report(y_test, preds, digits=3)
    cm = confusion_matrix(y_test, preds)

    print("\n=== Fake Account Classifier Report ===")
    print(report)
    print("Confusion Matrix (rows=true, cols=pred):")
    print(cm)

    # Save
    joblib.dump(scaler, SCALER_PATH)
    joblib.dump(clf, CLF_PATH)
    with open(REPORT_PATH, "w") as f:
        f.write(report + "\n")
        f.write(str(cm) + "\n")

    print(f"\n✅ Saved models to {MODELS_DIR}/")
    print(f" - {SCALER_PATH}")
    print(f" - {CLF_PATH}")
    print(f" - {REPORT_PATH}")

if __name__ == "__main__":
    main()
