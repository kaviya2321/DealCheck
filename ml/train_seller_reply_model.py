"""
Model B Training Script for DealCheck: SellerReplyModel
3-Class Classifier for Seller Behavioral Litmus Test:
- Class 0: 'accepts_protected' (Agreeing to PayPal Goods & Services)
- Class 1: 'refuses_protected' (Refusing online/protected payment, e.g. cash only)
- Class 2: 'pushes_friends_and_family' (Pushes back specifically demanding F&F / fee evasion)

Trained on >= 700 synthetic samples per class (2,100+ total) with TF-IDF + Logistic Regression.
"""

import os
import sys
import random
import joblib
import pandas as pd
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from model_classes import SellerReplyModel

random.seed(42)

MODELS_DIR = os.path.join(BASE_DIR, "models")
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_OUT_PATH = os.path.join(MODELS_DIR, "seller_reply_model.joblib")
DATA_OUT_PATH = os.path.join(DATA_DIR, "seller_replies_dataset.csv")

LABEL_MAP = {
    0: "accepts_protected",
    1: "refuses_protected",
    2: "pushes_friends_and_family"
}

ACCEPTS_TEMPLATES = [
    "Sure, send the PayPal link and I'll confirm receipt.",
    "Yes, PayPal Goods and Services works for me.",
    "That sounds great, I'm happy to use G&S protection.",
    "Sure thing, please send the invoice or checkout link.",
    "No problem at all, I'll ship with tracking once paid.",
    "Yeah that's totally fine, buyer protection is important.",
    "Works for me. Send the link across!",
    "I accept PayPal G&S, go ahead and send the payment.",
    "Goods & Services is good with me, I will pack it right now.",
    "Approved! Send me the official link and I'll get it ready for dispatch.",
    "Sounds fair. Send the checkout link and I will prepare the package.",
    "I'm completely fine with Goods and Services. Send it over.",
    "That's safe for both of us. Please share the payment link.",
    "Theek hai bhai, PayPal invoice bhej do main check kar leta hoon.",
    "Chalega, Goods and Services kar do, tracking de dunga kal.",
    "Yes perfect, as soon as the PayPal G&S confirmation arrives I will post it.",
    "Sure, I understand safety concerns. Send the payment link whenever you're ready.",
    "Fine by me! As long as PayPal verifies the address, I'll ship today.",
    "Okay, let's do it via PayPal Goods. Drop the link here.",
    "Got it. Send the PayPal checkout link and I'll notify you once cleared."
]

REFUSES_TEMPLATES = [
    "No PayPal. Cash only.",
    "I don't use PayPal or any online apps.",
    "Cash in person only. No online payments.",
    "I don't accept Goods & Services.",
    "Pick up and cash only, take it or leave it.",
    "I do not do payment links, strictly cash at exchange.",
    "Sorry, had too many issues with PayPal chargebacks, cash only.",
    "No online transfers. Cash when we meet in person.",
    "I don't do online checkout. Cash upon collection only.",
    "Cash only on pickup mate, no digital payments.",
    "Not interested in PayPal. If you can't pay cash in person, no deal.",
    "Strictly local pickup with cash. No shipping, no links.",
    "I don't have PayPal configured. Cash only please.",
    "No, in-person cash only. Too many scams online.",
    "Nahi bhai online payment nahi chalega, cash only aake le jao.",
    "Sirf cash chahiye, no PayPal or wallets. Milne par pay karo.",
    "I decline PayPal. Bank deposit or physical cash only.",
    "No cards or online links. Physical cash only upon meetup.",
    "I only do face to face cash deals.",
    "No PayPal, cash only when we meet at the mall."
]

PUSHES_FF_TEMPLATES = [
    "No, send it as Friends and Family so we avoid fees.",
    "Only F&F otherwise PayPal takes a 3.5% cut and holds my money for 21 days.",
    "I won't accept Goods and Services, send through Friends & Family.",
    "Send via F&F or the deal is off.",
    "Please select 'Sending to a friend / Friends and Family', not paying for goods.",
    "F&F only bro, I am selling as an individual and don't want business tax deductions.",
    "Don't send as G&S, send personal transfer so no fees apply.",
    "Select friends and family option on PayPal or I will refund immediately.",
    "Why send as goods? Just choose family and friends, I have high ratings.",
    "I only take payment as Friends and Family. Business payments get locked.",
    "Friends & Family only please. Otherwise the fee comes out of my pocket.",
    "No Goods & Services. Send as friend or find another seller.",
    "Use F and F option on PayPal so neither of us pays unnecessary fees.",
    "Bhai Friends and Family se hi bhejna, business mat karna tax katega.",
    "Sirf F&F chalega, 21 days hold nahi chahiye mujhe.",
    "Make sure you tick Friends & Family when sending, not Goods.",
    "F&F only! I don't do Goods and Services.",
    "Send it through PayPal friends option otherwise I cancel.",
    "Only friends and family transfer accepted. I'm shipping right after.",
    "F&F or no deal. I'm not giving 4% to PayPal."
]

VARIATIONS = [
    "", " thanks", " bro", " buddy", " please", " ok?", "!", "...",
    " Let me know.", " Thanks.", " Cool."
]

def generate_seller_dataset(samples_per_class=750):
    rows = []
    
    # Class 0: Accepts
    for _ in range(samples_per_class):
        base = random.choice(ACCEPTS_TEMPLATES)
        var = random.choice(VARIATIONS)
        text = (base + var).strip()
        rows.append({"text": text, "label": 0, "class_name": LABEL_MAP[0]})

    # Class 1: Refuses
    for _ in range(samples_per_class):
        base = random.choice(REFUSES_TEMPLATES)
        var = random.choice(VARIATIONS)
        text = (base + var).strip()
        rows.append({"text": text, "label": 1, "class_name": LABEL_MAP[1]})

    # Class 2: Pushes F&F
    for _ in range(samples_per_class):
        base = random.choice(PUSHES_FF_TEMPLATES)
        var = random.choice(VARIATIONS)
        text = (base + var).strip()
        rows.append({"text": text, "label": 2, "class_name": LABEL_MAP[2]})

    random.shuffle(rows)
    df = pd.DataFrame(rows)
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(DATA_OUT_PATH, index=False)
    print(f"[Model B Dataset] Generated {len(df):,} synthetic seller replies -> {DATA_OUT_PATH}")
    return df

def train():
    df = generate_seller_dataset(750)
    X = df["text"].tolist()
    y = df["label"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    print("\n[Model B] Training TF-IDF + Logistic Regression (Multi-class)...")
    word_vec = TfidfVectorizer(ngram_range=(1, 3), max_features=8000, sublinear_tf=True)
    char_vec = TfidfVectorizer(ngram_range=(3, 5), analyzer="char", max_features=8000, sublinear_tf=True)
    union = FeatureUnion([("word", word_vec), ("char", char_vec)])

    clf = LogisticRegression(
        C=2.0,
        max_iter=1000,
        class_weight="balanced",
        solver="lbfgs",
        random_state=42
    )

    pipeline = Pipeline([
        ("union", union),
        ("clf", clf)
    ])

    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    print("\n[Model B Test Performance]:")
    print(classification_report(y_test, y_pred, target_names=[LABEL_MAP[i] for i in range(3)]))

    wrapped_model = SellerReplyModel(pipeline, LABEL_MAP)

    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(wrapped_model, MODEL_OUT_PATH)
    print(f"\n[Model B] Model successfully saved to {MODEL_OUT_PATH}")
    return wrapped_model

if __name__ == "__main__":
    train()
