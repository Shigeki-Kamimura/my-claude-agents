#!/usr/bin/env python3
"""許可済みの1担当だけをread-only CLIで実行します。既定はdry-runです。"""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
from types import SimpleNamespace

import implementation_review as controller
import implementation_review_archive as archive
import implementation_review_state as flow


def allowed_task(state: dict, job_id: str) -> dict:
    flow.require(state["status"] == "RUNNING" and state["archive_status"] == "COMPLETE", "runまたはHTML記録が停止中です")
    job = state["jobs"].get(job_id)
    flow.require(job and job["status"] == "PLANNED", "不明または起動済みの担当です")
    flow.require(job["slot"] != "hq", "実装は親HQが行います。このlauncherは読み取り専用です")
    return job


def codex_log(session_id: str, start: dt.datetime, end: dt.datetime, home: Path) -> Path:
    """実IDと起動日の前後だけを、ファイル名で探します。本文総当たりはしません。"""
    flow.require(re.fullmatch(r"[A-Za-z0-9_-]+", session_id), "実セッションIDが不正です")
    flow.require(end >= start and (end - start).total_seconds() <= 86400, "ログ探索の時間範囲が不正です")
    dates = set()
    for point in (start.date(), end.date()):
        dates.update(point + dt.timedelta(days=offset) for offset in (-1, 0, 1))
    candidates = []
    for day in sorted(dates):
        folder = home / "sessions" / f"{day.year:04d}" / f"{day.month:02d}" / f"{day.day:02d}"
        candidates.extend(folder.glob("rollout-*-" + session_id + ".jsonl"))
    flow.require(len(candidates) == 1, "実IDに対応するCodex会話を一意に取得できません")
    path = candidates[0]
    archive.safe_regular(path)
    matches = []
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("type") == "session_meta":
                matches.append(row.get("payload", {}).get("id"))
                break
    flow.require(matches == [session_id], "会話ファイル内の実IDが一致しません")
    return path


def make_prompt(state: dict, job: dict, round_dir: Path) -> str:
    payload = flow.task_payload(state, job["id"])
    payload.update({"project": state["source_config"]["project"],
                    "snapshot_file": str(round_dir / "snapshot.json"),
                    "rule_sources": state["source_config"]["rules"],
                    "contract": str(controller.ROOT / ".claude/knowledge/implementation-review.md")})
    if job["mode"] == "initial" and job["slot"] in {"cr_a", "cr_b"}:
        flow.require("reports" not in payload and "open_findings" not in payload, "初回担当へ相手の結果を渡せません")
    consultant_note = ("L2の必須React/Nest等の相談は既存の規約に従って実行し、実担当・原本・応答を記録してください。\n"
                       if job["slot"] == "l2" else "他の層や専門担当を追加起動してはいけません。\n")
    return ("Workflow: implementation-pcr-loop\n" + consultant_note
            + "実装・commit・push・PR操作を行わず、指定した実担当だけを呼んでください。\n"
            "通常のcr:や既存の双方向workflowへ読み替えないでください。\n"
            "同じ親子の継続なら、previous_ownerの実担当だけを再開してください。\n"
            "新規担当なら、実装会話と相手の初回結果を渡さないでください。\n"
            "実担当はmcp md_review.review_context(current)を読み、必要な原本と例外を確認します。\n"
            "QA/E2Eは正常系・異常系の不足と過剰、期待値、fixture/mockを両方確認します。\n"
            "コード変更、アプリ・テスト・lint・build・CI実行、追加層の起動は禁止です。\n"
            "実担当の最終応答は、契約のimplementation-review-result JSONを1つ含めてください。\n"
            "親は実担当の最終応答を変更せず返してください。起動できなければBLOCKEDです。\n\n"
            + json.dumps(payload, ensure_ascii=False, indent=2))


