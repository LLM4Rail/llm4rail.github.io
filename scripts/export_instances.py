import csv
import io
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def fieldnames(rows):
    """All keys in first-seen order, so rows that carry result fields can follow pending rows."""
    names = {}
    for row in rows:
        names.update(dict.fromkeys(row))
    return list(names)


def render_csv(rows):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames(rows))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def render_js(data):
    return "window.LLM4RAIL_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n"


def main(root=ROOT):
    data = json.loads((root / "data/instances.json").read_text(encoding="utf-8"))
    (root / "data/instances.csv").write_text(render_csv(data["instances"]), encoding="utf-8", newline="")
    (root / "assets/js/data.js").write_text(render_js(data), encoding="utf-8")


if __name__ == "__main__":
    main()
