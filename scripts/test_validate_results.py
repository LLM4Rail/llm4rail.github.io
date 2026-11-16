"""Tests for validate_results.py. Run: python3 -m unittest discover -s scripts -p 'test_*.py'"""

import copy
import datetime as dt
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_instances  # noqa: E402
import validate_results  # noqa: E402


REPO = Path(__file__).resolve().parents[1]
TODAY = dt.date(2026, 12, 1)
COPY = ["data/instances.json", "data/baselines", "assets/js/i18n.js"]


def good_result(row, primal=None, dual=None, state="improved"):
    """A complete, valid result for `row`, gains computed against the 2026-11-11 baseline."""
    r = dict(row)
    r.update({
        "llm4rail": state,
        "llm4rail_primal": primal,
        "llm4rail_dual": dual,
        "primal_gain": None if primal is None else row["best_known"] - primal,
        "dual_gain": None if dual is None else dual - row["best_bound"],
        "primal_evidence": None if primal is None else "E2",
        "dual_evidence": None if dual is None else "E1",
        "baseline_date": "2026-11-11",
        "result_date": "2026-11-30",
        "model_sha256": "a" * 64,
        "solution_sha256": None if primal is None else "b" * 64,
        "llm": "example-llm 1.0",
        "solver": "Gurobi 13.0",
        "hardware": "2x 64-core CPU, 512 GB",
        "wall_seconds": 9000,
        "tokens": 1200000,
        "skill": "pesp-primal-v1",
        "library_record": "not_submitted",
        "evidence_url": "https://github.com/LLM4Rail/evidence/tree/main/PESPlib/R1L1",
    })
    return r


class ValidateResultsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        for rel in COPY:
            src, dst = REPO / rel, self.tmp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            (shutil.copytree if src.is_dir() else shutil.copy)(src, dst)
        self.data = json.loads((self.tmp / "data/instances.json").read_text(encoding="utf-8"))
        self.rows = {r["instance"]: r for r in self.data["instances"] if r["library"] == "PESPlib"}
        # Label the result states in the copy, as the site will before publishing a result.
        i18n = self.tmp / "assets/js/i18n.js"
        text = i18n.read_text(encoding="utf-8")
        text = text.replace('llm4rail: { pending: "No published result" }',
                            'llm4rail: { pending: "No published result", improved: "Improved", resolved: "Resolved" }')
        text = text.replace('llm4rail: { pending: "尚无公开结果" }',
                            'llm4rail: { pending: "尚无公开结果", improved: "已改进", resolved: "已解决" }')
        i18n.write_text(text, encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def replace(self, row):
        key = (row["library"], row["instance"])
        self.data["instances"] = [row if (r["library"], r["instance"]) == key else r for r in self.data["instances"]]

    def run_validator(self, evidence_root=None, export=True):
        (self.tmp / "data/instances.json").write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")
        if export:
            export_instances.main(self.tmp)
        rep, _ = validate_results.validate(self.tmp, evidence_root, TODAY)
        return rep

    def assertError(self, rep, fragment):
        self.assertTrue(any(fragment in e for e in rep.errors), f"no error containing {fragment!r}: {rep.errors}")

    def test_repository_is_clean(self):
        rep, _ = validate_results.validate(REPO, today=TODAY)
        self.assertEqual(rep.errors, [])

    def test_valid_improvement_passes(self):
        row = self.rows["R1L1"]
        self.replace(good_result(row, primal=row["best_known"] - 1000))
        rep = self.run_validator()
        self.assertEqual(rep.errors, [])

    def test_wrong_gain_is_caught(self):
        row = self.rows["R1L1"]
        r = good_result(row, primal=row["best_known"] - 1000)
        r["primal_gain"] = 999
        self.replace(r)
        self.assertError(self.run_validator(), "primal_gain 999 should be")

    def test_improved_without_gain_is_caught(self):
        row = self.rows["R1L1"]
        self.replace(good_result(row, primal=row["best_known"] + 5))
        self.assertError(self.run_validator(), "no gain over the baseline is positive")

    def test_resolved_needs_equal_bounds_and_strong_evidence(self):
        row = self.rows["R1L1"]
        r = good_result(row, primal=row["best_known"] - 10, dual=row["best_known"] - 20, state="resolved")
        r["dual_evidence"] = "E3"
        self.replace(r)
        rep = self.run_validator()
        self.assertError(rep, "are not equal")
        self.assertError(rep, "not both E1 or E2")

    def test_dual_above_baseline_feasible_value_is_caught(self):
        row = self.rows["R1L1"]
        self.replace(good_result(row, dual=row["best_known"] + 1))
        self.assertError(self.run_validator(), "exceeds the baseline feasible value")

    def test_primal_below_unverified_bound_only_warns(self):
        row = self.rows["R1L1"]  # PESPlib bound is publisher_unverified
        self.replace(good_result(row, primal=row["best_bound"] - 1))
        rep = self.run_validator()
        self.assertEqual(rep.errors, [])
        self.assertTrue(any("unverified" in w for w in rep.warnings))

    def test_pending_with_result_fields_is_caught(self):
        r = dict(self.rows["R1L1"], llm4rail_primal=1)
        self.replace(r)
        self.assertError(self.run_validator(), "pending but result fields are set")

    def test_missing_disclosure_is_caught(self):
        row = self.rows["R1L1"]
        r = good_result(row, primal=row["best_known"] - 1000)
        r["llm"] = ""
        r["tokens"] = None
        r["model_sha256"] = "ABC"
        self.replace(r)
        rep = self.run_validator()
        self.assertError(rep, "llm must be")
        self.assertError(rep, "tokens must be")
        self.assertError(rep, "model_sha256 must be")

    def test_submission_needs_strong_evidence(self):
        row = self.rows["R1L1"]
        r = good_result(row, primal=row["best_known"] - 1000)
        r["primal_evidence"] = "E4"
        r["library_record"] = "submitted"
        self.replace(r)
        self.assertError(self.run_validator(), "only E1 or E2 results can be submitted")

    def test_unknown_baseline_date_is_caught(self):
        row = self.rows["R1L1"]
        r = good_result(row, primal=row["best_known"] - 1000)
        r["baseline_date"] = "2026-11-12"
        self.replace(r)
        self.assertError(self.run_validator(), "no baseline snapshot")

    def test_baseline_gap_mismatch_is_caught(self):
        r = copy.deepcopy(self.rows["R1L1"])
        r["gap"] = 0.5
        self.replace(r)
        self.assertError(self.run_validator(), "gap 0.5 should be")

    def test_missing_i18n_label_is_caught(self):
        row = self.rows["R1L1"]
        self.replace(good_result(row, primal=row["best_known"] - 1000))
        rep = self.run_validator()  # setUp labels improved and resolved, not no_gain
        self.assertEqual(rep.errors, [])
        r = good_result(row, primal=row["best_known"] + 5, state="no_gain")
        self.replace(r)
        self.assertError(self.run_validator(), "has no label for no_gain")

    def test_stale_generated_files_are_caught(self):
        self.run_validator()
        self.data["instances"][0]["record"] = "changed"
        self.assertError(self.run_validator(export=False), "out of date")

    def test_evidence_bundle_hashes(self):
        row = self.rows["R1L1"]
        bundle = self.tmp / "evidence/PESPlib/R1L1"
        bundle.mkdir(parents=True)
        (bundle / "model.pesp").write_bytes(b"model")
        (bundle / "solution.txt").write_bytes(b"solution")
        h = {n: hashlib.sha256((bundle / n).read_bytes()).hexdigest() for n in ("model.pesp", "solution.txt")}
        (bundle / "SHA256SUMS").write_text("".join(f"{d}  {n}\n" for n, d in h.items()), encoding="utf-8")
        r = good_result(row, primal=row["best_known"] - 1000)
        r["model_sha256"], r["solution_sha256"] = h["model.pesp"], h["solution.txt"]
        self.replace(r)
        self.assertEqual(self.run_validator(self.tmp / "evidence").errors, [])
        (bundle / "solution.txt").write_bytes(b"tampered")
        self.assertError(self.run_validator(self.tmp / "evidence"), "sha256 does not match")


if __name__ == "__main__":
    unittest.main()
