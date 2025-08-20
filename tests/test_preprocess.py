from src.cleanhub.preprocess import clean_file
from pathlib import Path

def test_clean_file(tmp_path: Path):
    raw = tmp_path / "raw.txt"
    raw.write_text("ሰላም።   ፩፪ Hello!!\n", encoding="utf-8")
    out = tmp_path / "out.txt"
    n = clean_file(raw, out, normalize_numerals=True)
    assert n == 1
    cleaned = out.read_text(encoding="utf-8").strip()
    assert cleaned == "ሰላም 12 hello"
