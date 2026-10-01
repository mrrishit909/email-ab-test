"""Step 1: download the MineThatData e-mail experiment (Kevin Hillstrom, 2008; 64,000 customers, ~4 MB).

    ./venv/bin/python download.py

The file stays in data/raw/ and is not committed; this script fetches it again.
"""
import urllib.request
from pathlib import Path

URL = "http://www.minethatdata.com/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv"
OUT = Path(__file__).parent / "data" / "raw" / "hillstrom.csv"

if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(URL, OUT)
    rows = sum(1 for _ in OUT.open()) - 1
    assert rows == 64_000, f"expected 64,000 customers, got {rows:,}"
    print(f"{rows:,} customers -> {OUT}")
