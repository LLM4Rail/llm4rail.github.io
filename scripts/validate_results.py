"""Validate data/instances.json: the public baseline and every LLM4Rail result.

Usage:
    python3 scripts/validate_results.py                      # check the repository
    python3 scripts/validate_results.py --evidence-root DIR  # also check evidence bundles
    python3 scripts/validate_results.py --strict             # warnings fail too

Exit code 0 = no errors, 1 = errors (or warnings under --strict).

All catalogue problems are minimisation problems: a feasible value is an upper bound
(best_known, llm4rail_primal) and a bound is a lower bound (best_bound, llm4rail_dual).

Result rules (see the LLM4Rail plan, section "验证与结果发布规范"):
  * llm4rail = pending   -> no result fields set.
  * llm4rail != pending  -> disclosure fields, hashes, evidence grades and dates set;
                            primal_gain / dual_gain equal the gain over the frozen
                            baseline snapshot data/baselines/<baseline_date>.json.
  * improved             -> at least one positive gain.
  * no_gain              -> no positive gain.
  * resolved             -> primal == dual, both graded E1 or E2.
  * library_record submitted / listed -> the claimed side is graded E1 or E2.
"""

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_instances  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]

BASE_FIELDS = [
    "instance", "library", "set", "n1", "n2", "size_kind", "best_known", "best_bound", "gap",
    "status", "record", "source", "llm4rail", "upper_evidence", "bound_record", "bound_source",
    "bound_evidence", "family",
]
RESULT_FIELDS = [
    "llm4rail_primal", "llm4rail_dual", "primal_gain", "dual_gain", "primal_evidence",
    "dual_evidence", "baseline_date", "result_date", "model_sha256", "solution_sha256", "llm",
    "solver", "hardware", "wall_seconds", "tokens", "skill", "library_record", "evidence_url",
]
LIBRARIES = {"PESPlib", "TimPassLib", "DISPLIB", "MIPLIB 2017"}
SIZE_KINDS = {"ev_act", "tr_op", "var_con"}
STATUSES = {"open", "optimal", "no_bound"}
RESULT_STATES = {"pending", "improved", "resolved", "no_gain"}
GRADES = {"E1", "E2", "E3", "E4"}
STRONG_GRADES = {"E1", "E2"}
LIBRARY_RECORD = {"not_submitted", "submitted", "listed"}
# A baseline bound with this evidence is not proven; beating it is news, not a contradiction.
UNPROVEN_BOUNDS = {"publisher_unverified"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
EVIDENCE_HOME = "https://github.com/LLM4Rail/"
GAP_TOL = 5e-6  # gap is stored rounded to six decimals


def close(a, b, rel=1e-9, abs_=1e-6):
    return math.isclose(a, b, rel_tol=rel, abs_tol=abs_)


def is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def parse_date(value):
    try:
        return dt.date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, where, message):
        self.errors.append(f"{where}: {message}")

    def warn(self, where, message):
        self.warnings.append(f"{where}: {message}")


def i18n_keys(text, block):
    """Keys of a flat `block: { ... }` object, once per language, from assets/js/i18n.js."""
    found = []
    for body in re.findall(r"\b" + re.escape(block) + r"\s*:\s*\{([^{}]*)\}", text):
        found.append(set(re.findall(r"""(?:^|[,{\s])["']?([\w-]+)["']?\s*:""", body)))
    return found


