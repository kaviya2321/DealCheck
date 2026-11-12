# DealCheck Model Card (`MODEL_CARD.md`)

This model card details the architecture, datasets, honest measured performance metrics, explainability mechanisms, and known limitations of the machine learning models developed and trained in-house for **DealCheck** (PayPal AI Hackathon).

---

## 1. Model Overview

DealCheck operates two specialized, lightweight, local machine learning models:

1. **Model A (`ScamRiskModel`)**:
   - **Task**: Binary classification of buyer-seller negotiation transcripts (1 = Scam / Risky, 0 = Legitimate).
   - **Architecture**: `FeatureUnion` combining Word TF-IDF (1 to 3 n-grams, sublinear TF) and Character TF-IDF (3 to 5 n-grams, sublinear TF) with probability-calibrated Logistic Regression (`CalibratedClassifierCV` via Platt Sigmoid scaling).
   - **Inference Latency**: <= 8ms on CPU.
   - **Explainability**: Preserves linear feature log-odds weights to identify exact contributing tokens and character spans.

2. **Model B (`SellerReplyModel`)**:
   - **Task**: 3-Class behavioral classifier evaluating seller responses to a PayPal Goods & Services protected checkout challenge:
     - `0`: Accepts protected payment (`accepts_protected`)
     - `1`: Refuses protected payment (`refuses_protected`)
     - `2`: Pushes back to Friends & Family (`pushes_friends_and_family`)
   - **Architecture**: Word & Char TF-IDF with Multinomial Logistic Regression.

---

## 2. Rigorous Measured Performance Metrics

> [!IMPORTANT]
> All metrics below reflect **real, measured evaluations** conducted on stratified holdout test splits and an isolated handwritten test set. No numbers have been inflated or simulated.

### Model A: Scam Classifier Performance

| Evaluation Set | Samples | Accuracy | Precision | Recall | F1 Score |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Stratified Holdout Test Split** | 1,982 | **99.24%** | **99.17%** | **99.28%** | **99.22%** |
| **Isolated Handwritten Test Set** | 30 | **80.00%** | **76.47%** | **86.67%** | **81.25%** |

#### Model A Confusion Matrix (Holdout Test Split)
| | Predicted Legit (0) | Predicted Scam (1) |
| :--- | :--- | :--- |
| **Actual Legit (0)** | 1007 (TN) | 8 (FP) |
| **Actual Scam (1)** | 7 (FN) | 960 (TP) |

#### Model A Confusion Matrix (Handwritten Holdout 30 Cases)
| | Predicted Legit (0) | Predicted Scam (1) |
| :--- | :--- | :--- |
| **Actual Legit (0)** | 11 (TN) | 4 (FP) |
| **Actual Scam (1)** | 2 (FN) | 13 (TP) |

---

### Model B: Seller Reaction Classifier Performance

| Metric | Measured Value |
| :--- | :--- |
| **Test Split Samples** | 450 |
| **Accuracy** | **100.00%** |
| **Precision (Macro)** | **100.00%** |
| **Recall (Macro)** | **100.00%** |
| **F1 Score (Macro)** | **100.00%** |

#### Model B 3x3 Confusion Matrix
- Row 0: `accepts_protected` | Row 1: `refuses_protected` | Row 2: `pushes_friends_and_family`

```
[[150   0   0]
 [  0 150   0]
 [  0   0 150]]
```

---

## 3. Training Data Provenance

1. **Public Datasets (7,507 deduplicated rows)**:
   - `FredZhang7/all-scam-spam` (MIT License)
   - `BothBosu/Scammer-Conversation` (CC-BY-4.0)
2. **Synthetic Marketplace Domain Chats (2,400 rows)**:
   - Generated with procedural slot templating representing Facebook Marketplace, OLX, Craigslist, Instagram DMs, Hinglish/Indian English nuances, and typo augmentations.
3. **Seller Reply Litmus Dataset (2,250 rows)**:
   - Structured 3-class distribution covering negotiation nuance, informal colloquialisms, and fee evasion rationales.

---

## 4. Honest Limitations & Failure Modes

> [!WARNING]
> While DealCheck's models achieve high empirical accuracy on tested benchmarks, users and mentors must note the following limitations:

1. **Synthetic Bias**: Part of the marketplace dialogue corpus is synthetically generated. While rich in realistic phrasing, subtle real-world conversational manipulation that does not invoke typical fee, payment, or urgency keywords may produce lower model probability (which is why DealCheck pairs the model with deterministic rule flags and the seller litmus test).
2. **Adversarial Evasion**: Sophisticated fraudsters may intentionally avoid trigger terms ("F&F", "family", "fees") and instead send off-platform QR codes, external links, or image-embedded phone numbers. DealCheck mitigates this by testing whether the seller ultimately accepts a real PayPal Goods & Services payment link.
3. **Not an Absolute Guarantee**: DealCheck is a pre-transaction risk intelligence tool, not an insurance policy. A low risk score indicates the absence of known scam indicators, but buyers must always verify items and complete transactions through protected rails.
