"""
Explainability Engine for DealCheck
Extracts high-impact risky phrases from buyer-seller text based on Model A's
linear coefficients and known risk patterns, returning token character spans,
contribution scores, and human-readable risk rationales for the UI.
"""

import re
from typing import List, Dict, Any

RISK_EXPLANATIONS = {
    "friends and family": "Explicit push for PayPal Friends & Family removes all PayPal Buyer Protection.",
    "friends or family": "Pushing for Friends & Family payment removes all PayPal Buyer Protection.",
    "friends & family": "Explicit push for PayPal Friends & Family removes all PayPal Buyer Protection.",
    "friends & fam": "Shorthand for Friends & Family, evading PayPal Purchase Protection.",
    "f&f": "Shorthand for Friends & Family, evading PayPal purchase protection policies.",
    "f and f": "Shorthand for Friends & Family, bypassing buyer protection.",
    "personal payment": "Requests for personal rather than goods transfers leave no recourse for disputes.",
    "avoid fees": "Evading PayPal processing fees is a primary tactic used by fraudulent sellers.",
    "fee": "Mentions of fees often accompany excuses to avoid Goods & Services protection.",
    "21 days": "Mentions of PayPal's 21-day hold for new/unverified accounts to coerce F&F transfer.",
    "deposit": "Requiring an advance deposit before viewing or verification is a signature scam indicator.",
    "advance": "Advance payment demands before meeting or dispatching physical goods.",
    "token": "Booking token demand before showing the product or providing verifiable proof.",
    "zelle": "Zelle transfers are instant and lack buyer dispute mechanisms for merchandise.",
    "cashapp": "CashApp offers zero buyer protection for peer-to-peer purchases from strangers.",
    "crypto": "Cryptocurrency transactions are completely irreversible and untraceable.",
    "gift card": "Demanding payment via retail gift cards is an unmistakable indicator of fraud.",
    "telegram": "Switching conversation to anonymous encrypted channels to avoid platform audit trails.",
    "whatsapp": "Luring buyers away from marketplace messaging removes platform-level safeguards.",
    "military base": "Common phantom seller trope claiming deployment to explain refusal to meet.",
    "overseas": "Seller claims overseas location to avoid physical inspection.",
    "courier": "Fake courier/escrow arrangement requiring prepaid insurance vouchers.",
    "escrow": "Unverified third-party escrow services are frequently fake phishing sites.",
    "hurry": "Manufactured pressure to compel rushed payment without due verification.",
    "urgent": "Artificial urgency tactic to bypass careful inspection.",
    "someone else": "Fear-of-missing-out pressure asserting competing buyers.",
    "bhai": "Informal peer pressure common in marketplace negotiations.",
    "google pay": "Off-platform direct UPI / digital wallet transfer with no buyer purchase protection.",
    "tax": "Excuses claiming commercial taxes to dissuade official invoice creation."
}

def extract_highlighted_phrases(text: str, model=None, top_k: int = 8) -> List[Dict[str, Any]]:
    """
    Identifies high-risk phrases in text, calculates their character offsets,
    assigns risk weights, and provides explanatory context for UI rendering.
    """
    if not text:
        return []

    text_lower = text.lower()
    candidate_spans = []

    # 1. Check known high-coefficient phrases and patterns
    for phrase, explanation in RISK_EXPLANATIONS.items():
        pattern = r"\b" + re.escape(phrase) + r"\b"
        for match in re.finditer(pattern, text_lower):
            start, end = match.span()
            matched_text = text[start:end]
            
            # Fetch weight from model if available, else assign default heuristic weight
            weight = 2.5
            if model and hasattr(model, "pos_coef_map"):
                weight = model.pos_coef_map.get(phrase, 2.5)

            candidate_spans.append({
                "phrase": matched_text,
                "start": start,
                "end": end,
                "weight": round(float(weight), 2),
                "reason": explanation
            })

    # 2. Check model's top positive n-grams present in the text if model provided
    if model and hasattr(model, "pos_coef_map"):
        for ngram, weight in model.pos_coef_map.items():
            if len(ngram) >= 4 and ngram in text_lower:
                for match in re.finditer(re.escape(ngram), text_lower):
                    start, end = match.span()
                    # Only add if not already captured
                    if not any(s["start"] == start and s["end"] == end for s in candidate_spans):
                        candidate_spans.append({
                            "phrase": text[start:end],
                            "start": start,
                            "end": end,
                            "weight": round(float(weight), 2),
                            "reason": RISK_EXPLANATIONS.get(ngram, "Model identified this phrase as heavily correlated with marketplace scams.")
                        })

    # 3. Sort by weight descending, filter overlapping spans, take top_k
    candidate_spans.sort(key=lambda x: (x["weight"], -(x["end"] - x["start"])), reverse=True)

    non_overlapping = []
    for span in candidate_spans:
        # Check overlap
        overlaps = False
        for kept in non_overlapping:
            if max(span["start"], kept["start"]) < min(span["end"], kept["end"]):
                overlaps = True
                break
        if not overlaps:
            non_overlapping.append(span)
        if len(non_overlapping) >= top_k:
            break

    # Sort in order of appearance in the text for cleaner UI presentation
    non_overlapping.sort(key=lambda x: x["start"])
    return non_overlapping
