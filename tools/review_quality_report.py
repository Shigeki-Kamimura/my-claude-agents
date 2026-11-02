#!/usr/bin/env python3
"""独立採点した同条件のレビュー結果を比較します。レビュー自体は起動しません。"""

import argparse
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from statistics import median
import sys


CONTROLS = ("task_snapshot", "prompt_sha256", "role", "model", "effort", "cli_version", "tool_policy")
MIN_REPEATS = 3


def names(value):
    if (not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value)
            or len(set(value)) != len(value)):
        raise ValueError("ID一覧は重複のない文字列配列で指定してください")
    return set(value)


def assess(data, root):
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise ValueError("schema_version: 1のオブジェクトが必要です")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("空でないcases配列が必要です")
    gaps, failures, results, inputs = [], [], [], set()
    cost_gaps, cost_pairs, used_usage = [], {}, set()

    def measured_cost(run, label):
        refs = run.get("evidence", {})
        ref = refs.get("usage") if isinstance(refs, dict) else None
        if (run.get("cost_accounting_reviewed") is not True or not isinstance(ref, dict)
                or not isinstance(ref.get("path"), str) or not ref["path"]):
            cost_gaps.append(f"{label}: 全担当の使用量と独立した集計確認がありません")
            return None
        path = (root / ref["path"]).resolve()
        inputs.add(path)
        try:
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != ref.get("sha256"):
                raise ValueError("使用量ハッシュ不一致")
            if ref["sha256"] in used_usage:
                raise ValueError("同じ使用量証拠を再利用しています")
            used_usage.add(ref["sha256"])
            usage = json.loads(raw)
            participants = names(run.get("participants"))
            sources = usage["sources"]
            if not isinstance(sources, dict) or "parent" not in participants or set(sources) != participants:
                raise ValueError("親を含む全担当の一覧が不一致です")
            total = 0
            for source in sources.values():
                if source.get("status") != "AVAILABLE":
                    raise ValueError("不完全な担当使用量があります")
                tokens = source["tokens"]
                values = [tokens[k] for k in ("input_tokens", "output_tokens", "total_tokens")]
                if any(type(v) is not int or v < 0 for v in values) or sum(values[:2]) != values[2]:
                    raise ValueError("担当使用量が不正です")
                total += values[2]
            combined = usage["combined_tokens"]["total_tokens"]
            if type(combined) is not int or total <= 0 or total != combined:
                raise ValueError("全担当の合計が不一致です")
            since, until = [datetime.fromisoformat(usage["window"][k].replace("Z", "+00:00"))
                            for k in ("since", "until")]
            if since.utcoffset() is None or until.utcoffset() is None or since >= until:
                raise ValueError("実行期間が不正です")
            return {"total_tokens": total, "elapsed_seconds": (until - since).total_seconds()}
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            cost_gaps.append(f"{label}: 全担当の使用量・期間の証拠が不完全です")
            return None

    def evidence(ref, label):
        if not isinstance(ref, dict) or not isinstance(ref.get("path"), str) or not ref["path"]:
            gaps.append(f"{label}: 証拠参照なし")
            return False
        path = (root / ref["path"]).resolve()
        inputs.add(path)
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            gaps.append(f"{label}: 証拠ファイルなし")
            return False
        if digest != ref.get("sha256"):
            gaps.append(f"{label}: 証拠ハッシュ不一致")
            return False
        return True

    catalog = {}
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str) or not case["id"]:
            raise ValueError("caseにはidが必要です")
        key = case["id"]
        if key in catalog:
            raise ValueError("case IDが重複しています")
        expected, required = names(case.get("expected_defects")), names(case.get("required_checks"))
        if (not isinstance(case.get("kind"), str)
                or case["kind"] not in {"defect", "clean", "hold"} or not required):
            raise ValueError("caseのkindまたはrequired_checksが不正です")
        if (case["kind"] == "defect") != bool(expected):
            raise ValueError("defectには既知の欠陥IDを、clean/holdには空配列を指定してください")
        if not isinstance(case.get("expected_verdict"), str) or not case["expected_verdict"]:
            raise ValueError("expected_verdictが必要です")
        ready = evidence(case.get("oracle"), f"{key}/oracle")
        catalog[key] = (case, expected, required, ready)
    if not {"defect", "clean"} <= {v[0]["kind"] for v in catalog.values()}:
        gaps.append("既知欠陥と正常例の両方が必要です")

    indexed = {}
    for side in ("baseline", "candidate"):
        group = data.get(side)
        if not isinstance(group, dict) or not isinstance(group.get("runs"), list):
            raise ValueError(f"{side}にはruns配列が必要です")
        if not isinstance(group.get("configuration"), str) or not group["configuration"].strip():
            gaps.append(f"{side}: 設定版が未記録です")
        index = {}
        for run in group["runs"]:
            if not isinstance(run, dict):
                raise ValueError("runはオブジェクトで指定してください")
            key, repeat = run.get("case_id"), run.get("repeat")
            if not isinstance(key, str) or key not in catalog or type(repeat) is not int or repeat < 1:
                raise ValueError("runのcase_idまたはrepeatが不正です")
            if (key, repeat) in index:
                raise ValueError("同じcase/repeatが重複しています")
            index[key, repeat] = run
            refs = run.get("evidence", {})
            if isinstance(refs, dict):
                for ref in refs.values():
                    if isinstance(ref, dict) and isinstance(ref.get("path"), str) and ref["path"]:
                        inputs.add((root / ref["path"]).resolve())
        indexed[side] = index
    if data["baseline"].get("configuration") == data["candidate"].get("configuration"):
        gaps.append("比較する設定版が同一です")

    used_traces = set()

    def measured(run, case_id, side):
        label = f"{case_id}/{run['repeat']}/{side}"
        if run.get("status") != "EXECUTED":
            gaps.append(f"{label}: 実行未完了です")
            return None
        if (not isinstance(run.get("assessor"), str) or not run["assessor"].strip()
                or run.get("assessment_origin") != "independent"):
            gaps.append(f"{label}: 独立採点者が未記録です")
            return None
        refs = run.get("evidence", {})
        if not isinstance(refs, dict):
            raise ValueError("evidenceはオブジェクトで指定してください")
        valid = [evidence(refs.get(kind), f"{label}/{kind}") for kind in ("output", "trace", "assessment")]
        if not all(valid):
            return None
        trace_hash = refs["trace"]["sha256"]
        if trace_hash in used_traces:
            gaps.append(f"{label}: 同じ実行証拠が再利用されています")
            return None
        used_traces.add(trace_hash)
        needed = ("detected_defects", "false_positive_ids", "scope_error_ids")
        if any(run.get(key) is None for key in needed) or not isinstance(run.get("checks"), dict):
            gaps.append(f"{label}: 採点が未完了です")
            return None
        detected, false_positive, scope_error = (names(run[key]) for key in needed)
        if not detected <= catalog[case_id][1]:
            raise ValueError("detected_defectsに未定義の欠陥IDがあります")
        controls = run.get("conditions")
        if (not isinstance(controls, dict)
                or any(not isinstance(controls.get(k), str) or not controls[k].strip() for k in CONTROLS)):
            gaps.append(f"{label}: 比較条件が未記録です")
            return None
        if any(not re.fullmatch(r"[0-9a-f]{64}", controls[k]) for k in ("task_snapshot", "prompt_sha256")):
            gaps.append(f"{label}: 対象と依頼文のSHA-256が未記録です")
            return None
        return {"detected": detected, "false_positive": false_positive,
                "scope_error": scope_error, "conditions": controls}

    for case_id, (case, expected, required, oracle_ready) in catalog.items():
        repeats = {r for k, r in indexed["baseline"] if k == case_id} | {
            r for k, r in indexed["candidate"] if k == case_id}
        paired, case_controls = 0, None
        for repeat in sorted(repeats):
            runs = [indexed[side].get((case_id, repeat)) for side in ("baseline", "candidate")]
            if any(run is None for run in runs):
                gaps.append(f"{case_id}/{repeat}: 比較相手なし")
                continue
            values = [measured(run, case_id, side) for run, side in zip(runs, ("baseline", "candidate"))]
            if not oracle_ready or any(value is None for value in values):
                continue
            before, after = values
            if any(before["conditions"][k] != after["conditions"][k] for k in CONTROLS):
                gaps.append(f"{case_id}/{repeat}: 比較条件不一致")
                continue
            current_controls = {k: before["conditions"][k] for k in CONTROLS}
            if case_controls is not None and case_controls != current_controls:
                gaps.append(f"{case_id}/{repeat}: 繰返し間の比較条件不一致")
                continue
            case_controls = current_controls
            paired += 1
            costs = [measured_cost(run, f"{case_id}/{repeat}/{side}")
                     for run, side in zip(runs, ("baseline", "candidate"))]
            if all(cost is not None for cost in costs):
                cost_pairs.setdefault(case_id, []).append(costs)
            missing_checks = sorted(k for k in required if runs[1]["checks"].get(k) != "COMPLETE")
            missed = sorted(expected - after["detected"])
            lost = sorted(before["detected"] - after["detected"])
            row = {"case_id": case_id, "repeat": repeat, "missed_defects": missed,
                   "lost_detections": lost, "false_positive_ids": sorted(after["false_positive"]),
                   "scope_error_ids": sorted(after["scope_error"]), "missing_checks": missing_checks,
                   "baseline_missed_defects": sorted(expected - before["detected"]),
                   "baseline_false_positive_ids": sorted(before["false_positive"]),
                   "baseline_scope_error_ids": sorted(before["scope_error"]),
                   "verdict_matches": runs[1].get("verdict") == case["expected_verdict"]}
            results.append(row)
            if (missed or after["false_positive"] or after["scope_error"] or missing_checks
                    or not row["verdict_matches"]):
                failures.append(f"{case_id}/{repeat}: 品質条件を満たしていません")
        if paired < MIN_REPEATS:
            gaps.append(f"{case_id}: 有効な比較は{paired}回です。最低{MIN_REPEATS}回必要です")
    status = "FAIL" if failures else "INCONCLUSIVE" if gaps else "NO_OBSERVED_REGRESSION"
    cost_results = []
    for case_id in catalog:
        pairs = cost_pairs.get(case_id, [])
        if len(pairs) < MIN_REPEATS:
            cost_gaps.append(f"{case_id}: 全担当を含む費用比較が最低{MIN_REPEATS}回必要です")
            continue
        row = {"case_id": case_id, "pairs": len(pairs)}
        for index, side in enumerate(("baseline", "candidate")):
            row[side] = {"total_tokens": sum(p[index]["total_tokens"] for p in pairs),
                         "median_tokens": median(p[index]["total_tokens"] for p in pairs),
                         "median_elapsed_seconds": median(p[index]["elapsed_seconds"] for p in pairs),
                         "total_elapsed_seconds": sum(p[index]["elapsed_seconds"] for p in pairs)}
        row["beneficial"] = (row["candidate"]["total_tokens"] < row["baseline"]["total_tokens"]
                             and row["candidate"]["total_elapsed_seconds"] <= row["baseline"]["total_elapsed_seconds"]
                             and row["candidate"]["median_elapsed_seconds"] <= row["baseline"]["median_elapsed_seconds"])
        cost_results.append(row)
    benefit_status = ("REJECTED" if status == "FAIL" else
                      "INCONCLUSIVE" if status == "INCONCLUSIVE" or cost_gaps else
                      "BENEFIT_OBSERVED" if all(r["beneficial"] for r in cost_results) else "NOT_BENEFICIAL")
    return {"status": status, "paired_results": results, "failures": failures, "gaps": gaps,
            "benefit": {"status": benefit_status, "comparisons": cost_results, "gaps": cost_gaps},
            "limitations": ["採点と期待値は独立評価者の提供情報です。内容の正しさは自動判定しません。",
                            "証拠ファイルの存在とハッシュを確認します。レビューは起動しません。",
                            "結果は比較した事例に限ります。トークン削減で品質条件を相殺しません。",
                            "使用量への全呼出しの包含は独立採点者が確認します。参加者一覧だけでは証明しません。",
                            "採用候補は各例の全試行合計tokensと、経過時間の合計・中央値で比較します。実請求額は示しません。"]}, inputs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assessment", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--require-benefit", action="store_true", help="追加層の比較では品質と総使用量・時間を必須にします")
    args = parser.parse_args(argv)
    try:
        assessment_bytes = args.assessment.read_bytes()
        data = json.loads(assessment_bytes)
        result, inputs = assess(data, args.assessment.resolve().parent)
        result["assessment_sha256"] = hashlib.sha256(assessment_bytes).hexdigest()
        inputs.add(args.assessment.resolve())
        if (args.out.resolve() in inputs or
                (args.out.exists() and any(args.out.samefile(p) for p in inputs if p.exists()))):
            raise ValueError("出力先が入力証拠と同じです")
        spec = importlib.util.spec_from_file_location(
            "review_record", Path(__file__).with_name("render_review_record.py"))
        rr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rr)
        rr.ensure_safe_output(args.out)
        args.out.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        rr.write_atomic(args.out, (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode())
        print(f"{result['status']}; benefit={result['benefit']['status']}: {args.out}")
        if args.require_benefit and result["status"] == "NO_OBSERVED_REGRESSION":
            return {"BENEFIT_OBSERVED": 0, "INCONCLUSIVE": 4, "NOT_BENEFICIAL": 5}[result["benefit"]["status"]]
        return {"NO_OBSERVED_REGRESSION": 0, "FAIL": 3, "INCONCLUSIVE": 4}[result["status"]]
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
