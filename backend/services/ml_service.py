import os
import sys
import re
import joblib
import json
import httpx
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import settings

# Add ml/ directory to path
ML_DIR = str(settings.ML_DIR)
if ML_DIR not in sys.path:
    sys.path.insert(0, ML_DIR)

from scoring import compute_risk_score, evaluate_rules
from explainability import extract_highlighted_phrases

class MLService:
    def __init__(self):
        self.model_a = None
        self.model_b = None
        self._load_models()

    def _load_models(self):
        model_a_path = settings.MODELS_DIR / "scam_model.joblib"
        model_b_path = settings.MODELS_DIR / "seller_reply_model.joblib"

        if model_a_path.exists():
            try:
                self.model_a = joblib.load(model_a_path)
                print(f"[MLService] Successfully loaded Model A from {model_a_path}")
            except Exception as e:
                print(f"[MLService] Error loading Model A: {e}")
        else:
            print(f"[MLService] Model A file not found at {model_a_path}")

        if model_b_path.exists():
            try:
                self.model_b = joblib.load(model_b_path)
                print(f"[MLService] Successfully loaded Model B from {model_b_path}")
            except Exception as e:
                print(f"[MLService] Error loading Model B: {e}")
        else:
            print(f"[MLService] Model B file not found at {model_b_path}")

    def is_ready(self) -> bool:
        return self.model_a is not None and self.model_b is not None

    def analyze_chat(
        self,
        chat_text: str,
        item_name: str = "Item",
        price: float = 0.0,
        seller_reply_adjustment: int = 0
    ) -> Dict[str, Any]:
        """
        Runs Model A and rule engine. LLM is NEVER used for scoring.
        """
        if not self.model_a:
            raise RuntimeError("Model A (ScamRiskModel) is not loaded. Please run 'python train.py' first.")

        # 1. Model A inference: local TF-IDF + Logistic Regression
        model_prob = float(self.model_a.predict_proba([chat_text])[0])

        # 2. Transparent rule engine + composite score
        scoring_result = compute_risk_score(
            model_probability=model_prob,
            chat_text=chat_text,
            price=price,
            item_name=item_name,
            seller_reply_adjustment=seller_reply_adjustment
        )

        # 3. Model coefficient explainability (highlighted phrases)
        highlights = extract_highlighted_phrases(chat_text, model=self.model_a, top_k=8)

        # 4. Plain-language explanation and polite message
        # Built-in high quality template fallback (immediate, reliable, 100% offline-capable)
        explanation = self._generate_builtin_explanation(scoring_result, highlights, item_name, price)
        drafted_msg = self._generate_builtin_seller_message(item_name, price)

        return {
            "risk_score": scoring_result["final_score"],
            "raw_score": scoring_result["raw_score"],
            "model_probability": scoring_result["model_probability"],
            "model_base_points": scoring_result["model_base_points"],
            "rules_triggered": scoring_result["rules_triggered"],
            "rule_points_total": scoring_result["rule_points_total"],
            "seller_reply_adjustment": scoring_result["seller_reply_adjustment"],
            "verdict": scoring_result["verdict"],
            "verdict_title": scoring_result["verdict_title"],
            "verdict_badge": scoring_result["verdict_badge"],
            "guidance": scoring_result["guidance"],
            "highlighted_phrases": highlights,
            "explanation": explanation,
            "drafted_message": drafted_msg
        }

    def analyze_seller_reply(self, reply_text: str) -> Dict[str, Any]:
        """
        Runs Model B (3-class classifier) on seller reaction.
        """
        if not self.model_b:
            raise RuntimeError("Model B (SellerReplyModel) is not loaded.")
        return self.model_b.analyze(reply_text)

    def detect_deal_agreement(self, text: str) -> bool:
        """
        Detects whether buyer and seller agreed on terms or price in the chat.
        """
        if not text:
            return False
        patterns = [
            r"\b(deal|sounds good|let's do it|i agree|agreed|done deal|that works|works for me)\b",
            r"\b(send (the|a|payment)? link|i'll take it|i will take it|ready to buy|ready to pay)\b",
            r"\b(i can do that|send over the link|send payment info)\b"
        ]
        text_lower = text.lower()
        return any(re.search(p, text_lower) for p in patterns)

    def score_running_chat(
        self,
        new_message: str,
        full_transcript: str,
        sender_role: str,
        item_name: str = "Marketplace Item",
        price: float = 0.0,
        has_paypal_card: bool = False,
        invite_status: str = "JOINED"
    ) -> Dict[str, Any]:
        """
        Scores running conversation for live Deal Room.
        Evaluates cumulative transcript and the latest message.
        If has_paypal_card is True and sender is seller, executes Model B litmus test.
        """
        if not self.model_a:
            raise RuntimeError("Model A (ScamRiskModel) is not loaded.")

        # Combined text for overall context
        combined_text = full_transcript if full_transcript else new_message
        
        # 1. Model A inference on transcript
        prob_transcript = float(self.model_a.predict_proba([combined_text])[0])
        # Also check prob on new message if seller sent it
        prob_msg = float(self.model_a.predict_proba([new_message])[0]) if new_message else 0.0
        model_prob = max(prob_transcript, prob_msg)

        # 2. Model B evaluation if PayPal card was posted and seller replies
        seller_eval = None
        seller_adjustment = 0
        refusal_warning = None

        if has_paypal_card and sender_role == "seller" and self.model_b and new_message:
            seller_eval = self.model_b.analyze(new_message)
            seller_adjustment = seller_eval["risk_delta"]
            if seller_eval["classification"] in ("pushes_friends_and_family", "refuses_protected"):
                refusal_warning = "Walk away: real sellers have no reason to refuse buyer protection."
                seller_adjustment = max(seller_adjustment, 45)

        # 3. Transparent rule engine evaluation
        scoring_result = compute_risk_score(
            model_probability=model_prob,
            chat_text=combined_text,
            price=price,
            item_name=item_name,
            seller_reply_adjustment=seller_adjustment
        )

        # Add invite penalty if seller refused to join
        rules_triggered = list(scoring_result["rules_triggered"])
        if invite_status in ("DECLINED", "REFUSED"):
            rules_triggered.append({
                "id": "seller_refused_invite",
                "name": "Seller Refuses DealCheck Room",
                "points": 25,
                "explanation": "Seller refused to join the secured DealCheck room or insisted on unmonitored chat."
            })
            scoring_result["final_score"] = min(100, scoring_result["final_score"] + 25)

        # If refusal warning was triggered, ensure high risk score (at least 85)
        if refusal_warning:
            scoring_result["final_score"] = max(scoring_result["final_score"], 85)
            scoring_result["verdict"] = "HIGH"
            scoring_result["verdict_title"] = "High Risk — Seller Refused Protection"
            scoring_result["verdict_badge"] = "red"
            scoring_result["guidance"] = refusal_warning

        # 4. Extract highlighted risky phrases (from new message first, then transcript)
        highlights = extract_highlighted_phrases(new_message or combined_text, model=self.model_a, top_k=6)
        if not highlights and combined_text:
            highlights = extract_highlighted_phrases(combined_text, model=self.model_a, top_k=6)

        # 5. Check if polite nudge is needed (F&F or off-platform detected in latest message)
        nudge_required = False
        nudge_text = None
        new_msg_lower = (new_message or "").lower()
        if any(term in new_msg_lower for term in ["friends and family", "friends or family", "f&f", "zelle", "cashapp", "venmo", "crypto", "bitcoin", "gift card", "personal payment"]):
            nudge_required = True
            nudge_text = (
                "DealCheck AI Notice: To maintain full PayPal Buyer Protection, all transactions must use "
                "PayPal Goods & Services. Off-platform transfers (Zelle/Venmo/F&F) waive dispute rights."
            )

        explanation = self._generate_builtin_explanation(scoring_result, highlights, item_name, price)

        return {
            "risk_score": scoring_result["final_score"],
            "model_probability": scoring_result["model_probability"],
            "model_base_points": scoring_result["model_base_points"],
            "rules_triggered": rules_triggered,
            "rule_points_total": sum(r["points"] for r in rules_triggered),
            "seller_reply_adjustment": seller_adjustment,
            "verdict": scoring_result["verdict"],
            "verdict_title": scoring_result["verdict_title"],
            "verdict_badge": scoring_result["verdict_badge"],
            "guidance": scoring_result["guidance"],
            "highlighted_phrases": highlights,
            "explanation": explanation,
            "seller_evaluation": seller_eval,
            "refusal_warning": refusal_warning,
            "nudge_required": nudge_required,
            "nudge_text": nudge_text
        }

    async def ask_dealcheck_ai(self, question: str, deal_context: Dict[str, Any]) -> str:
        """
        Answers buyer questions in the live room. Gemini writes natural advice,
        with a local fallback if Gemini is offline. Gemini NEVER decides the score.
        """
        item_name = deal_context.get("item_name", "Item")
        price = deal_context.get("price", 0.0)
        risk_score = deal_context.get("risk_score", 0)
        verdict = deal_context.get("verdict", "LOW")
        rules = deal_context.get("rules_triggered", [])

        # 1. Try Gemini if configured
        api_key = settings.GEMINI_API_KEY.strip()
        if api_key:
            prompt = (
                f"You are DealCheck AI, a real-time safety advisor protecting a buyer in an online marketplace transaction.\n"
                f"Item: {item_name}, Price: ${price:.2f}\n"
                f"Current DealCheck Risk: {risk_score}/100 ({verdict})\n"
                f"Flags active: {[r.get('name', '') for r in rules]}\n"
                f"Buyer asks: \"{question}\"\n\n"
                f"Give concise (2-3 sentences), highly actionable advice. Always prioritize PayPal Goods & Services. "
                f"Do not invent facts or make up shipping tracking."
            )
            try:
                model_name = settings.GEMINI_MODEL or "gemini-2.5-flash"
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 200}
                }
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        candidates = resp.json().get("candidates", [])
                        if candidates:
                            return candidates[0]["content"]["parts"][0]["text"].strip()
            except Exception as e:
                print(f"[MLService] ask_dealcheck_ai Gemini error: {e}")

        # 2. Local deterministic fallback
        q_lower = question.lower()
        if "friend" in q_lower or "f&f" in q_lower:
            return (
                "Never pay via PayPal Friends & Family for purchases. It is meant only for personal gifts "
                "between trusted acquaintances and completely waives PayPal Buyer Protection. Always insist on Goods & Services."
            )
        elif "zelle" in q_lower or "venmo" in q_lower or "cashapp" in q_lower or "crypto" in q_lower:
            return (
                "Paying outside PayPal (via Zelle, Cash App, Venmo, or Crypto) removes all transaction security. "
                "If the seller refuses the protected PayPal checkout link, cancel the deal immediately."
            )
        elif "deposit" in q_lower or "advance" in q_lower or "hold" in q_lower:
            return (
                "Do not send deposits or holding fees before official checkout or inspection. Legitimate marketplace "
                "transactions should be paid in full through a single protected checkout."
            )
        elif "safe" in q_lower or "legit" in q_lower:
            return (
                f"DealCheck calculates this deal at {risk_score}/100 ({verdict} risk). "
                f"As long as you checkout through the official PayPal Goods & Services card generated in this room, "
                f"your money is covered by PayPal's 180-day buyer protection."
            )
        else:
            return (
                f"For the {item_name} (${price:.2f}), ensure you complete payment exclusively through the PayPal "
                f"Goods & Services link generated in this room. That guarantees protection if the item is not as described or never arrives."
            )

    async def polish_explanation_with_llm(
        self,
        chat_text: str,
        scoring_result: Dict[str, Any],
        item_name: str,
        price: float
    ) -> Optional[str]:
        """
        Optional: Uses Gemini ONLY to rephrase the explanation in natural language.
        Does NOT alter or calculate the risk score.
        """
        api_key = settings.GEMINI_API_KEY.strip()
        if not api_key:
            return None

        prompt = (
            f"You are DealCheck's buyer advocate. Summarize the transaction risks in 2 concise sentences.\n"
            f"Item: {item_name}, Price: ${price:.2f}\n"
            f"DealCheck Score: {scoring_result['final_score']}/100 ({scoring_result['verdict']})\n"
            f"Flags triggered: {[r['name'] for r in scoring_result['rules_triggered']]}\n"
            f"Chat snippet: {chat_text[:300]}\n"
            "Explain in clear, reassuring terms why the buyer must insist on PayPal Goods & Services or beware."
        )

        try:
            model_name = settings.GEMINI_MODEL or "gemini-2.5-flash"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 200}
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        return candidates[0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            print(f"[MLService] Gemini polish skipped: {e}")
        return None

    def _generate_builtin_explanation(
        self,
        scoring: Dict[str, Any],
        highlights: List[Dict[str, Any]],
        item_name: str,
        price: float
    ) -> str:
        score = scoring["final_score"]
        rules = scoring["rules_triggered"]
        
        if score >= 70:
            reasons = "; ".join([r["name"] for r in rules]) if rules else "high statistical anomaly in negotiation text"
            return (
                f"High-risk scam indicators detected ({score}/100). The seller exhibits classic fraud vectors "
                f"including: {reasons}. Under no circumstances send payments via PayPal Friends & Family or wire, "
                f"as these waive all PayPal Buyer Protection."
            )
        elif score >= 40:
            reasons = "; ".join([r["name"] for r in rules]) if rules else "unverified seller negotiation patterns"
            return (
                f"Moderate transaction risk ({score}/100). Certain patterns ({reasons}) warrant precaution. "
                f"Protect your purchase of '{item_name}' (${price:.2f}) by sending a PayPal Goods & Services link "
                f"and observing the seller's response."
            )
        else:
            return (
                f"Low risk ({score}/100). The negotiation appears standard and consistent with legitimate marketplace sales. "
                f"To keep full PayPal Buyer Protection intact, complete the deal using PayPal Goods & Services."
            )

    def _generate_builtin_seller_message(self, item_name: str, price: float) -> str:
        formatted_price = f"${price:.2f}" if price > 0 else "the agreed price"
        return (
            f"Hi! I'm ready to finalize purchasing the {item_name} for {formatted_price}. "
            f"For both of our security and to protect against shipping loss or fraudulent claims, "
            f"I only send payments via PayPal Goods & Services. "
            f"I have set up the official PayPal checkout link here: {{PAYPAL_LINK}}. "
            f"Once you confirm, PayPal will notify you and I will share my shipping address. Thanks!"
        )

ml_service = MLService()
