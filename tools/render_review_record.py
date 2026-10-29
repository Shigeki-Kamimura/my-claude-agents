#!/usr/bin/env python3
"""レビューの会話ログ(JSONL)から、自己完結のHTML記録を決定的に作ります。

LLMは使いません。入力のログを読み、時系列のHTMLを書き出すだけです。外部リソースとJavaScriptはありません。

対応する入力形式(実在するログを確認したもののみ):
  - Claude Codeのセッション: ~/.claude/projects/<名前>/<session_id>.jsonl
    同名フォルダの subagents/agent-*.jsonl とその .meta.json(agentType)も自動で含めます。
  - Codexのセッション: ~/.codex/sessions/<年>/<月>/<日>/rollout-*.jsonl
    (response_item の message / function_call / function_call_output / custom_tool_call(_output) / reasoning と session_meta)
  - 汎用: {"timestamp": ..., "role": ..., "text": ...} の各行
未知の形式の行は推測せず、件数として表示します。Codex形式は実ログの構造でのみ確認しており、実運用は未検証です。

既定では認証情報のみを伏せます。--redact-personalを付けると、URL、メールアドレス、ホームパス、IPv4アドレスも置換します。
ただし個人情報・社内の業務データ全般の匿名化は保証されません。共有前に、必ず目視で確認してください。
既知の制限(伏せ漏れ):
  - キー名に token / secret / password / api_key / private_key / credential / authorization を含まない値
  - 区切りが = か : でない指定(例: --password abc)
  - 4文字未満の引用符なしの値
  - 引用符なしの値に , ; } や空白を含むパスワード(その位置で値が切れます)
  - 引用符付きの値が10000文字を超える、または閉じ引用符がない場合は、行末まで伏せます(伏せ漏れではなく過剰側)
  - 非ASCII文字だけの引用符なしの値(日本語の散文と区別できないため残します。英数字を含めば伏せます)
  - token / tokens の件数(max_tokens、token_count など件数を表すキー)の数字だけの値は、認証情報ではないため残します
  - URL内のパスワードが/を含む場合、または200文字を超える場合
既知の制限(伏せ過ぎ。認証情報でない文字列も伏せることがあります。安全側の動作で、挙動は変えていません):
  - 散文でも Authorization の値は行末まで伏せます(例: Authorization: required for this endpoint)
  - 引用符の中でない Authorization の値は行末まで伏せるため、後続の引数も消えます(例: curl -H "Authorization: Bearer $T" https://...)
  - Bearer の後ろに8文字以上の英数字が続けば伏せます(例: Bearer authentication)
  - 引用符付きの値は、閉じ引用符の直後が区切りでない場合、または値が円記号+引用符で終わる場合、閉じを見つけられず行末まで伏せます
  - JSONの入れ子が5段以上(円記号が5個以上並ぶ引用符)の値は対象外です
出力先の親フォルダーがなければ作成します。.codex 配下が git 管理から除外されるのは、setup を実行した対象プロジェクトだけです。

使い方:
  python3 -I -B tools/render_review_record.py --out "$HOME/review-records/record.html" [--ledger ledger.json] [--no-subagents] [--omit-thinking] [--redact-personal] LOG.jsonl [LOG.jsonl ...]
台帳(任意)は、{"id","severity","summary","before","after","files","status"} を持つオブジェクトのJSON配列です。
"""

import argparse
import html
import json
import os
import re
import sys
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

FOLD_CHARS = 800  # これより長い本文は折りたたみます
FOLD_KINDS = {"tool_use", "tool_result", "thinking", "reasoning", "system", "agent_event"}

