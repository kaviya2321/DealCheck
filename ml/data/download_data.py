"""
Data Ingestion Script for DealCheck
Downloads public scam/fraud datasets from Hugging Face Hub,
normalizes them to (text, label) where 1=scam/risky and 0=legitimate,
and writes DATA_SOURCES.md with sources, licenses, and row counts.
"""

import os
import sys
import pandas as pd
from datasets import load_dataset

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(DATA_DIR, "public_datasets.csv")
SOURCES_MD = os.path.join(DATA_DIR, "DATA_SOURCES.md")

SOURCES = [
    {
        "name": "FredZhang7/all-scam-spam",
        "type": "Hugging Face Hub",
        "license": "MIT / Open-Access Research Dataset",
        "description": "Comprehensive scam, fraud and spam text dataset.",
        "text_col": "text",
        "label_col": "is_spam",
        "mapping": lambda x: 1 if int(x) == 1 else 0
    },
    {
        "name": "BothBosu/Scammer-Conversation",
        "type": "Hugging Face Hub",
        "license": "CC-BY-4.0",
        "description": "Multi-turn dialogues between scammers and potential victims with labeled interactions.",
        "text_col": "conversation",
        "label_col": "label",
        "mapping": lambda x: 1 if int(x) == 1 else 0
    },
    {
        "name": "Shade63/scam-classification-multiclass",
        "type": "Hugging Face Hub",
        "license": "Apache-2.0",
        "description": "Multiclass scam text classifications.",
        "text_col": "text",
        "label_col": "label",
        "mapping": lambda x: 1 if x != 0 and str(x).lower() != "legit" else 0
    }
]

def download_and_normalize():
    all_dfs = []
    report_entries = []

    print("[DealCheck Data Ingestion] Starting download of public datasets...")

    for src in SOURCES:
        name = src["name"]
        print(f"\n--> Fetching {name}...")
        try:
            ds = load_dataset(name, split="train")
            df = pd.DataFrame(ds)
            print(f"    Raw records: {len(df):,}")
            
            text_col = src["text_col"]
            label_col = src["label_col"]

            if text_col not in df.columns or label_col not in df.columns:
                raise ValueError(f"Expected columns ({text_col}, {label_col}) not found. Available: {list(df.columns)}")

            cleaned = pd.DataFrame()
            cleaned["text"] = df[text_col].astype(str).str.strip()
            cleaned["label"] = df[label_col].apply(src["mapping"]).astype(int)
            cleaned["source"] = name

            # Drop empty texts or duplicates
            cleaned = cleaned[cleaned["text"].str.len() > 10].drop_duplicates(subset=["text"])
            
            # Subsample large datasets if needed to keep training responsive and balanced
            # FredZhang7 has 42k, we can take up to 8,000 balanced rows to maintain speed and high quality
            if len(cleaned) > 8000:
                scam_sub = cleaned[cleaned["label"] == 1].sample(n=min(4000, sum(cleaned["label"] == 1)), random_state=42)
                legit_sub = cleaned[cleaned["label"] == 0].sample(n=min(4000, sum(cleaned["label"] == 0)), random_state=42)
                cleaned = pd.concat([scam_sub, legit_sub]).sample(frac=1.0, random_state=42)

            scam_cnt = int((cleaned["label"] == 1).sum())
            legit_cnt = int((cleaned["label"] == 0).sum())
            print(f"    Normalized: {len(cleaned):,} rows (Scam: {scam_cnt:,}, Legit: {legit_cnt:,})")

            all_dfs.append(cleaned)
            report_entries.append({
                "name": name,
                "status": "SUCCESS",
                "rows": len(cleaned),
                "scam_rows": scam_cnt,
                "legit_rows": legit_cnt,
                "license": src["license"],
                "description": src["description"],
                "notes": "Normalized to (text, label) where 1=scam/risky, 0=legitimate."
            })
        except Exception as e:
            print(f"    [!] Failed to download/process {name}: {e}")
            report_entries.append({
                "name": name,
                "status": f"FAILED ({type(e).__name__})",
                "rows": 0,
                "scam_rows": 0,
                "legit_rows": 0,
                "license": src["license"],
                "description": src["description"],
                "notes": f"Download failed: {str(e)[:180]}. Execution continued with other datasets."
            })

    if not all_dfs:
        raise RuntimeError("No public datasets could be downloaded.")

    combined = pd.concat(all_dfs, ignore_index=True)
    combined.to_csv(OUTPUT_FILE, index=False)
    print(f"\n[DealCheck Data Ingestion] Saved {len(combined):,} combined public records to {OUTPUT_FILE}")

    # Generate DATA_SOURCES.md
    generate_data_sources_md(report_entries, len(combined))
    return combined

def generate_data_sources_md(report_entries, total_public_rows):
    content = f"""# DealCheck: Dataset Registry & Provenance (`DATA_SOURCES.md`)

This document records the exact data sources, licenses, processing logic, and synthetic data generation used to train and evaluate DealCheck's machine learning models.

---

## 1. Public Training Datasets

All public datasets were acquired from the Hugging Face Hub using the `datasets` library and normalized to a uniform schema:
`text (str)` and `label (int)` where `1 = Scam / Risky`, `0 = Legitimate`.

| Dataset Name | Status | Rows Included | Scam Count | Legit Count | License | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for entry in report_entries:
        content += f"| `{entry['name']}` | **{entry['status']}** | {entry['rows']:,} | {entry['scam_rows']:,} | {entry['legit_rows']:,} | {entry['license']} | {entry['notes']} |\n"

    content += f"""
**Total Public Dataset Records:** {total_public_rows:,}

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
"""

    with open(SOURCES_MD, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[DealCheck Data Ingestion] Updated {SOURCES_MD}")

if __name__ == "__main__":
    download_and_normalize()
