import joblib
import pandas as pd

SCALER_PATH = "models/fake_scaler.joblib"
CLF_PATH = "models/fake_model.joblib"

def load():
    scaler = joblib.load(SCALER_PATH)
    clf = joblib.load(CLF_PATH)
    return scaler, clf

def predict(account_dict, scaler, clf):
    df = pd.DataFrame([account_dict])
    Xs = scaler.transform(df)
    pred = clf.predict(Xs)[0]
    proba = clf.predict_proba(Xs)[0, 1]
    return pred, proba

if __name__ == "__main__":
    scaler, clf = load()
    test_account = {
        "followers_count": 20,
        "following_count": 2000,
        "account_age_days": 5,
        "post_count": 2,
        "has_profile_pic": 0,
        "has_bio": 0
    }
    pred, proba = predict(test_account, scaler, clf)
    print("Fake?" , bool(pred), "| Probability:", round(proba, 3))