# 秘密情報のパターン。上から順に適用します。完全ではありません。
# 計算量を抑えるため、先頭に可変長の繰り返しを置かず、繰り返しには上限を付けています。
KEYWORDS = r"(?:token|secret|passw(?:or)?d|api[_-]?key|private[_-]?key|credential|authorization)"
QUOTE_SCAN = 10000  # 引用符付きの値の探索上限。閉じ引用符が見つからなければ行末まで伏せます(伏せ漏れより過剰側に倒す)
# 引用符付きの値。開き(円記号0〜4個+引用符)と同じ並びで閉じます。円記号が直前にある引用符は値の一部です(\" や JSON入れ子の \\\" )。
# 閉じ引用符の後は区切り(空白、, ; : . } ] ) または円記号)か終端が必要です。閉じがなければ行末までを値とします。空の値("")は対象外です。
QUOTED = (
    r"""(?P<q>\\{0,4}["'])(?!(?P=q))"""
    r"""(?:[^\n]{1,""" + str(QUOTE_SCAN) + r"""}?(?<!\\)(?P=q)(?=[\s,;:.}\])\\]|\Z)|[^\n]*)"""
)
ASSIGNMENT = re.compile(
    r"(?i)(" + KEYWORDS + r"""[\w.-]{0,40}\\{0,4}["']?[ \t]{0,5}[=:][ \t]{0,5})(""" + QUOTED + r"""|[^\s"',;}\\]{4,})"""
)
# Authorizationの値は、認証方式(Bearer/Basic/Token/Digest/ApiKeyなど)に関わらず、行末(引用符付きなら閉じ引用符)まで伏せます。
# 文字列としての \r \n の手前で止めます(JSON内の改行表記)
AUTHORIZATION = re.compile(
    r"(?i)(authorization[\w.-]{0,40}\\{0,4}[\"']?[ \t]{0,5}[=:][ \t]{0,5})(" + QUOTED + r"|(?:(?!\\[rn])[^\n])+)"
)
# 値が明らかに秘密でない散文(引用符なしの場合のみ)。迷う場合は伏せる側に倒します
PROSE_VALUES = {
    "required", "optional", "missing", "none", "null", "true", "false", "empty", "denied", "allowed",
    "invalid", "expired", "unset", "n/a", "redacted", "[redacted]",
}
# 件数を表すキー(max_tokens、total_tokens、token_count など)。数字だけの値は認証情報ではないので残します
COUNT_KEY = re.compile(r"(?i)tokens$|token_?(?:count|limit|usage|budget|total)s?$")

PEM_BEGIN = re.compile(r"-----BEGIN [A-Z ]{0,30}PRIVATE KEY(?: BLOCK)?-----")
PEM_END = re.compile(r"-----END [A-Z ]{0,30}PRIVATE KEY(?: BLOCK)?-----")

# パスワードに@を含むURLでも、ホストの直前の最後の@までをパスワードとして伏せます
REDACTIONS = (
    ("url_credentials", re.compile(r"(?<=://)[^/\s:@]{1,100}:[^/\s]{1,200}(?=@[^@/\s]+(?:[/:?#\s]|\Z))"), "[REDACTED]"),
    ("authorization", AUTHORIZATION, None),
    ("bearer", re.compile(r"(?i)\bBearer[ \t]{1,5}[A-Za-z0-9._~+/=-]{8,500}"), "Bearer [REDACTED]"),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"), "[REDACTED]"),
    ("api_key", re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9_-]{16,300}"), "[REDACTED]"),
    ("github", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,300}|github_pat_[A-Za-z0-9_]{20,300})"), "[REDACTED]"),
    ("aws_key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), "[REDACTED]"),
    ("slack", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,300}"), "[REDACTED]"),
)


def redact_private_keys(text: str):
    """秘密鍵ブロックを伏せます。ENDがなければ、BEGIN以降を最後まで伏せます(線形時間)。"""
    out, pos, count = [], 0, 0
    while True:
        begin = PEM_BEGIN.search(text, pos)
        if not begin:
            out.append(text[pos:])
            break
        out.append(text[pos:begin.start()])
        out.append("[REDACTED]")
        count += 1
        end = PEM_END.search(text, begin.end())
        if not end:
            break
        pos = end.end()
    return "".join(out), count


def _assignment(match):
    value = match.group(2)
    if value[:1] not in ("\\", '"', "'"):
        # 引用符なしの値のうち、認証情報でないと判断できるものは残します。迷う場合は伏せます
        key = re.sub(r"[\\\"'\s=:]+$", "", match.group(1))
        is_prose = value.lower() in PROSE_VALUES
        is_count = re.fullmatch(r"[\d,._]+", value) is not None and COUNT_KEY.search(key) is not None
        # 非ASCII文字だけの値は日本語の散文として残します。英数字を含む値(パスワード等)は伏せます
        is_non_ascii_prose = any(ord(c) > 127 for c in value) and not re.search(r"[A-Za-z0-9]", value)
        if is_prose or is_count or is_non_ascii_prose:
            return match.group(0)
    return match.group(1) + "[REDACTED]"


def _authorization(match):
    if match.group(2) == "[REDACTED]":
        return match.group(0)  # 伏せ済み
    return match.group(1) + "[REDACTED]"


