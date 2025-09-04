import os
import sys
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

DATA_PATH = os.path.join("data", "threat_dataset.csv")
MODELS_DIR = "models"
VEC_PATH = os.path.join(MODELS_DIR, "threat_model_vec.joblib")
CLF_PATH = os.path.join(MODELS_DIR, "threat_model_clf.joblib")
REPORT_PATH = os.path.join(MODELS_DIR, "threat_report.txt")

def main():
    # 0) Ensure folders
    os.makedirs(MODELS_DIR, exist_ok=True)

    # 1) Load data
    if not os.path.exists(DATA_PATH):
        print(f"[ERROR] Can't find {DATA_PATH}. Put your CSV there and try again.")
        sys.exit(1)

    df = pd.read_csv(DATA_PATH)
    required_cols = {"text", "is_threat"}
    if not required_cols.issubset(df.columns):
        print(f"[ERROR] CSV must have columns: {required_cols}. Found: {list(df.columns)}")
        sys.exit(1)

    # 2) Basic clean (optional: TF-IDF will handle most)
    df["text"] = df["text"].astype(str).fillna("")

    # 3) Train/Test split (stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["is_threat"], test_size=0.2, stratify=df["is_threat"], random_state=42
    )

    # 4) Vectorizer
    vec = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        stop_words="english"
    )
    Xtr = vec.fit_transform(X_train)
    Xte = vec.transform(X_test)

    # 5) Classifier
    clf = LogisticRegression(max_iter=1000, class_weight="balanced", solver="liblinear")
    clf.fit(Xtr, y_train)

    # 6) Evaluate
    preds = clf.predict(Xte)
    try:
        proba = clf.predict_proba(Xte)[:, 1]
        auc = roc_auc_score(y_test, proba)
    except Exception:
        proba, auc = None, None

    report = classification_report(y_test, preds, digits=3)
    cm = confusion_matrix(y_test, preds)

    print("\n=== Classification Report ===")
    print(report)
    print("Confusion Matrix (rows=true, cols=pred):")
    print(cm)
    if auc is not None:
        print(f"ROC-AUC: {auc:.3f}")

    # 7) Save model + vectorizer + report
    joblib.dump(vec, VEC_PATH)
    joblib.dump(clf, CLF_PATH)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("=== Classification Report ===\n")
        f.write(report + "\n")
        f.write("Confusion Matrix (rows=true, cols=pred):\n")
        f.write(str(cm) + "\n")
        if auc is not None:
            f.write(f"ROC-AUC: {auc:.3f}\n")

    print(f"\n✅ Saved models to: {MODELS_DIR}\\")
    print(f" - {VEC_PATH}")
    print(f" - {CLF_PATH}")
    print(f" - {REPORT_PATH}")

if __name__ == "__main__":
    main()
