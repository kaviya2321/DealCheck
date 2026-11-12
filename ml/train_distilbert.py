"""
Optional DistilBERT Fine-Tuning Script for DealCheck (Model A Transformer alternative)
Runs strictly when a CUDA GPU is available AND invoked with the --gpu flag.
Default application uses the high-efficiency, explainable calibrated Model A.
"""

import sys
import os
import argparse
import pandas as pd

def check_gpu():
    try:
        import torch
        if not torch.cuda.is_available():
            return False, "No CUDA GPU detected on system."
        device_name = torch.cuda.get_device_name(0)
        return True, f"CUDA GPU available: {device_name}"
    except ImportError:
        return False, "PyTorch is not installed with CUDA support."

def main():
    parser = argparse.ArgumentParser(description="DealCheck DistilBERT Fine-Tuning")
    parser.add_argument("--gpu", action="store_true", help="Explicitly enable GPU execution")
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    args = parser.parse_args()

    print("=========================================================")
    print("DealCheck: Optional DistilBERT Transformer Fine-Tuner")
    print("=========================================================")

    if not args.gpu:
        print("[Notice] Flag --gpu not provided.")
        print("To run DistilBERT fine-tuning, you must pass --gpu.")
        print("Default DealCheck runtime uses Model A (TF-IDF + Calibrated Logistic Regression)")
        print("for sub-10ms latency, zero GPU requirements, and direct token-level explainability.")
        sys.exit(0)

    gpu_available, reason = check_gpu()
    if not gpu_available:
        print(f"[Requirement Not Met] {reason}")
        print("DistilBERT fine-tuning is disabled on non-GPU environments.")
        print("DealCheck will continue using the high-performance Model A.")
        sys.exit(0)

    print(f"[OK] {reason}")
    print("[DistilBERT] Preparing Hugging Face Trainer with distilbert-base-uncased...")

    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
        from datasets import Dataset

        data_path = os.path.join(os.path.dirname(__file__), "data", "synthetic_marketplace_chats.csv")
        if not os.path.exists(data_path):
            print(f"[!] Training data file not found at {data_path}")
            sys.exit(1)

        df = pd.read_csv(data_path)[["text", "label"]].dropna()
        dataset = Dataset.from_pandas(df)
        train_test = dataset.train_test_split(test_size=0.2, seed=42)

        model_name = "distilbert-base-uncased"
        tokenizer = AutoTokenizer.from_pretrained(model_name)

        def tokenize(batch):
            return tokenizer(batch["text"], padding="max_length", truncation=True, max_length=256)

        tokenized = train_test.map(tokenize, batched=True)
        model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

        training_args = TrainingArguments(
            output_dir="./ml/distilbert_checkpoints",
            learning_rate=2e-5,
            per_device_train_batch_size=args.batch_size,
            per_device_eval_batch_size=args.batch_size,
            num_train_epochs=args.epochs,
            weight_decay=0.01,
            evaluation_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            fp16=True
        )

        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized["train"],
            eval_dataset=tokenized["test"],
            tokenizer=tokenizer
        )

        print("[DistilBERT] Initiating fine-tuning epochs...")
        trainer.train()

        out_path = "./ml/models/distilbert_scam_model"
        model.save_pretrained(out_path)
        tokenizer.save_pretrained(out_path)
        print(f"[DistilBERT] Successfully fine-tuned and saved model to {out_path}")

    except Exception as e:
        print(f"[!] Error during DistilBERT execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