PERSONAL_REDACTIONS = (
    ("email", re.compile(r"(?i)(?<![\w.+-])[\w.+-]{1,120}@[\w.-]{1,180}\.[a-z]{2,24}"), "[EMAIL_REDACTED]"),
    ("url", re.compile(r"(?i)\bhttps?://[^\s<>\"']{1,2048}"), "[URL_REDACTED]"),
    ("home_path", re.compile(r"(?i)(?<!\w)/(?:home|Users)/[^/\\\s\"']{1,200}"), "/[HOME_REDACTED]"),
    ("windows_user", re.compile(r"(?i)[A-Z]:[\\/](?:Users|Documents and Settings)[\\/][^\\/\s\"']{1,200}"), "[HOME_REDACTED]"),
    ("ipv4", re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])"), "[IP_REDACTED]"),
)


class Redactor:
    """秘密情報をパターンで置換し、置換した件数を数えます。"""

    def __init__(self, personal: bool = False):
        self.counts = Counter()
        self.personal = personal

    def _substitute(self, name, pattern, replacement, text):
        changed = 0

        def counted(match):
            nonlocal changed
            result = replacement(match) if callable(replacement) else match.expand(replacement)
            if result != match.group(0):
                changed += 1
            return result

        text = pattern.sub(counted, text)
        if changed:
            self.counts[name] += changed
        return text

    def __call__(self, text: str) -> str:
        text, n = redact_private_keys(text)
        if n:
            self.counts["private_key"] += n
        for name, pattern, replacement in REDACTIONS:
            text = self._substitute(name, pattern, _authorization if name == "authorization" else replacement, text)
        text = self._substitute("assignment", ASSIGNMENT, _assignment, text)
        if self.personal:
            for name, pattern, replacement in PERSONAL_REDACTIONS:
                text = self._substitute(name, pattern, replacement, text)
        return text


def text_of(value) -> str:
    """文字列、ブロックの配列、辞書を、表示用の文字列にします。"""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(text_of(item) for item in value)
    if isinstance(value, dict):
        if isinstance(value.get("text"), str):
            return value["text"]
        return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    return str(value)


class Source:
    """1つのログファイルから読んだ事象と、読めなかった行の数。"""

    def __init__(self, label: str, path: Path):
        self.label = label
        self.path = path
        self.events = []  # (timestamp, line_no, kind, who, text)
        self.unreadable = 0
        self.unrecognized = 0
        self.skipped = Counter()
        self.encrypted_reasoning = 0
        self.pending = []  # event_msgの本文。response_itemと重複するものは後で除きます
        self.meta = {}
        self.format = Counter()


def parse_claude(src: Source, d: dict, line_no: int, ts: str, omit_thinking: bool):
    message = d["message"]
    role = d.get("type")
    content = message.get("content")
    if isinstance(content, str):
        src.events.append((ts, line_no, "message", role, content))
        return
    if not isinstance(content, list):
        src.unrecognized += 1
        return
    for block in content:
        if not isinstance(block, dict):
            src.unrecognized += 1
            continue
        kind = block.get("type")
        if kind == "text":
            src.events.append((ts, line_no, "message", role, text_of(block.get("text"))))
        elif kind == "tool_use":
            args = json.dumps(block.get("input"), ensure_ascii=False, indent=2, sort_keys=True)
            src.events.append((ts, line_no, "tool_use", str(block.get("name")), args))
        elif kind == "tool_result":
            src.events.append((ts, line_no, "tool_result", "result", text_of(block.get("content"))))
        elif kind == "thinking":
            if not omit_thinking:
                src.events.append((ts, line_no, "thinking", role, text_of(block.get("thinking"))))
        else:
            src.unrecognized += 1


