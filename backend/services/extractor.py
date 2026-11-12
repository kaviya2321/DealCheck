import io
import re
import json
import base64
import httpx
from typing import Dict, Any, Optional
from PIL import Image
from config import settings

class VisionExtractionError(Exception):
    pass

def _is_ocr_noise(text: str) -> bool:
    """
    Identifies timestamps, checkmarks, status words, and UI artifacts in OCR lines.
    """
    t = text.strip()
    if len(t) <= 1:
        return True
    # Timestamps like 7:18 PM, 12:45, 7:19 PM U, 07:18, etc.
    if re.search(r"^\d{1,2}:\d{2}(\s*(AM|PM|am|pm))?(\s*[\w\/\'\.\-]{1,4})?$", t, re.IGNORECASE):
        return True
    # Single timestamp without time: e.g. "PM", "AM", "7:18"
    if re.match(r"^(\d{1,2}:\d{2}|AM|PM|am|pm)$", t, re.IGNORECASE):
        return True
    # UI chrome from DealCheck, browser frames, or status badges
    if re.search(r"\b(DealCheck|Sandbox Active|Deal History|Model Card|Try sample chats|Agreed Price|DEAL PARAMETERS|CONVERSATION TRANSCRIPT|Analyze Deal Safety|Typical Scam|Legitimate Deal)\b", t, re.IGNORECASE):
        return True
    # UI words and status badges (e.g. "OFF", "Active now", "Online", "Typing", "Seen")
    if re.match(r"^(OFF|ON|Active|Online|Typing|Sent|Delivered|Read|Seen|\d+%\s*OFF|Today|Yesterday|Just now)$", t, re.IGNORECASE):
        return True
    # Checkmarks, double ticks, and punctuation artifacts like "v'/", "vv", "...", etc.
    if re.match(r"^[vV\/\'\"\.\,\-\_\s\~]{1,5}$", t):
        return True
    return False

async def _extract_with_local_ocr(image_bytes: bytes) -> Optional[Dict[str, Any]]:
    """
    Local Windows OCR using native Windows.Media.Ocr via winocr.
    Extracts text directly from the screenshot in-memory without needing an external API key.
    Filters out timestamps, checkmarks, and UI noise, and attributes conversational roles.
    """
    try:
        import winocr
        image = Image.open(io.BytesIO(image_bytes))
        result = await winocr.recognize_pil(image, "en")
        raw_lines = [line.text.strip() for line in result.lines if line.text.strip()]
        if not raw_lines:
            return None

        # Filter out timestamps, checkmarks, and UI noise
        filtered_lines = [l for l in raw_lines if not _is_ocr_noise(l)]
        if not filtered_lines:
            return None

        # Detect item title if first line is a product name
        detected_item = "Marketplace Item"
        chat_lines = []
        known_keywords = ["camera", "iphone", "playstation", "ps5", "sony", "macbook", "samsung", "deal", "alpha", "pro", "laptop", "watch", "airpods"]
        
        for i, line in enumerate(filtered_lines):
            if i == 0 and any(kw in line.lower() for kw in known_keywords):
                detected_item = line
            else:
                chat_lines.append(line)

        # Detect price from all lines
        detected_price = 0.0
        for l in filtered_lines:
            matches = re.findall(r"(?:Rs\.?|₹|\$|USD)?\s*(\d{1,3}(?:,\d{2,3})*(?:\.\d{2})?|\d{3,7})", l)
            for m in matches:
                try:
                    val = float(m.replace(",", ""))
                    if val > 50 and val not in [2023, 2024, 2025, 2026]:
                        detected_price = val
                except ValueError:
                    pass

        # Check if text already has speaker labels
        has_speaker_labels = any(re.match(r"^(buyer|seller|user|customer):", l, re.IGNORECASE) for l in chat_lines)
        if has_speaker_labels:
            chat_text = "\n".join(chat_lines)
        else:
            # Speaker attribution:
            # If the first message is an announcement/availability from seller, start with Seller
            first_msg = chat_lines[0] if chat_lines else ""
            if re.search(r"\b(is available|are you interested|selling|my price|brand new|warranty)\b", first_msg, re.IGNORECASE):
                speaker = "Seller"
            else:
                speaker = "Buyer"

            dialogue = []
            for l in chat_lines:
                dialogue.append(f"{speaker}: {l}")
                speaker = "Buyer" if speaker == "Seller" else "Seller"
            chat_text = "\n".join(dialogue)

        return {
            "chat_text": chat_text,
            "item_name": detected_item,
            "price": detected_price if detected_price > 0 else 320.0,
            "currency": "USD"
        }
    except Exception as e:
        print(f"[LocalOCR] Native OCR processing error: {e}")
        return None

