#!/usr/bin/env python3
"""親エージェント用の遷移制御です。明示したrun以外を探索しません。"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import uuid

import implementation_review_archive as archive
import implementation_review_state as flow

ROOT = Path(__file__).resolve().parents[1]


def load_dependency(name: str):
    path = ROOT / "tools" / (name + ".py")
    if not path.is_file():
        raise flow.ContractError("既存の依存ツールがありません: " + str(path))
    spec = importlib.util.spec_from_file_location("loop_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def load_json(path: Path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            flow.require(key not in result, "JSONのキーが重複しています")
            result[key] = value
        return result
    archive.safe_regular(path)
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)


def source_identity(config: dict, destination: Path | None = None) -> dict:
    review = load_dependency("md_review")
    changed, _secrets = review.changed_paths(config)
    cfg = {**config, "paths": changed}
    review.check_scope(cfg)
    record = review.capture(cfg, destination)
    record["rules_id"] = flow.identity(record["rules"])
    return record


def log_window(owner: str, label: str, path: Path, start: int = 0) -> dict:
    archive.safe_regular(path)
    return {"owner_id": owner, "label": label, "path": str(path.absolute()), "start": start, "end": path.stat().st_size}


def refresh_parent(state: dict) -> None:
    item = state["archive_sources"]["parent"]
    item["end"] = Path(item["path"]).stat().st_size


def persist(folder: Path, state: dict, event: dict) -> dict:
    """HTMLを先に確定し、その後で実行可能な状態を保存します。"""
    candidate = copy.deepcopy(state)
    used = [int(p.stem.split("-")[-1]) for p in (folder / "records").glob("record-*.html")
            if p.stem.split("-")[-1].isdigit()]
    candidate["revision"] = max([state.get("revision", 0), *used]) + 1
    candidate["updated_at"] = now()
    refresh_parent(candidate)
    intent = folder / "pending-transition.json"
    archive.atomic_write(intent, json.dumps({"candidate": candidate, "event": event}, ensure_ascii=False).encode())
    expected = {"parent"} | set(candidate.get("required_archive_owners", []))
    record = archive.save_record(folder, candidate["revision"], candidate,
                                 list(candidate["archive_sources"].values()), expected)
    candidate["archive_status"] = record["status"]
    candidate["last_html"] = record["html_path"]
    candidate["audit"].append({"at": candidate["updated_at"], **event})
    # 同じ状態を二重処理しないため、未解決のHTML欠落では必ず停止します。
    if record["status"] != "COMPLETE":
        candidate["archive_error"] = "会話の取得・HTML保存が未完了です。記録を補って確認してください"
        if candidate["status"] not in {"RATE_LIMITED", "NEEDS_USER_INPUT"}:
            flow.stop(candidate, "BLOCKED", candidate["archive_error"])
    journal = folder / "review.md"
    entry = "\n\n## Controller event\n\n```json\n" + json.dumps(event, ensure_ascii=False, indent=2) + "\n```\n"
    previous = journal.read_text(encoding="utf-8") if journal.exists() else "# Implementation review\n"
    archive.atomic_write(journal, (previous + entry).encode())
    archive.atomic_write(folder / "state.json", json.dumps(candidate, ensure_ascii=False, indent=2).encode())
    intent.unlink()
    return candidate


def create(args) -> dict:
    project = args.project.expanduser().resolve()
    folder = args.run_dir.expanduser().absolute()
    flow.require(not folder.exists(), "runの保存先は新規フォルダーにしてください")
    flow.require(not folder.resolve().is_relative_to(project), "記録は対象リポジトリの外へ保存してください")
    flow.require(not any(p.is_symlink() for p in [folder, *folder.parents]), "保存先にsymlinkがあります")
    raw = load_json(args.policy)
    policy = flow.Policy(**raw)
    policy.validate()
    review = load_dependency("md_review")
    base = review.git(project, "rev-parse", "--verify", args.base + "^{commit}").decode().strip()
    merge_base = review.git(project, "merge-base", base, "HEAD").decode().strip()
    rules = [str(p.expanduser().resolve(strict=True)) for p in args.rules]
    flow.require(bool(rules), "必須規約の原本を指定してください")
    config = {"project": str(project), "base": merge_base, "base_provenance": base,
              "rules": rules, "exclusions": dict(args.exclude or [])}
    before = source_identity(config)
    request = args.request_file.read_text(encoding="utf-8")
    state = flow.new_state(policy, before["snapshot_id"], before["rules_id"], request)
    state.update({"run_id": str(uuid.uuid4()), "source_config": config, "source_record": before,
                  "archive_sources": {"parent": log_window("parent", "親", args.parent_log, args.parent_start)},
                  "required_archive_owners": [], "audit": [], "revision": 0})
    folder.mkdir(parents=True, mode=0o700)
    (folder / "snapshots").mkdir(mode=0o700)
    archive.atomic_write(folder / "review.md", ("# Implementation review\n\n## User request\n\n" + request + "\n").encode())
    return persist(folder, state, {"type": "authorized_start", "policy": raw, "snapshot_id": before["snapshot_id"]})


def verify_source(state: dict) -> dict:
    current = source_identity(state["source_config"])
    flow.require(current["rules_id"] == state["rules_id"], "開始時の規約版が変わりました")
    return current


def result_block(body: str) -> dict:
    blocks = re.findall(r"(?m)^```implementation-review-result\s*\n(.*?)\n```\s*$", body, re.S)
    flow.require(len(blocks) == 1, "実担当の結果に判定JSONが1つ必要です")
    result = json.loads(blocks[0])
    flow.require(isinstance(result, dict), "判定JSONがobjectではありません")
    return result


def native_completion(state: dict, job: dict, args, current: dict) -> tuple[dict, dict, list[dict]]:
    """実ログの親子IDと最終応答から結果を取り出します。"""
    receipts = load_dependency("review_receipts")
    archive.safe_regular(args.invocation_log)
    rows = receipts.records(args.invocation_log)
    native = receipts.identities(rows, job["provider"], job["role"])
    owner_id = args.owner_id
    flow.require(native["children"].get(owner_id) == job["role"], "指定した実担当を起動した証拠がありません")
    archive.safe_regular(args.child_log)
    renderer = archive.renderer_from()
    child_source, stats = archive.read_window(renderer, log_window(owner_id, job["slot"], args.child_log))
    flow.require(stats["status"] == "COMPLETE", "子の会話記録が欠落しています")
    replies = [e[4] for e in child_source.events if e[2] == "message" and e[3] == "assistant"]
    flow.require(bool(replies), "子の最終応答がありません")
    body = replies[-1]
    result = result_block(body)
    if job["provider"] == "codex":
        flow.require(native["completed"].get(owner_id) == body, "起動記録の完了本文と子の最終応答が一致しません")
    else:
        flow.require(any(r.get("type") == "result" and r.get("is_error") is False
                         and r.get("subtype") == "success" for r in rows), "Claude親の成功終了を確認できません")
    # reviewerを名乗るだけの親の応答は受理しません。
    receipt = {"job_id": job["id"], "provider": job["provider"], "role": job["role"],
               "parent_id": native["parent_session_id"], "owner_id": owner_id,
               "completed": True, "actual_child": True,
               "source_before": job["snapshot_id"], "source_after": current["snapshot_id"],
               "frozen_source_dir": job.get("frozen_source_dir"),
               "started_at": job["claimed_at"], "finished_at": now(),
               "evidence_ref": str(args.invocation_log.absolute())}
    transport_path = args.invocation_log.parent / "transport.json"
    if transport_path.is_file():
        transport = load_json(transport_path)
        flow.require(transport.get("owner_id") == owner_id and transport.get("parent_id") == native["parent_session_id"]
                     and transport.get("provider") == job["provider"], "transport記録が実担当と一致しません")
        receipt.update(transport="cli", transport_policy_id=transport.get("policy_id"),
                       previous_owner=transport.get("previous_owner"), ledger_id=transport.get("ledger_id"),
                       started_at=transport["started_at"], finished_at=transport["finished_at"])
    # 実起動を受けた親の会話も、明示されたログだけを保存します。
    sources = [log_window(owner_id, job["slot"] + " / " + job["provider"], args.child_log),
               log_window(native["parent_session_id"], job["slot"] + "の呼出し親", args.review_parent_log)]
    support = getattr(args, "support_log", None) or []
    consultants = {}
    for other_id, role, path_text in support:
        flow.require(job["slot"] == "l2" and native["children"].get(other_id) == role, "専門担当の実起動が一致しません")
        path = Path(path_text)
        item = log_window(other_id, role, path)
        source, evidence = archive.read_window(renderer, item)
        messages = [e[4] for e in source.events if e[2] == "message" and e[3] == "assistant"]
        flow.require(evidence["status"] == "COMPLETE" and bool(messages), "専門担当の会話が未完了です")
        if job["provider"] == "codex":
            flow.require(native["completed"].get(other_id) == messages[-1], "専門担当の完了本文が不一致です")
        consultants[other_id] = {"role": role, "completed": True, "evidence_ref": str(path), "sha256": evidence["sha256"]}
        sources.append(item)
    receipt["consultants"] = consultants
    return result, receipt, sources


def implementation_completion(state: dict, job: dict, result_file: Path, current: dict):
    """親HQの申告はSuppliedです。独立レビューの判定としては使いません。"""
    flow.require(job["slot"] == "hq", "親による実装申告はHQ専用です")
    result = load_json(result_file)
    parent_path = Path(state["archive_sources"]["parent"]["path"])
    parent_ids = set()
    with parent_path.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("type") == "session_meta":
                value = row.get("payload", {}).get("id")
            elif row.get("type") in {"user", "assistant", "result"}:
                value = row.get("sessionId") or row.get("session_id")
            else:
                value = None
            if isinstance(value, str) and value:
                parent_ids.add(value)
    flow.require(len(parent_ids) == 1, "実装親の実IDを確認できません")
    parent_id = next(iter(parent_ids))
    receipt = {"job_id": job["id"], "provider": job["provider"], "role": job["role"],
               "parent_id": parent_id, "owner_id": parent_id, "completed": True,
               "actual_child": False, "implementation_parent": True, "transport": "native",
               "source_before": job["snapshot_id"], "source_after": current["snapshot_id"],
               "frozen_source_dir": job.get("frozen_source_dir"),
               "started_at": job["claimed_at"], "finished_at": now(), "evidence_ref": str(parent_path)}
    return result, receipt


def freeze_review_source(folder: Path, state: dict, job: dict) -> None:
    """同じ対象版の実体を一度保存し、次回差分の比較元を残します。"""
    if job["slot"] == "hq":
        return
    target = folder / "snapshots" / state["snapshot_id"]
    if target.exists():
        stored = load_json(target / "snapshot.json")
        flow.require(stored.get("snapshot_id") == state["snapshot_id"], "保存済みsnapshotが一致しません")
    else:
        target.mkdir(mode=0o700)
        for view in ("base", "head", "index", "worktree"):
            (target / view).mkdir(mode=0o700)
        stored = source_identity(state["source_config"], target)
        flow.require(stored["snapshot_id"] == state["snapshot_id"] and stored["rules_id"] == state["rules_id"], "snapshot取得中に対象が変わりました")
        stored = {k: v for k, v in stored.items() if k != "rules_id"}
        archive.atomic_write(target / "snapshot.json", json.dumps(stored, ensure_ascii=False).encode())
    job["frozen_source_dir"] = str(target)
    previous = next((h for h in reversed(state["history"]) if h["result"]["slot"] == job["slot"]), None)
    if previous:
        origin = previous["result"]["snapshot_id"]
        prior = folder / "snapshots" / origin
        flow.require((prior / "snapshot.json").is_file(), "前回の実確認snapshotがありません")
        job["previous_snapshot_id"] = origin
        job["previous_source_dir"] = str(prior)
        job["prior_coverage"] = previous["result"]["coverage"]


def run_command(args) -> dict:
    folder = args.run_dir.expanduser().absolute()
    flow.require(not any(p.is_symlink() for p in [folder, *folder.parents]), "runにsymlinkがあります")
    lock_path = folder / ".controller.lock"
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = load_json(folder / "state.json")
        intent = folder / "pending-transition.json"
        if intent.exists():
            if args.command == "archive":
                pending_record = load_json(intent)
                state = pending_record["candidate"]
                flow.stop(state, "BLOCKED", "記録の復旧です。自動再開はしていません")
                return persist(folder, state, {"type": "archive_recovery", "previous_event": pending_record["event"]})
            raise flow.ContractError("未完了の記録があります。archiveで記録を復旧し、実行状態を確認してください")
        flow.require(state.get("schema_version") == flow.SCHEMA_VERSION, "状態の版が不正です")
        if args.command == "status":
            return {"status": state["status"], "stage": state["stage"], "last_html": state["last_html"],
                    "pending": flow.pending(state), "open_findings": flow.unresolved(state)}
        if args.command == "archive":
            return persist(folder, state, {"type": "archive_checkpoint"})
        if args.command == "halt":
            flow.stop(state, args.reason, args.message)
            return persist(folder, state, {"type": "halt", "reason": args.reason, "message": args.message})
        current = verify_source(state)
        if args.command == "snapshot":
            return current
        if args.command == "next":
            flow.require(current["snapshot_id"] == state["snapshot_id"], "レビュー中に対象が変わりました")
            return {"tasks": [flow.task_payload(state, j["id"]) for j in flow.pending(state)],
                    "status": state["status"], "html": state["last_html"]}
        if args.command == "claim":
            updated = flow.claim(state, args.job_id, current["snapshot_id"], current["rules_id"])
            updated["jobs"][args.job_id]["claimed_at"] = now()
            freeze_review_source(folder, updated, updated["jobs"][args.job_id])
            updated = persist(folder, updated, {"type": "claimed", "job_id": args.job_id})
            return flow.task_payload(updated, args.job_id) if updated["status"] == "RUNNING" else updated
        if args.command == "finish-hq":
            job = state["jobs"].get(args.job_id)
            flow.require(job and job["status"] == "CLAIMED", "未起動のHQです")
            result, receipt = implementation_completion(state, job, args.result_file, current)
            updated = flow.accept(state, job["id"], result, receipt)
            updated["source_record"] = current
            return persist(folder, updated, {"type": "implementation_supplied", "job_id": job["id"], "result": result, "receipt": receipt})
        if args.command == "finish":
            job = state["jobs"].get(args.job_id)
            flow.require(job and job["status"] == "CLAIMED", "未起動・不明な依頼です")
            result, receipt, sources = native_completion(state, job, args, current)
            # 生の結果を先に保存し、受理失敗でも監査できます。
            for source in sources:
                state["archive_sources"][source["owner_id"]] = source
                if source["owner_id"] not in state["required_archive_owners"]:
                    state["required_archive_owners"].append(source["owner_id"])
            try:
                updated = flow.accept(state, args.job_id, result, receipt)
            except (ValueError, KeyError, TypeError) as exc:
                flow.stop(state, "BLOCKED", "結果の受理に失敗しました: " + str(exc))
                return persist(folder, state, {"type": "rejected_result", "job_id": args.job_id, "reason": str(exc)})
            if job["slot"] == "hq":
                updated["source_record"] = current
            return persist(folder, updated, {"type": "completed", "job_id": args.job_id, "result": result, "receipt": receipt})
        raise flow.ContractError("不明な操作です")
    except (ValueError, KeyError, TypeError) as exc:
        if "state" in locals() and not (folder / "pending-transition.json").exists():
            flow.stop(state, "BLOCKED", str(exc))
            return persist(folder, state, {"type": "controller_error", "reason": str(exc)})
        raise
    finally:
        os.close(fd)


def compact_response(result: dict) -> dict:
    """保存済みの全文を、親の文脈へ繰り返し返しません。"""
    if "jobs" not in result or "history" not in result:
        return result
    return {"run_id": result.get("run_id"), "status": result["status"], "stage": result["stage"],
            "snapshot_id": result["snapshot_id"], "fix_rounds": result["fix_rounds"],
            "next": [{"job_id": j["id"], "slot": j["slot"], "provider": j["provider"], "mode": j["mode"]}
                     for j in flow.pending(result)],
            "open_item_ids": [f["key"] for f in flow.unresolved(result)],
            "archive_status": result["archive_status"], "html": result.get("last_html"),
            "stop_reason": result.get("stop_reason"), "archive_error": result.get("archive_error")}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--project", required=True, type=Path)
    init.add_argument("--base", required=True)
    init.add_argument("--run-dir", required=True, type=Path)
    init.add_argument("--policy", required=True, type=Path)
    init.add_argument("--request-file", required=True, type=Path)
    init.add_argument("--rules", required=True, nargs="+", type=Path)
    init.add_argument("--exclude", nargs=2, action="append")
    init.add_argument("--parent-log", required=True, type=Path)
    init.add_argument("--parent-start", required=True, type=int, help="この依頼の先頭行のbyte位置です")
    for operation in ("next", "status", "snapshot", "archive", "claim", "finish", "finish-hq", "halt"):
        sub = commands.add_parser(operation)
        sub.add_argument("--run-dir", required=True, type=Path)
        if operation in {"claim", "finish", "finish-hq"}:
            sub.add_argument("--job-id", required=True)
        if operation == "finish-hq":
            sub.add_argument("--result-file", required=True, type=Path)
        if operation == "finish":
            sub.add_argument("--invocation-log", required=True, type=Path)
            sub.add_argument("--child-log", required=True, type=Path)
            sub.add_argument("--review-parent-log", required=True, type=Path)
            sub.add_argument("--owner-id", required=True)
            sub.add_argument("--support-log", nargs=3, action="append", metavar=("OWNER", "ROLE", "PATH"))
        if operation == "halt":
            sub.add_argument("--reason", choices=("BLOCKED", "RATE_LIMITED", "NEEDS_USER_INPUT"), required=True)
            sub.add_argument("--message", required=True)
    args = parser.parse_args(argv)
    try:
        result = create(args) if args.command == "init" else run_command(args)
        print(json.dumps(compact_response(result), ensure_ascii=False, indent=2))
        return 0 if result.get("status") not in {"BLOCKED", "RATE_LIMITED"} else 2
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