def parse_codex(src: Source, d: dict, line_no: int, ts: str):
    payload = d["payload"]
    kind = payload.get("type")
    top = d.get("type")
    if top == "session_meta":
        for key in ("id", "cli_version", "cwd", "timestamp"):
            if key in payload:
                src.meta[key] = payload[key]
        if "base_instructions" in payload:
            src.skipped["base_instructions(省略)"] += 1
        return
    if top == "event_msg":
        # user_message/agent_messageはresponse_itemの重複が多いため、後で照合します
        if kind in ("user_message", "agent_message") and isinstance(payload.get("message"), str):
            role = "user" if kind == "user_message" else "assistant"
            src.pending.append((ts, line_no, "message", role, payload["message"]))
        elif kind == "sub_agent_activity":
            text = " ".join(f"{k}={payload.get(k)}" for k in ("kind", "agent_path", "model", "reasoning_effort") if payload.get(k) is not None)
            src.events.append((ts, line_no, "agent_event", "sub_agent_activity", text))
        else:
            src.skipped[f"event_msg:{kind}(表示対象外)"] += 1
        return
    if top in ("turn_context", "inter_agent_communication_metadata"):
        src.skipped[f"{top}(表示対象外)"] += 1
        return
    if top != "response_item":
        src.unrecognized += 1
        return
    if kind == "message":
        role = str(payload.get("role"))
        kind_of = "system" if role in ("developer", "system") else "message"
        src.events.append((ts, line_no, kind_of, role, text_of(payload.get("content"))))
    elif kind == "agent_message":
        parts = payload.get("content") if isinstance(payload.get("content"), list) else []
        texts = [b.get("text") for b in parts if isinstance(b, dict) and isinstance(b.get("text"), str)]
        encrypted = sum(1 for b in parts if isinstance(b, dict) and "encrypted_content" in b)
        if encrypted:
            src.encrypted_reasoning += encrypted
        who = f"{payload.get('author')} → {payload.get('recipient')}"
        src.events.append((ts, line_no, "agent_message", who, "\n".join(texts)))
    elif kind in ("function_call", "custom_tool_call"):
        args = payload.get("arguments", payload.get("input"))
        src.events.append((ts, line_no, "tool_use", str(payload.get("name")), text_of(args)))
    elif kind in ("function_call_output", "custom_tool_call_output"):
        src.events.append((ts, line_no, "tool_result", "result", text_of(payload.get("output"))))
    elif kind == "reasoning":
        if payload.get("encrypted_content"):
            src.encrypted_reasoning += 1
        summary = text_of(payload.get("summary"))
        if summary.strip():
            src.events.append((ts, line_no, "reasoning", "assistant", summary))
    else:
        src.unrecognized += 1


def read_source(label: str, path: Path, omit_thinking: bool) -> Source:
    src = Source(label, path)
    last_ts = ""
    with path.open(encoding="utf-8", errors="replace") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                d = json.loads(line)
            except ValueError:
                src.unreadable += 1
                continue
            if not isinstance(d, dict):
                src.unrecognized += 1
                continue
            ts = d.get("timestamp") if isinstance(d.get("timestamp"), str) else last_ts
            last_ts = ts
            if d.get("type") in ("user", "assistant") and isinstance(d.get("message"), dict):
                src.format["claude"] += 1
                parse_claude(src, d, line_no, ts, omit_thinking)
            elif isinstance(d.get("payload"), dict) and d.get("type") in ("response_item", "event_msg", "session_meta", "turn_context", "inter_agent_communication_metadata"):
                src.format["codex"] += 1
                parse_codex(src, d, line_no, ts)
            elif "role" in d and ("text" in d or "content" in d):
                src.format["generic"] += 1
                src.events.append((ts, line_no, "message", str(d["role"]), text_of(d.get("text", d.get("content")))))
            else:
                src.skipped[f"type={d.get('type')}(表示対象外)"] += 1
    # response_itemと同じ本文のevent_msgは重複として除き、件数だけ残します
    seen = {(ev[3], ev[4].strip()) for ev in src.events if ev[2] == "message"}
    for ev in src.pending:
        if (ev[3], ev[4].strip()) in seen:
            src.skipped["event_msgの重複(省略)"] += 1
        else:
            src.events.append(ev)
    return src


def subagent_sources(session: Path, omit_thinking: bool):
    folder = session.with_suffix("") / "subagents"
    if not folder.is_dir():
        return []
    result = []
    for path in sorted(folder.glob("agent-*.jsonl")):
        agent_type = "不明"
        try:
            meta = json.loads(path.with_suffix(".meta.json").read_text(encoding="utf-8"))
            if isinstance(meta, dict) and isinstance(meta.get("agentType"), str):
                agent_type = meta["agentType"]
        except (OSError, ValueError):
            pass
        result.append(read_source(f"子 {agent_type} ({path.stem})", path, omit_thinking))
    return result


def render_event(ev, redact) -> str:
    source_label, ts, kind, who, text = ev
    body = html.escape(redact(text))
    label = html.escape(redact(who))
    stamp = html.escape(ts or "-")
    head = f'<span class="ts">{stamp}</span> <span class="src">{html.escape(redact(source_label))}</span> <span class="who">{label}</span>'
    if kind in FOLD_KINDS or len(text) > FOLD_CHARS:
        summary = f"{kind} ({len(text):,}文字)"
        return f'<div class="ev {kind}">{head}<details><summary>{html.escape(summary)}</summary><pre>{body}</pre></details></div>'
    return f'<div class="ev {kind}">{head}<pre>{body}</pre></div>'


