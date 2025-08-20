from pathlib import Path
from src.cleanhub.model import train_model, evaluate_model
from src.cleanhub.preprocess import clean_file

def test_train_eval(tmp_path: Path):
    # Create processed dataset: two classes with 2 samples each
    pos = tmp_path / "pos"; pos.mkdir(parents=True, exist_ok=True)
    neg = tmp_path / "neg"; neg.mkdir(parents=True, exist_ok=True)
    (pos/"a.txt").write_text("ጥሩ ነው\ngood\n", encoding="utf-8")
    (pos/"b.txt").write_text("ፍቅር ነው\nlove\n", encoding="utf-8")
    (neg/"a.txt").write_text("መጥፎ ነው\nbad\n", encoding="utf-8")
    (neg/"b.txt").write_text("ጥርስ ህመም\npain\n", encoding="utf-8")

    model_path = tmp_path / "m.joblib"
    train_model(tmp_path, model_path)
    metrics = evaluate_model(tmp_path, model_path)
    assert "accuracy" in metrics
