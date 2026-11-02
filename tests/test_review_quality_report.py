"""未実行・見逃し・誤指摘・必須確認不足を品質成功にしないことを確認します。"""

import copy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "tools/review_quality_report.py"
SPEC = importlib.util.spec_from_file_location("review_quality", SCRIPT)
quality = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(quality)


class QualityTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.source = self.root / "assessment.json"

    def ref(self, name, text):
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return {"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def measured(self):
        cases = []
        for key, kind, expected, verdict in (("defect", "defect", ["D1", "D2"], "REQUEST_CHANGES"),
                                             ("clean", "clean", [], "APPROVE"),
                                             ("hold", "hold", [], "DEFER")):
            cases.append({"id": key, "kind": kind, "expected_defects": expected,
                "expected_verdict": verdict, "required_checks": ["purpose", "rules", "counterevidence", "consultation"],
                "oracle": self.ref(key + "-oracle.txt", "事前に独立評価者が固定した期待値と原本参照")})
        data = {"schema_version": 1, "cases": cases}
        for side in ("baseline", "candidate"):
            runs = []
            for case in cases:
                for repeat in range(1, 4):
                    tag = f"{side}-{case['id']}-{repeat}"
                    runs.append({"case_id": case["id"], "repeat": repeat, "status": "EXECUTED",
                        "assessor": "independent-human", "assessment_origin": "independent",
                        "conditions": {key: hashlib.sha256(key.encode()).hexdigest()
                                       if key in {"task_snapshot", "prompt_sha256"} else "fixed-" + key
                                       for key in quality.CONTROLS},
                        "evidence": {key: self.ref(tag + "-" + key + ".txt", tag + " " + key)
                                     for key in ("trace", "output", "assessment")},
                        "detected_defects": case["expected_defects"].copy(),
                        "false_positive_ids": [], "scope_error_ids": [],
                        "checks": dict.fromkeys(case["required_checks"], "COMPLETE"),
                        "verdict": case["expected_verdict"]})
            data[side] = {"configuration": side + "-snapshot", "runs": runs}
        return data

    def report(self, data):
        return quality.assess(data, self.root)[0]

    def costs(self, data, candidate_tokens=90, candidate_seconds=110):
        for side in ("baseline", "candidate"):
            for run in data[side]["runs"]:
                participants = ["parent", "adviser"] + (["acceptance"] if side == "candidate" else [])
                total = 100 if side == "baseline" else candidate_tokens
                since = datetime(2026, 11, 2, tzinfo=timezone.utc) + timedelta(minutes=5 * run["repeat"])
                until = since + timedelta(seconds=120 if side == "baseline" else candidate_seconds)
                sources = {name: {"status": "AVAILABLE", "tokens": {
                    "input_tokens": 1, "output_tokens": 0, "total_tokens": 1}} for name in participants}
                sources["parent"]["tokens"] = {"input_tokens": total-len(participants)+1,
                                               "output_tokens": 0, "total_tokens": total-len(participants)+1}
                usage = {"sources": sources, "combined_tokens": {"total_tokens": total},
                    "window": {"since": since.isoformat(), "until": until.isoformat()},
                    "receipt_id": f"{side}-{run['case_id']}-{run['repeat']}"}
                name = f"{side}-{run['case_id']}-{run['repeat']}-usage.json"
                run["evidence"]["usage"] = self.ref(name, json.dumps(usage))
                run["participants"] = participants
                run["cost_accounting_reviewed"] = True
        return data

    def test_matched_repeated_defect_clean_and_hold_cases_pass_only_observed_scope(self):
        data = self.measured()
        result = self.report(data)
        self.assertEqual("NO_OBSERVED_REGRESSION", result["status"])
        self.assertEqual(9, len(result["paired_results"]))
        self.assertFalse(result["gaps"])
        self.assertNotIn("quality_guaranteed", result)
        self.assertEqual("INCONCLUSIVE", result["benefit"]["status"])

    def test_additional_layer_needs_quality_and_whole_run_benefit(self):
        data = self.costs(self.measured())
        result = self.report(data)
        self.assertEqual("BENEFIT_OBSERVED", result["benefit"]["status"])
        self.assertEqual(270, result["benefit"]["comparisons"][0]["candidate"]["total_tokens"])
        data["candidate"]["runs"][0]["detected_defects"] = ["D1"]
        self.assertEqual("REJECTED", self.report(data)["benefit"]["status"])
        for tokens, seconds in ((101, 110), (90, 121), (100, 110)):
            data = self.costs(self.measured(), tokens, seconds)
            self.assertEqual("NOT_BENEFICIAL", self.report(data)["benefit"]["status"])

    def test_missing_parent_partial_usage_and_unreviewed_cost_never_qualify(self):
        original = self.costs(self.measured())
        for change in ({"participants": ["adviser", "acceptance"]},
                       {"cost_accounting_reviewed": False}):
            data = copy.deepcopy(original)
            data["candidate"]["runs"][0].update(change)
            self.assertEqual("INCONCLUSIVE", self.report(data)["benefit"]["status"])
        run = original["candidate"]["runs"][0]
        path = self.root / run["evidence"]["usage"]["path"]
        value = json.loads(path.read_text())
        value["sources"]["acceptance"]["status"] = "PARTIAL"
        run["evidence"]["usage"] = self.ref(path.name, json.dumps(value))
        self.assertEqual("INCONCLUSIVE", self.report(original)["benefit"]["status"])

    def test_invalid_totals_period_or_reused_usage_do_not_prove_benefit(self):
        for kind in ("total", "period", "duplicate", "hash"):
            data = self.costs(self.measured())
            run = data["candidate"]["runs"][0]
            path = self.root / run["evidence"]["usage"]["path"]
            usage = json.loads(path.read_text())
            if kind == "total":
                usage["combined_tokens"]["total_tokens"] = 1
            elif kind == "period":
                usage["window"]["since"] = "2026-11-02T00:05:00"
            elif kind == "duplicate":
                data["candidate"]["runs"][1]["evidence"]["usage"] = run["evidence"]["usage"].copy()
            elif kind == "hash":
                run["evidence"]["usage"]["sha256"] = "0" * 64
            if kind in ("total", "period"):
                run["evidence"]["usage"] = self.ref(path.name, json.dumps(usage))
            self.assertEqual("INCONCLUSIVE", self.report(data)["benefit"]["status"])

    def test_require_benefit_exit_status_includes_parent_and_added_layer(self):
        for tokens, expected in ((90, 0), (101, 5)):
            data = self.costs(self.measured(), candidate_tokens=tokens)
            self.source.write_text(json.dumps(data))
            result = subprocess.run([sys.executable, "-I", "-B", str(SCRIPT), str(self.source),
                "--out", str(self.root / "benefit.json"), "--require-benefit"], capture_output=True, text=True)
            self.assertEqual(expected, result.returncode, result.stderr)

    def test_aggregate_cost_cannot_hide_expensive_outlier_behind_median(self):
        data = self.costs(self.measured())
        run = data["candidate"]["runs"][0]
        path = self.root / run["evidence"]["usage"]["path"]
        value = json.loads(path.read_text())
        value["sources"]["parent"]["tokens"] = {"input_tokens": 998, "output_tokens": 0, "total_tokens": 998}
        value["combined_tokens"]["total_tokens"] = 1000
        run["evidence"]["usage"] = self.ref(path.name, json.dumps(value))
        result = self.report(data)
        self.assertEqual("NOT_BENEFICIAL", result["benefit"]["status"])
        self.assertEqual(90, result["benefit"]["comparisons"][0]["candidate"]["median_tokens"])

    def test_miss_false_positive_scope_drift_false_approval_and_missing_check_fail(self):
        original = self.measured()
        changes = ({"detected_defects": ["D1"]}, {"false_positive_ids": ["FP1"]},
                   {"scope_error_ids": ["SCOPE1"]}, {"verdict": "APPROVE"},
                   {"checks": {"purpose": "COMPLETE", "consultation": "PENDING"}})
        for change in changes:
            with self.subTest(change=change):
                data = copy.deepcopy(original)
                data["candidate"]["runs"][0].update(change)
                data["candidate"]["tokens"] = 1
                self.assertEqual("FAIL", self.report(data)["status"])
        data = copy.deepcopy(original)
        data["candidate"]["runs"][0]["detected_defects"] = ["D1"]
        row = self.report(data)["paired_results"][0]
        self.assertEqual(["D2"], row["lost_detections"])
        self.assertEqual(["D2"], row["missed_defects"])

    def test_missing_runs_assessment_conditions_or_evidence_never_pass(self):
        original = self.measured()
        for change in ({"status": "NOT_RUN"}, {"status": "PARTIAL"}, {"assessor": ""},
                       {"assessment_origin": "self"}, {"false_positive_ids": None},
                       {"evidence": {}}, {"conditions": {}}):
            with self.subTest(change=change):
                data = copy.deepcopy(original)
                data["candidate"]["runs"][0].update(change)
                self.assertEqual("INCONCLUSIVE", self.report(data)["status"])
        for key in quality.CONTROLS:
            data = copy.deepcopy(original)
            data["candidate"]["runs"][0]["conditions"][key] = "changed"
            self.assertEqual("INCONCLUSIVE", self.report(data)["status"])
        path = self.root / original["candidate"]["runs"][0]["evidence"]["trace"]["path"]
        path.write_text("changed after assessment")
        self.assertEqual("INCONCLUSIVE", self.report(original)["status"])

    def test_insufficient_pairs_missing_controls_and_duplicate_trials_are_not_samples(self):
        data = self.measured()
        data["candidate"]["runs"].pop()
        self.assertEqual("INCONCLUSIVE", self.report(data)["status"])
        data["candidate"]["runs"] = []
        self.assertEqual("INCONCLUSIVE", self.report(data)["status"])
        data = self.measured()
        data["baseline"]["runs"].append(data["baseline"]["runs"][0])
        with self.assertRaises(ValueError):
            self.report(data)
        data = self.measured()
        data["cases"] = [data["cases"][0]]
        for side in ("baseline", "candidate"):
            data[side]["runs"] = [r for r in data[side]["runs"] if r["case_id"] == "defect"]
        self.assertEqual("INCONCLUSIVE", self.report(data)["status"])

    def test_reused_run_log_and_changed_repeat_conditions_cannot_inflate_comparison(self):
        data = self.measured()
        runs = data["candidate"]["runs"]
        runs[1]["evidence"]["trace"] = runs[0]["evidence"]["trace"]
        self.assertEqual("INCONCLUSIVE", self.report(data)["status"])
        data = self.measured()
        for side in ("baseline", "candidate"):
            data[side]["runs"][1]["conditions"]["model"] = "different-model"
        self.assertEqual("INCONCLUSIVE", self.report(data)["status"])
        data = self.measured()
        data["candidate"]["runs"][6]["verdict"] = "APPROVE"
        self.assertEqual("FAIL", self.report(data)["status"])

    def test_cli_protects_assessment_and_evidence_and_reports_unknown_not_success(self):
        data = self.costs(self.measured())
        self.source.write_text(json.dumps(data))
        alias = self.root / "alias.json"
        alias.hardlink_to(self.source)
        output = self.root / data["cases"][0]["oracle"]["path"]
        usage = self.root / data["candidate"]["runs"][0]["evidence"]["usage"]["path"]
        for path in (self.source, alias, output, usage):
            before = path.read_bytes()
            result = subprocess.run([sys.executable, "-I", "-B", str(SCRIPT), str(self.source),
                                     "--out", str(path)], capture_output=True, text=True)
            self.assertEqual(2, result.returncode, result.stderr)
            self.assertEqual(before, path.read_bytes())
        data["candidate"]["runs"][0]["status"] = "NOT_RUN"
        self.source.write_text(json.dumps(data))
        trace = self.root / data["candidate"]["runs"][0]["evidence"]["trace"]["path"]
        before = trace.read_bytes()
        result = subprocess.run([sys.executable, "-I", "-B", str(SCRIPT), str(self.source),
                                 "--out", str(trace)], capture_output=True, text=True)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertEqual(before, trace.read_bytes())
        data["candidate"]["runs"] = []
        self.source.write_text(json.dumps(data))
        out = self.root / "quality.json"
        result = subprocess.run([sys.executable, "-I", "-B", str(SCRIPT), str(self.source),
                                 "--out", str(out)], capture_output=True, text=True)
        self.assertEqual(4, result.returncode, result.stderr)
        self.assertEqual("INCONCLUSIVE", json.loads(out.read_text())["status"])


if __name__ == "__main__":
    unittest.main()