def load_ledger(path: Path) -> list:
    """台帳のJSON配列を読んで検証します。読めない・形式が違う場合は OSError / ValueError です。"""
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("台帳はJSON配列である必要があります")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("台帳の各要素はオブジェクトである必要があります")
    return rows


def render_ledger(rows: list, redact) -> str:
    cols = ("id", "severity", "summary", "before", "after", "files", "status")
    out = ["<h2>指摘と修正の台帳</h2><table><tr>" + "".join(f"<th>{c}</th>" for c in cols) + "</tr>"]
    for row in rows:
        out.append("<tr>" + "".join(f"<td>{html.escape(redact(text_of(row.get(c))))}</td>" for c in cols) + "</tr>")
    out.append("</table>")
    return "".join(out)


CSS = (
    "body{font-family:sans-serif;max-width:60em;margin:1em auto;padding:0 1em}"
    ".ev{border-left:4px solid #bbb;margin:.4em 0;padding:.2em .6em}"
    ".ev.message{border-color:#36c}.ev.tool_use{border-color:#c90}.ev.tool_result{border-color:#9a9}"
    ".ev.agent_message,.ev.agent_event{border-color:#3a8}.ev.thinking,.ev.reasoning{border-color:#c9c}.ev.system{border-color:#999;color:#555}"
    ".ts{color:#666;font-size:.8em}.src{font-size:.8em;background:#eee;padding:0 .3em}.who{font-weight:bold}"
    "pre{white-space:pre-wrap;word-break:break-word;margin:.2em 0}"
    "table{border-collapse:collapse}td,th{border:1px solid #bbb;padding:.2em .4em;vertical-align:top}"
    ".warn{background:#fff3cd;padding:.5em}"
)


def build(sources, ledger_rows, redact) -> str:
    events = []
    for index, src in enumerate(sources):
        for ts, line_no, kind, who, text in src.events:
            events.append((ts, index, line_no, (src.label, ts, kind, who, text)))
    events.sort(key=lambda item: item[:3])  # 時刻、入力順、行番号。時刻が同じ場合も安定した順序にします

    parts = [f"<!doctype html><html lang=\"ja\"><head><meta charset=\"utf-8\"><title>レビュー記録</title><style>{CSS}</style></head><body>"]
    parts.append("<h1>レビュー記録</h1>")
    parts.append('<p class="warn">秘密情報はパターンで置換していますが、完全ではありません。共有する前に、必ず内容を確認してください。LLMによる整形はしていません。</p>')
    parts.append("<h2>入力</h2><ul>")
    for src in sources:
        counts = ", ".join(f"{k} {v}" for k, v in src.format.items()) or "対応する行なし"
        extra = [f"事象 {len(src.events)}件", f"読めない行 {src.unreadable}件", f"形式が未確認の要素 {src.unrecognized}件"]
        if src.encrypted_reasoning:
            extra.append(f"暗号化された思考 {src.encrypted_reasoning}件(表示不可)")
        extra += [f"{k} {v}件" for k, v in src.skipped.items() if v]
        meta = " ".join(f"{k}={v}" for k, v in src.meta.items())
        line = f"{src.label} [{counts}] {meta} / " + ", ".join(extra)
        parts.append(f"<li>{html.escape(redact(line))}</li>")
    parts.append("</ul>")
    if ledger_rows is not None:
        parts.append(render_ledger(ledger_rows, redact))
    parts.append("<h2>時系列</h2>")
    for _, _, _, ev in events:
        parts.append(render_event(ev, redact))
    # 伏せ処理の件数は、本文の処理が済んだ後に確定します
    summary = ", ".join(f"{k} {v}件" for k, v in sorted(redact.counts.items())) or "置換なし"
    parts.append(f"<h2>伏せ処理の結果</h2><p>{html.escape(summary)}</p></body></html>")
    return "".join(parts)