def check_baseline_row(r, where, rep):
    missing = [field for field in BASE_FIELDS if field not in r]
    if missing:
        rep.error(where, f"missing fields: {', '.join(missing)}")
        return
    if r["library"] not in LIBRARIES:
        rep.error(where, f"unknown library {r['library']!r}")
    if r["size_kind"] not in SIZE_KINDS:
        rep.error(where, f"unknown size_kind {r['size_kind']!r}")
    if r["status"] not in STATUSES:
        rep.error(where, f"unknown status {r['status']!r}")
    for field in ("n1", "n2"):
        if not (isinstance(r[field], int) and r[field] > 0):
            rep.error(where, f"{field} must be a positive integer")
    bk, bb = r["best_known"], r["best_bound"]
    if not (is_number(bk) and is_number(bb)):
        rep.error(where, "best_known and best_bound must be finite numbers")
        return
    if bb > bk:
        rep.error(where, f"best_bound {bb} exceeds best_known {bk}")
    gap = 0.0 if bk == bb else (bk - bb) / abs(bk)
    if not (is_number(r["gap"]) and abs(r["gap"] - gap) <= GAP_TOL):
        rep.error(where, f"gap {r['gap']} should be {gap:.6f}")
    if (r["status"] == "optimal") != (bk == bb):
        rep.error(where, f"status {r['status']!r} does not match best_known {bk} / best_bound {bb}")
    for field in ("source", "bound_source"):
        if not str(r[field]).startswith("https://"):
            rep.error(where, f"{field} must be an https URL")


def check_result(r, where, base, rep, today):
    state = r.get("llm4rail")
    present = [f for f in RESULT_FIELDS if r.get(f) is not None]
    if state == "pending":
        if present:
            rep.error(where, f"llm4rail is pending but result fields are set: {', '.join(present)}")
        return

    primal, dual = r.get("llm4rail_primal"), r.get("llm4rail_dual")
    if primal is None and dual is None:
        rep.error(where, "a result needs llm4rail_primal or llm4rail_dual")
        return
    for name, value in (("llm4rail_primal", primal), ("llm4rail_dual", dual)):
        if value is not None and not is_number(value):
            rep.error(where, f"{name} must be a finite number")
            return
    if primal is not None and dual is not None and dual > primal and not close(dual, primal):
        rep.error(where, f"llm4rail_dual {dual} exceeds llm4rail_primal {primal}")

    # Disclosure, provenance, dates.
    for field in ("llm", "solver", "hardware", "skill"):
        if not (isinstance(r.get(field), str) and r[field].strip()):
            rep.error(where, f"{field} must be a non-empty string (use \"none\" for no skill)")
    if not (is_number(r.get("wall_seconds")) and r["wall_seconds"] > 0):
        rep.error(where, "wall_seconds must be a positive number")
    if not (isinstance(r.get("tokens"), int) and not isinstance(r["tokens"], bool) and r["tokens"] >= 0):
        rep.error(where, "tokens must be a non-negative integer")
    if not SHA256.match(str(r.get("model_sha256"))):
        rep.error(where, "model_sha256 must be 64 lowercase hex characters")
    if primal is not None and not SHA256.match(str(r.get("solution_sha256"))):
        rep.error(where, "solution_sha256 must be 64 lowercase hex characters when a primal value is claimed")
    url = r.get("evidence_url")
    if not (isinstance(url, str) and url.startswith("https://")):
        rep.error(where, "evidence_url must be an https URL")
    elif not url.startswith(EVIDENCE_HOME):
        rep.warn(where, f"evidence_url is outside {EVIDENCE_HOME}")
    if r.get("library_record") not in LIBRARY_RECORD:
        rep.error(where, f"library_record must be one of {sorted(LIBRARY_RECORD)}")

    baseline_date, result_date = parse_date(r.get("baseline_date")), parse_date(r.get("result_date"))
    if result_date is None:
        rep.error(where, "result_date must be an ISO date (YYYY-MM-DD)")
    elif result_date > today:
        rep.error(where, f"result_date {result_date} is in the future")
    if baseline_date is None:
        rep.error(where, "baseline_date must be an ISO date (YYYY-MM-DD)")
    elif result_date is not None and result_date < baseline_date:
        rep.error(where, "result_date is earlier than baseline_date")

    # Evidence grades.
    grades = {}
    for side, value in (("primal", primal), ("dual", dual)):
        grade = r.get(side + "_evidence")
        if value is None:
            if grade is not None:
                rep.error(where, f"{side}_evidence is set but llm4rail_{side} is not")
            continue
        if grade not in GRADES:
            rep.error(where, f"{side}_evidence must be one of {sorted(GRADES)}")
        grades[side] = grade

    # Gains against the frozen baseline.
    gains = {}
    snapshot = base.get(r.get("baseline_date"))
    if baseline_date is not None and snapshot is None:
        rep.error(where, f"no baseline snapshot data/baselines/{r.get('baseline_date')}.json")
    key = (r["library"], r["instance"])
    if snapshot is not None:
        ref = snapshot.get(key)
        if ref is None:
            rep.error(where, f"instance missing from baseline {r['baseline_date']}")
        else:
            if primal is not None:
                gains["primal"] = ref["best_known"] - primal
                if primal < ref["best_bound"] and not close(primal, ref["best_bound"]):
                    msg = f"llm4rail_primal {primal} is below the baseline lower bound {ref['best_bound']}"
                    if r["bound_evidence"] in UNPROVEN_BOUNDS:
                        rep.warn(where, msg + " (the baseline bound is unverified: check before claiming)")
                    else:
                        rep.error(where, msg)
            if dual is not None:
                gains["dual"] = dual - ref["best_bound"]
                if dual > ref["best_known"] and not close(dual, ref["best_known"]):
                    rep.error(where, f"llm4rail_dual {dual} exceeds the baseline feasible value {ref['best_known']}")
            for side in ("primal", "dual"):
                stored = r.get(side + "_gain")
                if side not in gains:
                    if stored is not None:
                        rep.error(where, f"{side}_gain is set but llm4rail_{side} is not")
                elif not (is_number(stored) and close(stored, gains[side])):
                    rep.error(where, f"{side}_gain {stored} should be {gains[side]!r}")

    # State rules.
    improved = any(g > 0 and not close(g, 0.0) for g in gains.values())
    if state == "improved" and gains and not improved:
        rep.error(where, "llm4rail is improved but no gain over the baseline is positive")
    if state == "no_gain" and improved:
        rep.error(where, "llm4rail is no_gain but a gain over the baseline is positive")
    if state == "resolved":
        if primal is None or dual is None or not close(primal, dual):
            rep.error(where, "llm4rail is resolved but llm4rail_primal and llm4rail_dual are not equal")
        if not (grades.get("primal") in STRONG_GRADES and grades.get("dual") in STRONG_GRADES):
            rep.error(where, "llm4rail is resolved but primal and dual evidence are not both E1 or E2")
        if not improved and snapshot is not None:
            rep.warn(where, "resolved without improving either baseline bound")
    if r.get("library_record") in {"submitted", "listed"} and not (set(grades.values()) & STRONG_GRADES):
        rep.error(where, "only E1 or E2 results can be submitted to a library")
    weak = sorted(s for s, g in grades.items() if g in {"E3", "E4"})
    if weak and state in {"improved", "resolved"}:
        rep.warn(where, f"{' and '.join(weak)} evidence is E3/E4: publish it labelled, not counted as a record")


