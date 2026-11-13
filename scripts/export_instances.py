import csv
import json
from pathlib import Path


root = Path(__file__).resolve().parents[1]
data = json.loads((root / "data/instances.json").read_text(encoding="utf-8"))
rows = data["instances"]

with (root / "data/instances.csv").open("w", encoding="utf-8", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

(root / "assets/js/data.js").write_text(
    "window.LLM4RAIL_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n",
    encoding="utf-8",
)
