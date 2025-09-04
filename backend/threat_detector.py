import os
import joblib

class ThreatDetector:
    def __init__(self,
                 vec_path="models/threat_model_vec.joblib",
                 clf_path="models/threat_model_clf.joblib"):
        if not os.path.exists(vec_path) or not os.path.exists(clf_path):
            raise FileNotFoundError(f"Threat model files missing. Expected: {vec_path}, {clf_path}")
        self.vec = joblib.load(vec_path)
        self.clf = joblib.load(clf_path)

        # Keyword dictionary
        self.threat_keywords = [
            "kill", "murder", "shoot", "bomb", "attack",
            "hack", "stab", "destroy", "explode",
            "gun", "knife", "terrorist", "assassinate",
            "threat", "blast", "execute"
        ]

    def predict(self, text: str, threshold: float = 0.6):
        text = str(text or "").lower()
        X = self.vec.transform([text])

        # Model prediction
        if hasattr(self.clf, "predict_proba"):
            prob = float(self.clf.predict_proba(X)[0, 1])
        else:
            score = float(self.clf.decision_function(X)[0])
            prob = 1 / (1 + pow(2.718281828, -score))

        model_label = bool(prob >= threshold)

        # Keyword-based fallback
        keyword_hit = any(word in text for word in self.threat_keywords)

        # Final decision: either ML OR keywords
        final_label = model_label or keyword_hit

        return {
            "is_threat": final_label,
            "probability": prob,
            "keyword_hit": keyword_hit
        }
