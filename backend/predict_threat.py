import joblib

VEC_PATH = "models/threat_model_vec.joblib"
CLF_PATH = "models/threat_model_clf.joblib"

def load():
    vec = joblib.load(VEC_PATH)
    clf = joblib.load(CLF_PATH)
    return vec, clf

def predict(text, vec, clf):
    X = vec.transform([text])
    proba = clf.predict_proba(X)[0, 1]
    pred = int(proba >= 0.6)  # threshold; adjust if needed
    return pred, proba

if __name__ == "__main__":
    vec, clf = load()
    print("Type a post (blank to exit):")
    while True:
        t = input("> ").strip()
        if not t:
            break
        label, score = predict(t, vec, clf)
        print(f"Threat={bool(label)} | score={score:.3f}")
