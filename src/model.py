from __future__ import annotations
from pathlib import Path
import glob
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import classification_report, accuracy_score

def _load_processed_dir(processed_dir: str | Path) -> pd.DataFrame:
    """
    Expects cleaned .txt files placed into class-named subfolders, e.g.:
      data/processed/pos/*.txt
      data/processed/neg/*.txt
    Each .txt may contain multiple lines (treated as separate samples).
    """
    rows = []
    for class_dir in Path(processed_dir).glob("*"):
        if not class_dir.is_dir(): continue
        label = class_dir.name
        for fp in glob.glob(str(class_dir / "*.txt")):
            with open(fp, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        rows.append({"text": line, "label": label})
    if not rows:
        raise ValueError(f"No samples found under {processed_dir}. "
                         f"Place cleaned text under class folders (e.g., processed/pos, processed/neg).")
    return pd.DataFrame(rows)

def _make_pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1,2), min_df=2, token_pattern=r"(?u)\b\w+\b")),
        ("clf", SGDClassifier(loss="log_loss", max_iter=2000, n_jobs=-1, random_state=42))
    ])

def train_model(processed_dir: str | Path, model_out: str | Path) -> str:
    df = _load_processed_dir(processed_dir)
    X, y = df["text"].tolist(), df["label"].tolist()
    pipe = _make_pipeline()
    pipe.fit(X, y)
    Path(model_out).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, model_out)
    return str(model_out)

def evaluate_model(processed_dir: str | Path, model_path: str | Path) -> dict:
    df = _load_processed_dir(processed_dir)
    X, y = df["text"].tolist(), df["label"].tolist()
    pipe: Pipeline = joblib.load(model_path)
    yhat = pipe.predict(X)
    acc = accuracy_score(y, yhat)
    report = classification_report(y, yhat, output_dict=True)
    return {"accuracy": acc, "report": report}

def predict_file(input_file: str | Path, model_path: str | Path) -> list[tuple[str,str,float]]:
    pipe: Pipeline = joblib.load(model_path)
    texts = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s: texts.append(s)
    if not texts:
        return []
    proba = pipe.predict_proba(texts)
    labels = pipe.classes_
    out = []
    preds = pipe.predict(texts)
    for t, pred, p in zip(texts, preds, proba.max(axis=1)):
        out.append((t, pred, float(p)))
    return out