def stop_and_archive(folder: Path, reason: str, message: str, logs: list[dict], missing: list[str]) -> None:
    fd = os.open(folder / ".controller.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        state = controller.load_json(folder / "state.json")
        flow.stop(state, reason, message)
        for source in logs:
            state["archive_sources"][source["owner_id"]] = source
        state["required_archive_owners"] = sorted(set(state["required_archive_owners"]) | set(missing) | {s["owner_id"] for s in logs})
        controller.persist(folder, state, {"type": "transport_failure", "reason": reason, "message": message})
    finally:
        os.close(fd)


def execute(args) -> dict:
    folder = args.run_dir.expanduser().absolute()
    flow.require(not any(p.is_symlink() for p in (folder, *folder.parents)), "runへのsymlinkは使用できません")
    state = controller.load_json(folder / "state.json")
    job = allowed_task(state, args.job_id)
    if not args.apply:
        return {"status": "DRY_RUN", "job": flow.task_payload(state, job["id"]), "launch": False}
    flow.require(shutil.which(job["provider"]) is not None, "指定したCLIがありません。別モデルへ切り替えません")
    if job["provider"] == "claude":
        used = [j for j in state["jobs"].values() if j.get("receipt", {}).get("provider") == "claude" and j["slot"] != job["slot"]]
        flow.require(not used or args.confirm_more_claude_layers, "Claudeの追加層には利用者による事前確認が必要です")
    runner = controller.load_dependency("start_md_review")
    review = controller.load_dependency("md_review")
    receipts = controller.load_dependency("review_receipts")
    flow.require(callable(getattr(runner, "command_for_provider", None)), "共通transportの追加差分が未反映です")
    provider_lock = None
    if job["provider"] == "claude":
        provider_lock = os.open(folder / ".claude-dispatch.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(provider_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            os.close(provider_lock)
            raise flow.ContractError("同じrunでClaudeが実行中です。追加起動しません")
    known_logs = []
    started = dt.datetime.now(dt.timezone.utc)
    claimed = False
    failure_status = "BLOCKED"
    try:
        controller.run_command(SimpleNamespace(command="claim", run_dir=folder, job_id=job["id"]))
        state = controller.load_json(folder / "state.json")
        job = state["jobs"][job["id"]]
        flow.require(state["status"] == "RUNNING" and job["status"] == "CLAIMED", "依頼を確保できません")
        claimed = True
        round_dir = folder / job["id"]
        round_dir.mkdir(mode=0o700)
        for view in ("base", "head", "index", "worktree"):
            (round_dir / view).mkdir(mode=0o700)
        frozen = controller.source_identity(state["source_config"], round_dir)
        flow.require(frozen["snapshot_id"] == job["snapshot_id"] and frozen["rules_id"] == job["rules_id"], "固定版が変わりました")
        archive.atomic_write(round_dir / "snapshot.json", json.dumps({k: v for k, v in frozen.items() if k != "rules_id"}, ensure_ascii=False).encode())
        comparison = None
        if job.get("previous_snapshot_id"):
            comparison = runner.previous_source(folder / "snapshots", {
                "round_id": job["previous_snapshot_id"], "result": {"snapshot_id": job["previous_snapshot_id"]}}, round_dir, frozen)
            archive.atomic_write(round_dir / "comparison.json", json.dumps(comparison, ensure_ascii=False).encode())
        request = flow.task_payload(state, job["id"])
        request.update(required_diff_views=["delta"] if comparison and job.get("prior_coverage") == "COMPLETE" else ["branch", "staged", "unstaged"],
                       comparison_file=str(round_dir / "comparison.json") if comparison else None,
                       project=state["source_config"]["project"], rule_source_files=state["source_config"]["rules"],
                       snapshot_file=str(round_dir / "snapshot.json"),
                       contract_file=str(controller.ROOT / ".claude/knowledge/implementation-review.md"))
        archive.atomic_write(round_dir / "context.json", json.dumps({"request": request, "sections": {}}, ensure_ascii=False).encode())
        prompt = make_prompt(state, job, round_dir)
        archive.atomic_write(round_dir / "request.txt", prompt.encode())
        resume = job["previous_parent"] if job["owner_mode"] == "resume" and job["provider"] == "claude" else None
        # 外部Codexはfresh execです。元担当必須の依頼を別担当へ読み替えません。
        flow.require(not (job["provider"] == "codex" and job["owner_mode"] == "resume"), "この継続は元のnative担当へ戻してください")
        argv = runner.command_for_provider(job["provider"], state["source_config"]["project"], round_dir, resume)
        policy_id = flow.identity({"launcher": archive.digest(Path(runner.__file__).read_bytes()),
                                   "gate": archive.digest((controller.ROOT / "tools/md_review_tool_gate.py").read_bytes())})
        if resume:
            previous = next(h["receipt"] for h in reversed(state["history"]) if h["receipt"]["owner_id"] == job["previous_owner"])
            flow.require(previous.get("transport_policy_id") == policy_id, "再開先の制限設定を確認できません")
        env = dict(os.environ)
        env["CLAUDE_CODE_DISABLE_ADVISOR_TOOL"] = "1"
        with (round_dir / "stdout.jsonl").open("x", encoding="utf-8") as output, (round_dir / "stderr.log").open("x", encoding="utf-8") as errors:
            os.chmod(round_dir / "stdout.jsonl", 0o600)
            os.chmod(round_dir / "stderr.log", 0o600)
            with subprocess.Popen(argv, cwd=state["source_config"]["project"], env=env, stdin=subprocess.PIPE,
                                  stdout=output, stderr=errors, text=True, start_new_session=True) as process:
                try:
                    process.communicate(prompt, timeout=args.timeout)
                except (subprocess.TimeoutExpired, KeyboardInterrupt):
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.communicate(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.communicate()
                    raise flow.ContractError("実行が時間制限に達しました。再試行していません")
                exit_code = process.returncode
        ended = dt.datetime.now(dt.timezone.utc)
        rows = receipts.records(round_dir / "stdout.jsonl")
        if job["provider"] == "claude":
            limit = runner.rate_limit_signal(round_dir, exit_code)
            if limit:
                failure_status = "RATE_LIMITED"
                raise flow.ContractError("Claudeの利用制限です。別の担当やモデルを起動していません")
            finals = [r for r in rows if r.get("type") == "result"]
            flow.require(bool(finals), "Claudeの終了記録がありません")
            parent_log = receipts.claude_transcript(state["source_config"]["project"], finals[-1].get("session_id"))
            archive.safe_regular(parent_log)
            rows += receipts.records(parent_log)
        native = receipts.identities(rows, job["provider"], job["role"],
                                      {"reviewer_id": job["previous_owner"]} if resume else None)
        owners = [k for k, role in native["children"].items() if role == job["role"]]
        allowed_roles = {job["role"]}
        if job["slot"] == "l2":
            allowed_roles |= {"react-ui-flow", "vue-frontend", "nestjs-backend", "spring-boot", "sec-arch", "data-platform"}
        flow.require(len(owners) == 1 and set(native["children"].values()) <= allowed_roles,
                     "未選択の担当の起動、または担当不明です")
        owner = owners[0]
        flow.require(re.fullmatch(r"[A-Za-z0-9_-]+", owner), "子の実IDが不正です")
        if job["provider"] == "codex":
            home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
            parent_log = codex_log(native["parent_session_id"], started, ended, home)
            child_log = codex_log(owner, started, ended, home)
        else:
            child_log = parent_log.with_suffix("") / "subagents" / ("agent-" + owner + ".jsonl")
        support_logs = []
        for extra_id, role in native["children"].items():
            if extra_id == owner:
                continue
            if job["provider"] == "codex":
                extra_path = codex_log(extra_id, started, ended, home)
            else:
                flow.require(re.fullmatch(r"[A-Za-z0-9_-]+", extra_id), "専門担当の実IDが不正です")
                extra_path = parent_log.with_suffix("") / "subagents" / ("agent-" + extra_id + ".jsonl")
            support_logs.append([extra_id, role, str(extra_path)])
        known_logs = [controller.log_window(native["parent_session_id"], job["slot"] + "呼出し親", parent_log),
                      controller.log_window(owner, job["slot"], child_log)] + [controller.log_window(i, r, Path(p)) for i, r, p in support_logs]
        flow.require(exit_code == 0, "CLIが正常終了していません")
        invocation = round_dir / "native-invocation.jsonl"
        archive.atomic_write(invocation, b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows))
        archive.atomic_write(round_dir / "transport.json", json.dumps({"policy_id": policy_id, "started_at": started.isoformat(),
             "finished_at": ended.isoformat(), "provider": job["provider"], "owner_id": owner,
             "parent_id": native["parent_session_id"], "previous_owner": job["previous_owner"],
             "ledger_id": job["ledger_id"], "transport": "cli"}, ensure_ascii=False).encode())
        finished = controller.run_command(SimpleNamespace(command="finish", run_dir=folder, job_id=job["id"], owner_id=owner,
            invocation_log=invocation, child_log=child_log, review_parent_log=parent_log, support_log=support_logs))
        if finished.get("status") in {"BLOCKED", "RATE_LIMITED"}:
            stop_and_archive(folder, finished["status"], finished.get("stop_reason", "結果受理に失敗しました"), known_logs, [])
            return controller.load_json(folder / "state.json")
        return finished
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        if claimed:
            # 実子の特定前でも、取得済みstdoutは捨てません。完全な会話とは扱いません。
            missing = ["unfinished:" + job["id"]] if not known_logs else []
            output_path = folder / job["id"] / "stdout.jsonl"
            if not known_logs and output_path.is_file():
                known_logs = [controller.log_window("transport:" + job["id"], "取得済みCLI応答（部分記録）", output_path)]
            stop_and_archive(folder, failure_status, str(exc), known_logs, missing)
        raise
    finally:
        if provider_lock is not None:
            os.close(provider_lock)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--confirm-more-claude-layers", action="store_true", help="利用者が事前確認した場合のみ指定します")
    args = parser.parse_args(argv)
    try:
        flow.require(1 <= args.timeout <= 86400, "timeoutの範囲が不正です")
        result = execute(args)
        print(json.dumps(controller.compact_response(result), ensure_ascii=False, indent=2))
        return 0 if result.get("status") not in {"BLOCKED", "RATE_LIMITED"} else 2
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
