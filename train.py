"""
DealCheck Master Training Pipeline Runner
Usage:
    python train.py
Or:
    make train
"""

import sys
import subprocess
import os

def run_step(desc, cmd):
    print(f"\n{'='*60}")
    print(f">> {desc}")
    print(f"{'='*60}")
    res = subprocess.run([sys.executable] + cmd, check=True)
    if res.returncode != 0:
        print(f"[ERROR] Step failed: {desc}")
        sys.exit(res.returncode)

def main():
    print("=========================================================")
    print("DealCheck: Full End-to-End Model Training Pipeline")
    print("=========================================================")

    # Step 1: Download & normalize public datasets
    run_step("Step 1/5: Downloading & Normalizing Public Scam Datasets", ["ml/data/download_data.py"])

    # Step 2: Generate domain-specific synthetic marketplace chats
    run_step("Step 2/5: Synthesizing Marketplace Domain Conversations", ["ml/data/generate_marketplace_data.py"])

    # Step 3: Train Model A (ScamRiskModel)
    run_step("Step 3/5: Training Model A (ScamRiskModel - TF-IDF + Logistic Regression)", ["ml/train_scam_model.py"])

    # Step 4: Train Model B (SellerReplyModel)
    run_step("Step 4/5: Training Model B (SellerReplyModel - 3-Class Litmus Classifier)", ["ml/train_seller_reply_model.py"])

    # Step 5: Evaluate all models and generate metrics.json and MODEL_CARD.md
    run_step("Step 5/5: Evaluating Models on Holdout & Handwritten Datasets", ["ml/evaluate.py"])

    print("\n" + "="*60)
    print("DealCheck Training Pipeline Completed Successfully!")
    print("Artifacts generated:")
    print("  - ml/models/scam_model.joblib")
    print("  - ml/models/seller_reply_model.joblib")
    print("  - ml/reports/metrics.json")
    print("  - ml/MODEL_CARD.md")
    print("  - ml/data/DATA_SOURCES.md")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
