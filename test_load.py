import joblib

vec = joblib.load("models/threat_model_vec.joblib")
clf = joblib.load("models/threat_model_clf.joblib")

print("✅ Vectorizer type:", type(vec))
print("✅ Classifier type:", type(clf))