def check_evidence_bundle(r, where, evidence_root, rep):
    bundle = evidence_root / r["library"].replace(" ", "-") / r["instance"]
    sums = bundle / "SHA256SUMS"
    if not sums.is_file():
        rep.error(where, f"missing {sums}")
        return
    listed = set()
    for n, line in enumerate(sums.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        m = re.match(r"^([0-9a-f]{64}) [ *](.+)$", line)
        if not m:
            rep.error(where, f"{sums}:{n}: not a sha256sum line")
            continue
        digest, name = m.groups()
        path = (bundle / name).resolve()
        if bundle.resolve() not in path.parents:
            rep.error(where, f"{sums}:{n}: {name} points outside the bundle")
            continue
        if not path.is_file():
            rep.error(where, f"{sums}:{n}: {name} is missing")
            continue
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        if h.hexdigest() != digest:
            rep.error(where, f"{name}: sha256 does not match SHA256SUMS")
        listed.add(digest)
    for field in ("model_sha256", "solution_sha256"):
        if r.get(field) and r[field] not in listed:
            rep.error(where, f"{field} is not listed in {sums}")


def load_baselines(root, rep):
    snapshots = {}
    for path in sorted((root / "data/baselines").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        date = data.get("meta", {}).get("baseline_date")
        if date != path.stem:
            rep.error(str(path.relative_to(root)), f"meta.baseline_date {date!r} does not match the file name")
        snapshots[path.stem] = {(r["library"], r["instance"]): r for r in data["instances"]}
    return snapshots


def validate(root=ROOT, evidence_root=None, today=None):
    rep = Report()
    today = today or dt.date.today()
    data = json.loads((root / "data/instances.json").read_text(encoding="utf-8"))
    rows = data["instances"]
    baselines = load_baselines(root, rep)

    seen = set()
    for i, r in enumerate(rows):
        where = f"{r.get('library', '?')}/{r.get('instance', f'#{i}')}"
        key = (r.get("library"), r.get("instance"))
        if key in seen:
            rep.error(where, "duplicate library + instance")
        seen.add(key)
        unknown = set(r) - set(BASE_FIELDS) - set(RESULT_FIELDS)
        if unknown:
            rep.error(where, f"unknown fields: {', '.join(sorted(unknown))}")
        n_errors = len(rep.errors)
        check_baseline_row(r, where, rep)
        if len(rep.errors) > n_errors:
            continue
        if r["llm4rail"] not in RESULT_STATES:
            rep.error(where, f"llm4rail must be one of {sorted(RESULT_STATES)}")
            continue
        check_result(r, where, baselines, rep, today)
        if evidence_root is not None and r["llm4rail"] != "pending":
            check_evidence_bundle(r, where, evidence_root, rep)

    # Every coded value shown on the site needs an English and a Chinese label.
    i18n_text = (root / "assets/js/i18n.js").read_text(encoding="utf-8")
    used = {
        "set": {r.get("set") for r in rows},
        "status": {r.get("status") for r in rows},
        "llm4rail": {r.get("llm4rail") for r in rows},
        "evidence": {r.get("upper_evidence") for r in rows} | {r.get("bound_evidence") for r in rows},
    }
    for block, values in used.items():
        per_lang = i18n_keys(i18n_text, block)
        if len(per_lang) != 2:
            rep.error("assets/js/i18n.js", f"expected an en and a zh `{block}` block, found {len(per_lang)}")
            continue
        for lang, keys in zip(("en", "zh"), per_lang):
            missing = sorted(v for v in values - keys if v is not None)
            if missing:
                rep.error("assets/js/i18n.js", f"{lang}.{block} has no label for {', '.join(missing)}")

    # Generated files must match instances.json (run scripts/export_instances.py).
    expected = {
        "data/instances.csv": export_instances.render_csv(rows),
        "assets/js/data.js": export_instances.render_js(data),
    }
    for rel, text in expected.items():
        path = root / rel
        actual = path.read_bytes().decode("utf-8") if path.is_file() else None
        if actual != text:
            rep.error(rel, "out of date: run python3 scripts/export_instances.py")

    return rep, rows


def summary(rows):
    counts = {}
    for r in rows:
        counts[r.get("llm4rail")] = counts.get(r.get("llm4rail"), 0) + 1
    return ", ".join(f"{k} {v}" for k, v in sorted(counts.items(), key=lambda kv: str(kv[0])))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root (default: this repository)")
    parser.add_argument("--evidence-root", type=Path, help="local checkout of the evidence bundles")
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = parser.parse_args(argv)

    rep, rows = validate(args.root.resolve(), args.evidence_root)
    for line in rep.errors:
        print("ERROR  " + line)
    for line in rep.warnings:
        print("WARN   " + line)
    print(f"{len(rows)} instances ({summary(rows)}): {len(rep.errors)} errors, {len(rep.warnings)} warnings")
    failed = rep.errors or (args.strict and rep.warnings)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