def ensure_safe_output(path: Path) -> None:
    """Git管理対象内の未除外ファイルへのログ保存を禁止します。"""
    parent = path.resolve().parent
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent
    probe = subprocess.run(["git", "-C", str(parent), "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True, check=False)
    if probe.returncode != 0:
        return
    root = Path(probe.stdout.strip()).resolve()
    try:
        rel = str(path.resolve().relative_to(root))
    except ValueError:
        return
    # .gitignoreは変更も参照もしません。setup.shの .git/info/exclude を使います。
    info = subprocess.run(["git", "-C", str(root), "rev-parse", "--git-path", "info/exclude"],
                          capture_output=True, text=True, check=False)
    if info.returncode != 0:
        raise ValueError("Gitの除外設定を確認できません")
    exclude = Path(info.stdout.strip())
    if not exclude.is_absolute():
        exclude = root / exclude
    try:
        entries = {line.strip().rstrip("/") for line in exclude.read_text(encoding="utf-8").splitlines()
                   if line.strip() and not line.lstrip().startswith("#")}
    except OSError:
        entries = set()
    allowed = rel.startswith(".codex/review-records/") and bool({".codex", ".codex/review-records"} & entries)
    tracked = subprocess.run(["git", "-C", str(root), "ls-files", "--error-unmatch", "--", rel],
                             capture_output=True, check=False)
    if tracked.returncode == 0 or not allowed:
        raise ValueError("Git内のHTML保存先は .git/info/exclude で除外した .codex/review-records/ のみ許可します。その他はリポジトリ外へ保存してください")


def write_atomic(path: Path, data: bytes) -> None:
    """同じフォルダーの一時ファイルへ書いて置き換えます。途中で失敗しても出力先を壊しません。"""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        os.replace(tmp, path)
        os.chmod(path, 0o600)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("logs", nargs="+", type=Path, help="会話ログのJSONL")
    parser.add_argument("--out", required=True, type=Path, help="出力するHTMLのパス(親フォルダーがなければ作成します)")
    parser.add_argument("--ledger", type=Path, help="指摘と修正の台帳(JSON配列、任意)")
    parser.add_argument("--no-subagents", action="store_true", help="Claudeの子agentの記録を含めない")
    parser.add_argument("--omit-thinking", action="store_true", help="Claudeのthinkingブロックを含めない(既定は折りたたんで含める)")
    parser.add_argument("--redact-personal", action="store_true", help="メール、URL、ホームパス、IPv4も伏せる(完全な匿名化は保証されません)")
    args = parser.parse_args(argv)

    for path in [*args.logs, *([args.ledger] if args.ledger else [])]:
        if not path.is_file():
            print(f"入力が見つかりません: {path}", file=sys.stderr)
            return 2

    sources = []
    try:
        for path in args.logs:
            sources.append(read_source(path.name, path, args.omit_thinking))
            if not args.no_subagents:
                sources.extend(subagent_sources(path, args.omit_thinking))
    except OSError as exc:
        print(f"入力を読めません: {exc}", file=sys.stderr)
        return 2

    # 出力先が入力と同じ実体なら、入力ログを壊さないよう書かずに拒否します(symlinkも解決して比較)
    out_real = args.out.resolve()
    inputs = [src.path.resolve() for src in sources] + ([args.ledger.resolve()] if args.ledger else [])
    if out_real in inputs:
        print(f"出力先が入力と同じです。書き込みません: {args.out}", file=sys.stderr)
        return 2
    ledger_rows = None
    if args.ledger:
        try:
            ledger_rows = load_ledger(args.ledger)
        except (OSError, ValueError) as exc:
            print(f"台帳を読めません: {exc}", file=sys.stderr)
            return 2
    try:
        ensure_safe_output(args.out)
        args.out.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    except (OSError, ValueError) as exc:
        print(f"安全な出力先を確保できません: {exc}", file=sys.stderr)
        return 2

    redact = Redactor(personal=args.redact_personal)
    document = build(sources, ledger_rows, redact)
    try:
        # 孤立サロゲートなど符号化できない文字は?に置き換え、出力が空にならないようにします
        write_atomic(args.out, document.encode("utf-8", errors="replace"))
    except OSError as exc:
        print(f"書き込めません: {exc}", file=sys.stderr)
        return 2

    bad = sum(s.unreadable for s in sources)
    unknown = sum(s.unrecognized for s in sources)
    print(f"書き出し: {args.out} / 入力 {len(sources)}件 / 読めない行 {bad}件 / 形式が未確認の要素 {unknown}件 / 伏せ処理 {sum(redact.counts.values())}件")
    if bad or unknown:
        print(f"注意: 読めない行 {bad}件、未確認の要素 {unknown}件があります。HTMLの入力欄を確認してください。", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
