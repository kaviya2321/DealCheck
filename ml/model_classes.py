"""
Core Model Classes for DealCheck:
- ScamRiskModel (Model A)
- SellerReplyModel (Model B)
"""

import numpy as np

class ScamRiskModel:
    def __init__(self, vectorizer, base_estimator, calibrated_clf):
        self.vectorizer = vectorizer
        self.base_estimator = base_estimator
        self.calibrated_clf = calibrated_clf
        self.feature_names = np.array(vectorizer.get_feature_names_out())
        self.coefficients = base_estimator.coef_[0]
        # Precompute positive coefficient map for explainability lookup
        self.pos_coef_map = {
            self.feature_names[i]: float(self.coefficients[i])
            for i in range(len(self.feature_names))
            if self.coefficients[i] > 0.05
        }

    def predict_proba(self, texts):
        X = self.vectorizer.transform(texts)
        return self.calibrated_clf.predict_proba(X)[:, 1]

    def predict(self, texts, threshold=0.5):
        probs = self.predict_proba(texts)
        return (probs >= threshold).astype(int)


class SellerReplyModel:
    def __init__(self, pipeline, label_map):
        self.pipeline = pipeline
        self.label_map = label_map

    def predict(self, texts):
        preds = self.pipeline.predict(texts)
        return [self.label_map[p] for p in preds]

    def predict_proba(self, texts):
        return self.pipeline.predict_proba(texts)

    def analyze(self, reply_text: str):
        probs = self.predict_proba([reply_text])[0]
        pred_idx = int(np.argmax(probs))
        class_name = self.label_map[pred_idx]
        conf = float(probs[pred_idx])

        if pred_idx == 0:  # Accepts protected
            risk_delta = -40
            litmus_verdict = "PASSED"
            summary = "Seller agreed to PayPal Goods & Services. Legitimate seller behavior verified."
        elif pred_idx == 1:  # Refuses
            risk_delta = +20
            litmus_verdict = "WARNING"
            summary = "Seller refused protected online payment. Exercise caution (prefer cash in public space)."
        else:  # Pushes F&F
            risk_delta = +40
            litmus_verdict = "FAILED"
            summary = "Seller actively demanded PayPal Friends & Family to bypass buyer protection. High risk scam vector."

        return {
            "classification": class_name,
            "confidence": round(conf, 4),
            "probabilities": {self.label_map[i]: round(float(probs[i]), 4) for i in range(len(self.label_map))},
            "risk_delta": risk_delta,
            "litmus_verdict": litmus_verdict,
            "summary": summary
        }
