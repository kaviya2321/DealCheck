# DealCheck: Dataset Registry & Provenance (`DATA_SOURCES.md`)

This document records the exact data sources, licenses, processing logic, and synthetic data generation used to train and evaluate DealCheck's machine learning models.

---

## 1. Public Training Datasets

All public datasets were acquired from the Hugging Face Hub using the `datasets` library and normalized to a uniform schema:
`text (str)` and `label (int)` where `1 = Scam / Risky`, `0 = Legitimate`.

| Dataset Name | Status | Rows Included | Scam Count | Legit Count | License | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FredZhang7/all-scam-spam` | **SUCCESS** | 8,000 | 4,000 | 4,000 | MIT / Open-Access Research Dataset | Normalized to (text, label) where 1=scam/risky, 0=legitimate. |
| `BothBosu/Scammer-Conversation` | **SUCCESS** | 758 | 318 | 440 | CC-BY-4.0 | Normalized to (text, label) where 1=scam/risky, 0=legitimate. |
| `Shade63/scam-classification-multiclass` | **FAILED (DataFilesNotFoundError)** | 0 | 0 | 0 | Apache-2.0 | Download failed: No task.toml or instruction.md files found. Execution continued with other datasets. |

**Total Public Dataset Records:** 8,758

---

## 2. Synthetic Marketplace Domain Dataset (SYNTHETIC)

- **Identifier**: `ml/data/synthetic_marketplace_chats.csv`
- **Classification**: **SYNTHETIC**
- **Generator**: `ml/data/generate_marketplace_data.py`
- **Volume**: $\ge 2,200$ multi-turn buyer-seller marketplace conversation transcripts.
- **License**: MIT / Proprietary to DealCheck project.
- **Domain Coverage**:
  - Platforms modeled: Facebook Marketplace, OLX India, Instagram DMs, Craigslist, OfferUp.
  - Scam vectors represented (Label = 1):
    - Coercion to pay via **PayPal Friends & Family** ("F&F", "family and friends", "personal payment") to evade fees.
    - False fee-avoidance claims ("PayPal business fees take 4%, please choose friends option").
    - Redirection to non-protected payment rails (Google Pay, PhonePe, Zelle, Crypto, Wire, Apple Gift Cards).
    - Fabricated urgency ("Have 4 buyers offering cash today", "Need advance within 30 mins").
    - Advance deposit before viewing / delivery ("Send 50% booking deposit now").
    - Fake courier / escrow stories ("FedEx courier will collect cash from you, just pay insurance fee").
    - Hinglish / Indian English colloquialisms ("Bhai send advance", "Google Pay kar do", "courier dispatch ho jayega").
  - Legitimate marketplace negotiations (Label = 0):
    - Price bargaining with reasonable counter-offers.
    - Insisting on in-person meeting in public locations (police station, mall, metro station).
    - Product inspection, serial number verification, invoice requests.
    - Explicit agreement to use **PayPal Goods & Services** with buyer protection.
- **Rationale**: Public spam/phishing corpora lean heavily toward email or SMS formats. This domain-specific synthetic generation fills the distribution gap for real-time buyer-seller chat dynamics.

---

## 3. Hand-Written Holdout Test Dataset

- **Identifier**: `ml/data/handwritten_test.csv`
- **Classification**: **MANUAL / HAND-WRITTEN HOLDOUT**
- **Volume**: 30 realistic buyer-seller conversations (15 scam, 15 legit).
- **Strict Isolation**: Excluded from both training and validation splits. Kept exclusively for objective holdout evaluation reported in `MODEL_CARD.md`.
