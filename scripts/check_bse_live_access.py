"""Non-bypass diagnostic for the public BSE quote endpoint; saves no price on failure."""
from pathlib import Path
import argparse, json, urllib.request, urllib.error

parser = argparse.ArgumentParser()
parser.add_argument("--scrip", required=True)
args = parser.parse_args()
url = f"https://api.bseindia.com/BseIndiaAPI/api/StockReachGraph/w?scripcode={args.scrip}&flag=0"
try:
    with urllib.request.urlopen(url, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    print(json.dumps({"status": "available", "source": url, "keys": sorted(payload)[:10]}))
except urllib.error.HTTPError as exc:
    print(json.dumps({"status": "unavailable", "source": url, "http_status": exc.code, "reason": "Endpoint denied the ordinary request; no headers, login, or bypass were attempted."}))
except Exception as exc:
    print(json.dumps({"status": "unavailable", "source": url, "reason": str(exc)}))
