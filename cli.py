import argparse
from pathlib import Path
from src.cleanhub.preprocess import batch_clean
from src.cleanhub.model import train_model, evaluate_model, predict_file
from src.cleanhub.io_cloud import maybe_upload, maybe_download
import yaml

def load_config(path: str | None):
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    p = argparse.ArgumentParser(description="Cloud ML Enhancement for Ethiopian text")
    sub = p.add_subparsers(dest="cmd", required=True)

    # preprocess
    sp = sub.add_parser("preprocess", help="Clean raw data to processed/")
    sp.add_argument("--input-glob", default="data/raw/*.txt", help="Glob for raw files")
    sp.add_argument("--outdir", default="data/processed", help="Output dir")
    sp.add_argument("--normalize-numerals", action="store_true")
    sp.add_argument("--config", help="YAML config with cloud settings")

    # train
    st = sub.add_parser("train", help="Train a text classifier")
    st.add_argument("--train-dir", default="data/processed", help="Dir with cleaned .txt grouped by class")
    st.add_argument("--model-out", default="models/model.joblib")
    st.add_argument("--config", help="YAML config with cloud settings")

    # eval
    se = sub.add_parser("eval", help="Evaluate on a processed dir")
    se.add_argument("--eval-dir", default="data/processed", help="Dir with cleaned .txt grouped by class")
    se.add_argument("--model-path", default="models/model.joblib")
    se.add_argument("--config", help="YAML config with cloud settings")

    # predict
    spd = sub.add_parser("predict", help="Predict labels for a text file")
    spd.add_argument("--input-file", required=True)
    spd.add_argument("--model-path", default="models/model.joblib")

    args = p.parse_args()
    cfg = load_config(args.config)

    if args.cmd == "preprocess":
        maybe_download(cfg, what="data")
        n = batch_clean(args.input_glob, args.outdir, normalize_numerals=args.normalize_numerals)
        print(f"[INFO] Cleaned {n} files → {args.outdir}")
        maybe_upload(cfg, local_path=args.outdir, what="data")

    elif args.cmd == "train":
        maybe_download(cfg, what="data")
        model_path = train_model(args.train_dir, args.model_out)
        print(f"[INFO] Trained model saved → {model_path}")
        maybe_upload(cfg, local_path=model_path, what="model")

    elif args.cmd == "eval":
        maybe_download(cfg, what="data")
        metrics = evaluate_model(args.eval_dir, args.model_path)
        print("[INFO] Evaluation:", metrics)

    elif args.cmd == "predict":
        preds = predict_file(args.input_file, args.model_path)
        for i, (text, label, prob) in enumerate(preds, 1):
            print(f"{i:03d} | {label:10s} | {prob:.3f} | {text[:80].replace('\\n',' ')}")

if __name__ == "__main__":
    main()
