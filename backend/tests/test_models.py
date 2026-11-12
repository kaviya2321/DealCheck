import pytest
import sys
import os
import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ML_DIR = os.path.join(BASE_DIR, "ml")
sys.path.insert(0, ML_DIR)

from explainability import extract_highlighted_phrases

@pytest.fixture(scope="module")
def loaded_models():
    scam_model_path = os.path.join(ML_DIR, "models", "scam_model.joblib")
    seller_model_path = os.path.join(ML_DIR, "models", "seller_reply_model.joblib")
    
    assert os.path.exists(scam_model_path), "Model A joblib file missing"
    assert os.path.exists(seller_model_path), "Model B joblib file missing"

    model_a = joblib.load(scam_model_path)
    model_b = joblib.load(seller_model_path)
    return model_a, model_b

def test_model_a_scam_vs_legit_inference(loaded_models):
    model_a, _ = loaded_models

    scam_chat = "Buyer: Can I do PayPal G&S? Seller: No, PayPal takes fees. Send via Friends and Family only or deal is off."
    legit_chat = "Buyer: Can we meet at the library to inspect the laptop? Seller: Sure, meet me at 3pm, test it before paying."

    prob_scam = float(model_a.predict_proba([scam_chat])[0])
    prob_legit = float(model_a.predict_proba([legit_chat])[0])

    assert prob_scam > 0.70, f"Expected high scam probability, got {prob_scam}"
    assert prob_legit < 0.35, f"Expected low scam probability, got {prob_legit}"

def test_model_b_seller_replies_inference(loaded_models):
    _, model_b = loaded_models

    res_accept = model_b.analyze("Sure, send the PayPal Goods and Services link and I'll confirm.")
    assert res_accept["classification"] == "accepts_protected"
    assert res_accept["risk_delta"] == -40
    assert res_accept["litmus_verdict"] == "PASSED"

    res_refuse = model_b.analyze("No online payment. Cash in person only.")
    assert res_refuse["classification"] == "refuses_protected"
    assert res_refuse["risk_delta"] == 20
    assert res_refuse["litmus_verdict"] == "WARNING"

    res_ff = model_b.analyze("Send Friends and Family only so neither of us pays unnecessary fees.")
    assert res_ff["classification"] == "pushes_friends_and_family"
    assert res_ff["risk_delta"] == 40
    assert res_ff["litmus_verdict"] == "FAILED"

def test_explainability_highlights(loaded_models):
    model_a, _ = loaded_models
    text = "Please send payment via friends and family so we avoid fees and I'll arrange courier delivery."
    highlights = extract_highlighted_phrases(text, model=model_a)

    assert len(highlights) > 0
    phrases = [h["phrase"].lower() for h in highlights]
    assert any("friends and family" in p for p in phrases)
    # Spans should be accurate character offsets
    for h in highlights:
        span_text = text[h["start"]:h["end"]]
        assert span_text == h["phrase"]
