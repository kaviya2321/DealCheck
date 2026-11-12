"""
Model A Training Script for DealCheck: ScamRiskModel
Architecture:
- Feature Extraction: FeatureUnion of Word TF-IDF (1-3 ngrams) and Character TF-IDF (3-5 ngrams)
- Classifier: Logistic Regression with class weighting
- Calibration: CalibratedClassifierCV with Platt scaling (sigmoid)
- Explainability: Preserves feature names and linear coefficients for token/phrase risk attribution.
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from model_classes import ScamRiskModel
from sklearn.pipeline import FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV

DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")
PUBLIC_DATA_PATH = os.path.join(DATA_DIR, "public_datasets.csv")
SYNTHETIC_DATA_PATH = os.path.join(DATA_DIR, "synthetic_marketplace_chats.csv")
MODEL_OUT_PATH = os.path.join(MODELS_DIR, "scam_model.joblib")

def load_training_data():
    dfs = []
    if os.path.exists(PUBLIC_DATA_PATH):
        df_pub = pd.read_csv(PUBLIC_DATA_PATH)
        print(f"[Model A] Loaded {len(df_pub):,} records from public datasets.")
        dfs.append(df_pub[["text", "label"]])
    else:
        print("[!] Public dataset file missing. Please run download_data.py first.")

    if os.path.exists(SYNTHETIC_DATA_PATH):
        df_syn = pd.read_csv(SYNTHETIC_DATA_PATH)
        print(f"[Model A] Loaded {len(df_syn):,} records from synthetic marketplace chats.")
        dfs.append(df_syn[["text", "label"]])
    else:
        print("[!] Synthetic dataset file missing. Please run generate_marketplace_data.py first.")

    if not dfs:
        raise RuntimeError("No training data found in ml/data/")

    full_df = pd.concat(dfs, ignore_index=True).dropna(subset=["text", "label"])
    full_df["text"] = full_df["text"].astype(str)
    full_df["label"] = full_df["label"].astype(int)
    full_df = full_df[full_df["text"].str.strip().str.len() > 10].drop_duplicates(subset=["text"])
    print(f"[Model A] Total deduplicated training dataset: {len(full_df):,} samples.")
    print(f"         Class distribution: Scam (1) = {sum(full_df['label'] == 1):,}, Legit (0) = {sum(full_df['label'] == 0):,}")
    return full_df

def train():
    df = load_training_data()
    X = df["text"].tolist()
    y = df["label"].values

    print("\n[Model A] Building Feature Extraction Pipeline...")
    word_vec = TfidfVectorizer(
        ngram_range=(1, 3),
        max_features=25000,
        sublinear_tf=True,
        min_df=2,
        token_pattern=r"(?u)\b\w+\b"
    )
    char_vec = TfidfVectorizer(
        ngram_range=(3, 5),
        analyzer="char",
        max_features=25000,
        sublinear_tf=True,
        min_df=3
    )
    union = FeatureUnion([
        ("word", word_vec),
        ("char", char_vec)
    ])

    print("[Model A] Fitting vectorizer on text corpora...")
    X_trans = union.fit_transform(X)
    print(f"          Feature space dimensionality: {X_trans.shape[1]:,} features.")

    print("[Model A] Fitting Base Logistic Regression...")
    base_lr = LogisticRegression(
        C=2.5,
        max_iter=1000,
        class_weight="balanced",
        solver="lbfgs",
        random_state=42
    )
    base_lr.fit(X_trans, y)

    print("[Model A] Calibrating probabilities via 5-Fold Stratified Platt Scaling (sigmoid)...")
    calibrated_clf = CalibratedClassifierCV(
        estimator=base_lr,
        method="sigmoid",
        cv=5
    )
    calibrated_clf.fit(X_trans, y)

    model = ScamRiskModel(
        vectorizer=union,
        base_estimator=base_lr,
        calibrated_clf=calibrated_clf
    )

    # Quick test inference
    test_cases = [
        "Pay me via PayPal Friends and Family to avoid fees. No Goods and Services.",
        "Sure, we can meet tomorrow at the police station lobby. You can inspect the phone before paying."
    ]
    test_probs = model.predict_proba(test_cases)
    print("\n[Model A] Sanity Check:")
    print(f"  Scam chat prob:  {test_probs[0]:.4f} (Expected high > 0.75)")
    print(f"  Legit chat prob: {test_probs[1]:.4f} (Expected low < 0.25)")

    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(model, MODEL_OUT_PATH)
    print(f"\n[Model A] Model successfully saved to {MODEL_OUT_PATH}")
    return model

if __name__ == "__main__":
    train()
