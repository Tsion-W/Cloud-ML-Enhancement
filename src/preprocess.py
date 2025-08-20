from __future__ import annotations
import re, glob
from pathlib import Path
from typing import Iterable

# Try to use the portfolio cleaner if installed; otherwise fallback to a tiny local cleaner.
try:
    from ethioclean import EthiopianTextCleaner  # pip install ethioclean (optional)
except Exception:  # fallback
    class EthiopianTextCleaner:
        def __init__(self, lower=True, remove_punctuation=True, normalize_numerals=True):
            self.lower = lower
            self.remove_punctuation = remove_punctuation
            self.normalize_numerals = normalize_numerals
            self.punct = r"[!\"#$%&'()*+,\-./:;<=>?@\[\]^_`{|}~።፣፤፥፦፧፨]"

        def _norm_nums(self, s: str) -> str:
            m = {"፩":"1","፪":"2","፫":"3","፬":"4","፭":"5","፮":"6","፯":"7","፰":"8","፱":"9","፲":"10"}
            for g,a in m.items():
                s = s.replace(g, a)
            return s

        def clean_text(self, s: str) -> str:
            s = re.sub(r"\s+", " ", s).strip()
            if self.remove_punctuation: s = re.sub(self.punct, "", s)
            if self.lower: s = s.lower()
            if self.normalize_numerals: s = self._norm_nums(s)
            return s

        def clean_corpus(self, xs: Iterable[str]) -> list[str]:
            return [self.clean_text(x) for x in xs]

def clean_file(in_path: str | Path, out_path: str | Path, normalize_numerals=True) -> int:
    cleaner = EthiopianTextCleaner(normalize_numerals=normalize_numerals)
    with open(in_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    cleaned = cleaner.clean_corpus(lines)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(cleaned))
    return len(cleaned)

def batch_clean(input_glob: str, outdir: str | Path, normalize_numerals=True) -> int:
    paths = sorted(glob.glob(input_glob))
    total = 0
    for p in paths:
        name = Path(p).stem
        outp = Path(outdir) / f"{name}.txt"
        total += clean_file(p, outp, normalize_numerals=normalize_numerals)
    return len(paths)
