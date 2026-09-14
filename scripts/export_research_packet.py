"""Export a deterministic JSON packet for a future API, UI, or citation-aware RAG layer."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from project_runner import run_registered_company
from research_packet import build_research_packet

parser = argparse.ArgumentParser(description="Export a source-backed research packet without invoking AI.")
parser.add_argument("--company", default="infosys")
parser.add_argument("--output", help="Output JSON path; defaults to data/processed/<company>_research_packet.json")
args = parser.parse_args()

run = run_registered_company(ROOT, args.company)
output = Path(args.output) if args.output else ROOT / "data/processed" / f"{args.company}_research_packet.json"
output.parent.mkdir(parents=True, exist_ok=True)
packet = build_research_packet(run)
output.write_text(json.dumps(packet, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
print(f"Exported source-backed research packet to {output}")