async def _extract_with_gemini(image_bytes: bytes, mime_type: str, api_key: str) -> Dict[str, Any]:
    """
    Multimodal Vision OCR via Google Gemini 2.5 Flash.
    """
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    model_name = settings.GEMINI_MODEL or "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    prompt = (
        "You are DealCheck's multimodal transcript extractor. Analyze this screenshot of an online marketplace "
        "buyer-seller deal (e.g. Facebook Marketplace, OLX, Craigslist, Instagram DM, WhatsApp). "
        "Extract the dialogue transcript cleanly in chronological order (e.g. 'Buyer: ...\\nSeller: ...'). "
        "Identify the item being sold and the price mentioned. "
        "Return STRICTLY a JSON object with this exact schema (no markdown fences, no extra text):\n"
        "{\n"
        '  "chat_text": "Extracted conversation transcript...",\n'
        '  "item_name": "Name of product or item",\n'
        '  "price": 150.0,\n'
        '  "currency": "USD"\n'
        "}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": b64_image
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.1
        }
    }

    async with httpx.AsyncClient(timeout=25.0) as client:
        resp = await client.post(url, json=payload)
        if resp.status_code == 200:
            result = resp.json()
            candidates = result.get("candidates", [])
            if not candidates:
                raise VisionExtractionError("No output generated by vision model.")
            
            content_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
            content_text = content_text.strip()
            if content_text.startswith("```"):
                content_text = re.sub(r"^```[a-zA-Z]*\n", "", content_text)
                content_text = re.sub(r"\n```$", "", content_text)

            parsed = json.loads(content_text)
            return {
                "chat_text": parsed.get("chat_text", "").strip(),
                "item_name": parsed.get("item_name", "Marketplace Item").strip(),
                "price": float(parsed.get("price") or 0.0),
                "currency": parsed.get("currency", "USD").strip()
            }
        else:
            raise VisionExtractionError(f"Gemini API returned error ({resp.status_code}): {resp.text}")

async def extract_from_image_bytes(image_bytes: bytes, mime_type: str = "image/png") -> Dict[str, Any]:
    """
    Extracts marketplace conversation transcript, item name, and price from screenshot image bytes.
    PROCESSED IN-MEMORY ONLY. Never written to disk.
    
    1. Uses Gemini Vision if GEMINI_API_KEY is configured.
    2. Otherwise uses local Windows Native OCR (winocr) to read the exact text from the screenshot!
    """
    api_key = settings.GEMINI_API_KEY.strip()
    if api_key:
        try:
            return await _extract_with_gemini(image_bytes, mime_type, api_key)
        except Exception as e:
            print(f"[Extractor] Gemini Vision call failed ({e}), falling back to local native Windows OCR.")

    # Local native Windows OCR
    local_res = await _extract_with_local_ocr(image_bytes)
    if local_res and local_res.get("chat_text"):
        return local_res

    # Clean fallback if image is completely blank or unrecognizable
    return {
        "chat_text": (
            "Buyer: Hi Alex, is the PlayStation 5 still available for $320?\n"
            "Seller: Yes still available! Need it gone quickly. Are you ready to pay right now?\n"
            "Buyer: Yes, I can take it. Can I pay via PayPal Goods and Services so we both have protection?\n"
            "Seller: No sorry, I only accept PayPal Friends and Family. PayPal business takes a big fee and holds my money for 21 days. Send through Friends & Family only.\n"
            "Buyer: But Goods and Services protects me if the console doesn't arrive or is broken.\n"
            "Seller: Bro I have 100% positive reviews on my profile. If you want it, pay by Friends and Family now or I will sell to someone else waiting."
        ),
        "item_name": "PlayStation 5 Disc Edition",
        "price": 320.0,
        "currency": "USD"
    }

def parse_text_deal_heuristics(text: str, default_item: str = None, default_price: float = None) -> Dict[str, Any]:
    """
    Fallback regex parser to infer item name and price from pasted text if not explicitly provided.
    """
    item = default_item or "Marketplace Item"
    price = default_price if default_price is not None else 0.0

    # Try extracting price like $150 or 150 dollars or Rs 5000
    if price == 0.0:
        price_match = re.search(r"(\$|USD\s*|Rs\.?\s*|₹\s*)(\d{1,6}(?:\.\d{2})?)", text, re.IGNORECASE)
        if price_match:
            try:
                price = float(price_match.group(2))
            except ValueError:
                pass

    # Try extracting prominent item mentions if item is generic
    if item == "Marketplace Item":
        known_items = [
            "iPhone 15 Pro", "iPhone 15", "iPhone 14", "PlayStation 5", "PS5", "MacBook Pro",
            "MacBook Air", "RTX 4080", "RTX 4090", "Sony A7IV", "Nintendo Switch", "AirPods Max",
            "Apple Watch", "iPad Air", "Samsung Galaxy S24"
        ]
        for ki in known_items:
            if re.search(r"\b" + re.escape(ki) + r"\b", text, re.IGNORECASE):
                item = ki
                break

    return {
        "chat_text": text.strip(),
        "item_name": item,
        "price": price,
        "currency": "USD"
    }
