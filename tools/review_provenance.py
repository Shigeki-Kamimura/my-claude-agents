#!/usr/bin/env python3
"""レビュー依頼の来歴遮蔽(BIAS-1)、利用量の記録、Claude利用上限の検出を行う補助関数です。

外部へ問い合わせません。利用量の値は利用者が入力した自由文だけを保持し、推測や測定をしません。
"""

import datetime
import re

AUTHOR_MODELS = ("claude", "codex", "human", "unknown")
KNOWN_MODELS = ("claude", "codex")
LAYER_DIRECTION_AUTHOR = {"codex-claude-review": "codex", "claude-codex-review": "claude"}

# 行頭だけを対象にします。引用符や箇条書きの接頭辞は許します。
_PREFIX = r"^\s*(?:[>*_-]+\s*)*"
_AI_NAMES = r"(?:claude|codex|gpt|chatgpt|openai|anthropic|copilot|gemini|cursor|an?\s+ai|the\s+ai|ai|an?\s+llm|llm)"
SIGNATURE_PATTERNS = (
    re.compile(_PREFIX + r"co-authored-by\s*:", re.I),
    re.compile(_PREFIX + r"(?:🤖\s*)?generated\s+(?:with|by)\s+\[?\s*" + _AI_NAMES + r"\b", re.I),
    re.compile(_PREFIX + r"🤖"),
    re.compile(_PREFIX + r"(?:this\s+\w+\s+(?:was\s+)?)?(?:written|authored|implemented|generated|created|produced)"
               r"\s+(?:entirely\s+|partly\s+|mostly\s+)?by\s+\[?\s*" + _AI_NAMES + r"\b", re.I),
)
_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")


def strip_author_signatures(text):
    """依頼本文や引用したPR/commit本文から、作成ツールの署名行を除きます。

    fenced code block内は変更しません(コードや差分を保つため)。このため、
    コードブロックに貼り付けた署名は除かれません。文体の痕跡も隠せません。
    戻り値は (整形後の本文, 除いた行数) です。
    """
    kept, removed, fence = [], 0, None
    for line in text.splitlines(keepends=True):
        marker = _FENCE.match(line)
        if marker:
            if fence is None:
                fence = marker[1][0]
            elif marker[1][0] == fence:
                fence = None
            kept.append(line)
            continue
        if fence is None and any(pattern.search(line) for pattern in SIGNATURE_PATTERNS):
            removed += 1
            continue
        kept.append(line)
    return "".join(kept).strip(), removed


def model_family(*values):
    """モデル名やplatform名から claude / codex / unknown を決めます。最初に判定できた値を使います。"""
    for value in values:
        lowered = str(value or "").lower()
        if re.search(r"claude|sonnet|opus|haiku|anthropic", lowered):
            return "claude"
        if re.search(r"gpt|codex|openai|chatgpt|\bo[1-9]\b", lowered):
            return "codex"
    return "unknown"


def effective_author_model(config):
    """記録済みのauthor_model、なければ方向から定まる実装側を返します。(値, 出典)"""
    declared = config.get("author_model")
    if declared in AUTHOR_MODELS:
        return declared, "declared"
    implied = LAYER_DIRECTION_AUTHOR.get(config.get("direction"))
    return (implied, "direction") if implied else ("unknown", "none")


def review_independence(author, reviewer):
    """同一モデルの確認は self_check です。claude/codex以外が絡む場合は断定せず unknown です。"""
    if author in KNOWN_MODELS and reviewer in KNOWN_MODELS:
        return "self_check" if author == reviewer else "cross_model"
    return "unknown"


def independence_record(config, evidence):
    """検証済みの判定欄のinvocation_evidenceから、host側の来歴記録を作ります。判定欄の11項目は変えません。"""
    author, source = effective_author_model(config)
    reviewer = model_family(evidence.get("model"), evidence.get("platform"))
    return {"author_model": author, "author_model_source": source, "reviewer_model": reviewer,
            "review_independence": review_independence(author, reviewer)}


# 利用量: 利用者入力の自由文だけを記録します。測定や問合せはしません。
USAGE_MAX_CHARS = 200
MANY_FILES = 30
VERY_MANY_FILES = 60


def usage_record(reading, direction, layers):
    """claude_usage_before(利用者の自由文)または claude_usage: unknown を返します。"""
    needs = direction == "codex-claude-review" and (len(layers) >= 2 or "adv" in layers)
    if reading is None:
        return {"claude_usage": "unknown"} if needs else {}
    text = reading.strip()
    if not text or len(text) > USAGE_MAX_CHARS or any(ord(char) < 32 or ord(char) == 127 for char in text):
        raise ValueError(f"claude-usage-beforeは1行{USAGE_MAX_CHARS}字以内の自由文です")
    return {"claude_usage": "unknown"} if text.lower() == "unknown" else {"claude_usage_before": text}


def estimate_cost_class(layers, changed_path_count):
    """層数と変更pathの数からの目安です。測定値ではなく、model/effortも変えません。"""
    if ("adv" in layers or len(layers) >= 3 or changed_path_count >= VERY_MANY_FILES
            or len(layers) >= 2 and changed_path_count >= MANY_FILES):
        return "high"
    if len(layers) >= 2 or changed_path_count >= MANY_FILES:
        return "medium"
    return "low"


# 利用上限: 失敗した終了だけを対象にし、判定欄を持つ正常な本文は対象にしません。
_STRICT_LIMIT = (
    re.compile(r"hit your[^\n.]{0,60}limit", re.I),
    re.compile(r"usage limit reached", re.I),
    re.compile(r"rate_limit_error", re.I),
)
_STDERR_LIMIT = _STRICT_LIMIT + (re.compile(r"\b429\b"), re.compile(r"too many requests", re.I),
                                 re.compile(r"rate[ _-]?limit", re.I))
_RESET = re.compile(r"resets?\s+(?:at\s+)?([^\n·|]{1,60})", re.I)
_EPOCH = re.compile(r"limit reached\|(\d{9,13})", re.I)


def _reset_hint(text):
    epoch = _EPOCH.search(text)
    if epoch:
        seconds = int(epoch[1])
        seconds = seconds / 1000 if seconds > 10 ** 11 else seconds
        stamp = datetime.datetime.fromtimestamp(seconds, datetime.timezone.utc).isoformat()
        return f"epoch {epoch[1]} ({stamp})"
    reset = _RESET.search(text)
    return reset[1].strip() if reset else None


def detect_rate_limit(final_text, api_status, stderr_tail, failed):
    """Claudeの利用上限シグナルを検出します。failedでなければ検出しません。

    final_text: 最終resultの本文。api_status: 最終resultのapi_error_status。
    stderr_tail: 標準エラーの末尾。failed: 非0終了、is_error、またはresult欠落/判定欄なし。
    """
    if not failed:
        return None
    candidates = [("result", final_text or "", _STRICT_LIMIT), ("stderr", stderr_tail or "", _STDERR_LIMIT)]
    if api_status == 429:
        return {"signal": "api_error_status=429", "reset_hint": _reset_hint(final_text or "") or _reset_hint(stderr_tail or "")}
    for source, text, patterns in candidates:
        for pattern in patterns:
            hit = pattern.search(text)
            if hit:
                return {"signal": f"{source}: {hit[0][:80]}", "reset_hint": _reset_hint(text) or _reset_hint(final_text or "")}
    return None
