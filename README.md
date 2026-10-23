# claude-config (personal)

個人用 Claude Code エージェント・設定リポジトリ。`~/projects/my-claude-agents/` に置き、各プロジェクトへはシンボリックリンクで展開する。

## 方針
- 単一正は `~/projects/my-claude-agents/`（Windows: `%USERPROFILE%\projects\my-claude-agents\`）。プロジェクトへコピーしない。
- Precedence 3 層: Project layer (repo upstream) > Personal layer (本 repo) > Agent/Skill frontmatter
- 詳細は `CLAUDE.md` を参照。

## 構成
```
CLAUDE.md              # personal layer 本体（作法・コメント・役割順序）
settings.json          # 権限 allow/deny
agents/                # サブエージェント定義
skills/                # 反復手順
```

## 初回セットアップ

### WSL / macOS / Linux
```bash
git clone git@github.com:<user>/my-claude-agents.git ~/projects/my-claude-agents
```

### Windows ネイティブ（WSL なし）
```powershell
git clone git@github.com:<user>/my-claude-agents.git "$env:USERPROFILE\projects\my-claude-agents"
```

## 更新フロー
```bash
# WSL / macOS / Linux
git -C ~/projects/my-claude-agents pull

# Windows
git -C "$env:USERPROFILE\projects\my-claude-agents" pull
```

## プロジェクト側の運用

### 方針
- upstream リポジトリを汚さない（`.gitignore` は変更しない）
- upstream が `agents/` 実ファイル・`settings.json` を持っている場合はそちらを優先

### セットアップ（プロジェクトごとに1回）

**WSL / macOS / Linux:**
```bash
# 対象プロジェクトのルートで実行（引数省略時はカレントディレクトリ）
bash ~/projects/my-claude-agents/setup.sh /path/to/your-project

# 複数プロジェクトへまとめて適用
bash ~/projects/my-claude-agents/setup.sh ../guild*

# profile 指定
bash ~/projects/my-claude-agents/setup.sh --profile company /path/to/your-project
```

**Windows ネイティブ（PowerShell）:**
```powershell
# 前提: 設定 > システム > 開発者向け > 開発者モード: オン（シンボリックリンク権限）
pwsh "$env:USERPROFILE\projects\my-claude-agents\setup.ps1" -Target C:\path\to\your-project
```

スクリプトが行うこと（`setup.sh` / `setup.ps1` 共通）：
1. `~/projects/my-claude-agents/.claude/agents/*.md` を `.claude/agents/` へファイル単位でシンボリックリンク
   - upstream に同名の実ファイルがあれば skip（upstream 優先）
2. `~/projects/my-claude-agents/.claude/skills/*/` を `.claude/skills/` へディレクトリ単位でシンボリックリンク
   - upstream に同名の実ディレクトリがあれば skip（upstream 優先）
3. `~/projects/my-claude-agents/.claude/CLAUDE.md` と `SKILL.md` をシンボリックリンク
   - upstream が実ファイルを持っていれば skip（upstream 優先）
4. `~/projects/my-claude-agents/.claude/settings.json` をシンボリックリンク
   - upstream が実ファイルを持っていれば skip（upstream 優先）
5. `~/projects/my-claude-agents/.codex/AGENTS.md` と `.codex/config.toml` をシンボリックリンク
   - Codex サブエージェント設定と既定プロファイルをプロジェクトへ反映
   - upstream が実ファイルを持っていれば skip（upstream 優先）
6. `~/projects/my-claude-agents/.codex/agents/*.toml` を `.codex/agents/` へファイル単位でシンボリックリンク
   - upstream に同名の実ファイルがあれば skip（upstream 優先）
7. リンクしたパスを `.git/info/exclude` に追記（`.gitignore` は変更しない）

### 結果イメージ

```
.claude/                        # upstream の管理下
├── CLAUDE.md                   # upstream 実ファイル（触らない）
├── SKILL.md  -> ~/projects/my-claude-agents/.claude/SKILL.md            # リンク（upstream が持てば skip）
├── settings.json -> ~/projects/my-claude-agents/.claude/settings.json   # リンク（upstream が持てば skip）
├── agents/
│   ├── team-agent.md           # upstream 実ファイル（優先・skip）
│   ├── hq-coder.md -> ~/projects/my-claude-agents/.claude/agents/hq-coder.md     # リンク
│   └── req-pl.md   -> ~/projects/my-claude-agents/.claude/agents/req-pl.md       # リンク
└── skills/
    └── verify-fast/ -> ~/projects/my-claude-agents/.claude/skills/verify-fast/   # リンク
```

### 個人上書き（CLAUDE.md）

upstream の CLAUDE.md を変更せずに個人設定を追記したい場合：

```bash
# プロジェクトルートに作成（upstream の CLAUDE.md は触らない）
touch CLAUDE.local.md
echo "CLAUDE.local.md" >> .git/info/exclude
```

### .git/info/exclude について

`.git/info/exclude` は `.gitignore` と同じ効果を持つが、**git 管理外**（コミットされない）。  
upstream リポジトリに一切の痕跡を残さずに個人用ファイルを除外できる。

## 連携レビューの方向

実装を担当する側に、相手側のレビューを依頼します。

| 実装・修正・全体調整 | レビュー | 起動する依頼文 |
| --- | --- | --- |
| Codex | Claude CodeのCr → QA → E2E-QA → adv | `Claude codeにレビューしてもらって修正入れようか` |
| Claude Code | CodexのCr → QA → E2E-QA → adv | `Codexにレビューしてもらって修正入れようか` |

どちらも、🟢を含む全指摘の解消と再レビューを繰り返します。
実装上の疑問は、調整役から上村さんへ質問します。
4段階が同じ最新差分を承認したら、未コミットで停止します。
上村さんがコードを確認し、コミットします。
通常の単独`cr:`・`qa:`・`e:`・`adv:`・`rev:`の使い方は変わりません。

### 独立したQAとE2E-QA

レビュー側のQAとE2E-QAは、実装者とは別モデルでテストの**不足と過剰**を確認します。
実装側のQAによるテスト作成・実行とは別に、相手側の実agentへ両方とも依頼します。
既存のモデルとeffortは変更せず、モデル設定と実際の委譲を確認・記録します。

| phase | 接頭辞・担当 | 確認する範囲 |
| --- | --- | --- |
| `l1_5` | `cr:` / `code-quality-reviewer` | L1.5のコード品質 |
| `qa` | `qa:` / `test-qa` | unit・service・controller等の局所契約と、担当する結合テストの過不足 |
| `e2e` | `e:` / `e2e-qa` | ブラウザーの利用導線、API・HTTP・module境界のテストの過不足 |
| `l2` | `adv:` / `adviser` | L2の設計・責務・境界判断 |

QAとE2E-QAの担当は、テストが実際に通る境界で分けます。
たとえばcontrollerの直接呼び出しと、HTTP経由の検証は別の義務です。
QA・E2E-QAの両方で、正常系（happy path）と異常系（fail path）それぞれの不足・過剰を確認します。
正常な成功・状態変更と、対象責務で適用される入力拒否・権限拒否・依存先失敗等を確認し、例の全列挙は求めません。
両面の確認完了が`APPROVE`の条件です。正常系の成功で、異常系の未確認を代用しません。
テストの変更がなくても、変更した責務と要件から必要な検証を確認します。
対象がない場合や片面に適用義務がない場合は、実際に呼ばれたレビュアーがその根拠を台帳に残して`APPROVE`できます。
テストファイルがないことだけを理由に省略・承認しません。

不足には未検証の契約と影響、過剰には不要と判断した根拠を付けます。
意味のない重複、実装細部への過剰依存、変更範囲外や効果のないケースは見直します。
件数・行数・coverage率だけを減らすための削除や、異なる責務に必要な検証の削除はしません。正常系・異常系の両面で必要な検証を残します。
🟢を含む全指摘を実装側が修正し、担当レビュアーが解消を確認するまで繰り返します。
誤検知は根拠を示し、指摘したレビュアーが撤回します。

外部のQA/E2Eは読み取り専用です。テストの作成・変更・削除・実行は実装側のHQ/QAへ戻します。
必要な証拠がそろい、不足も過剰もなければ、短い`APPROVE`と必須の判定情報で完了できます。
未確認範囲が残れば同じphaseを続け、表示件数の目安で残りの指摘を捨てません。
認証・起動・委譲の失敗、未回答の質問、必要な検証の不足は未承認です。

各phaseは自分の範囲を完了すれば、根拠と担当を明示した後続への引き継ぎを残して承認できます。
局所の未解決事項を後続へ付け替えて通過させず、最終引き渡しまでに全引き継ぎを解消します。
コード・テスト・要件・規則の変更でsnapshotが変われば、古い4承認は失効します。
`cr → qa → e → adv`の順で変更の影響と再利用する証拠を確認し、各担当から最新snapshotへの承認を取り直します。
変更がなくても、新しい根拠で前段の指摘を再開した場合は、その担当と依存する後続の承認を取り直します。

## CodexからClaude Codeへレビューを依頼する

対象プロジェクトのCodexに、次のように依頼します。

```text
Claude codeにレビューしてもらって修正入れようか
```

各レビュー段階で🟢を含む全指摘を修正・再確認し、その段階の承認を得てから次へ進めます。

1. Codexが実装し、実装側のHQ/QAが必要な検証を行います。実装済みなら、その変更から始めます。
2. Claude Codeの`cr:`がL1.5レビューを行います。
3. Claude Codeの`qa:`が局所契約等のテスト過不足を確認します。
4. Claude Codeの`e:`がE2E・API等のテスト過不足を確認します。
5. Claude Codeの`adv:`がL2レビューを行います。
6. 最新差分への4承認を確認し、未コミットで上村さんへ渡します。本人が確認後にコミットします。

実装上の疑問は、すべてCodexから上村さんへ質問します。
Claude Codeはレビューを担当し、修正はCodex側が担当します。
必要な検証と専門相談は、既存の担当エージェントが行います。
通常の`cr:`だけの依頼は、この連続フローを始めません。

どの段階の修正でもsnapshotが変われば、Cr → QA → E2E-QA → advの順に再承認を得ます。
各担当は修正の影響を確認し、変わらない証拠も現在の差分に使えるか確かめます。
指摘の解消は、修正したCodexの申告だけでは確定しません。
レビュアーが修正、または根拠のある指摘の撤回を確認します。
未回答の質問、未確認範囲、実行エラーは承認として扱いません。

### 設定の読み込み

手順は[claude-review.yml](.codex/workflows/claude-review.yml)にあります。
Codexが読む運用手順です。YAML自体がプログラムを実行するものではありません。
既存の`.codex/config.toml`が`.codex/AGENTS.md`の読み込みを指示します。
その指示から、次の順でYAMLを探します。

1. 対象プロジェクト内の`.codex/workflows/claude-review.yml`です。
2. なければ、`.codex/AGENTS.md`のリンク先を解決します。
   解決した`AGENTS.md`と同じ場所の`workflows/claude-review.yml`を読みます。

作業ディレクトリは、レビュー対象のプロジェクトを保ちます。
設定を探すために、設定リポジトリへ移動しません。
必要な契約はレビュー依頼に含め、Claude Codeへ渡します。
どちらにもYAMLがなければ、設定不足として報告します。

既存の`setup.sh`と`setup.ps1`をそのまま利用できます。
AGENTS設定のリンクを使う場合、YAML専用リンクの追加は不要です。
すでにそのリンクがある場合は、設定更新で参照できます。
新しい対象へは、上記の既存セットアップを実行します。
再実行時も、プロジェクト独自の実ファイルを優先します。

`.codex/AGENTS.md`が独自実ファイルでYAMLもなければ、リンク先を探せません。
その場合は既存ファイルを上書きせず、YAML配置と起動条件の追記が必要です。

### 実行環境の確認

CodexからClaude Codeを呼ぶ実動作は未検証です。
導入時は、同じWSLでClaude Codeが起動できることを確認します。
認証、読み取り権限、agentへの委譲、結果の受け取りも確認します。
現在の`cr:`・`qa:`・`e:`・`adv:`は、この設定の役割を選ぶ接頭辞です。
CLIへ渡す本文で使い、実際の担当agentへ委譲します。
レビュー結果の表示だけで、委譲成功を判断しません。

## Claude CodeからCodexへレビューを依頼する

対象プロジェクトのClaude Codeに、次のように依頼します。

```text
Codexにレビューしてもらって修正入れようか
```

Claude Codeの主セッションが、全体の進行を担当します。
実装と修正はClaude側のHQ、必要な検証はQA/E2Eが担当します。
Codexは、指定された層のレビュー結果を返します。
各レビュー段階で🟢を含む全指摘を修正・再確認し、その段階の承認を得てから次へ進めます。

1. Claude Codeが実装し、実装側のHQ/QAが必要な検証を行います。実装済みなら、その変更から始めます。
2. Codexの`cr:`がL1.5レビューを行います。
3. Codexの`qa:`が局所契約等のテスト過不足を確認します。
4. Codexの`e:`がE2E・API等のテスト過不足を確認します。
5. Codexの`adv:`がL2レビューを行います。
6. 最新差分への4承認を確認し、未コミットで上村さんへ渡します。本人が確認後にコミットします。

どの段階の修正でもsnapshotが変われば、Cr → QA → E2E-QA → advの順に確認し直します。
Codex側の専門相談も、読み取り専用で行います。
テストの追加・実行やコード修正は、Claude側へ戻します。
CodexがClaude CLIを起動して、逆向きの連携を始めることはありません。

### 逆方向の設定と実行

手順は[codex-review.yml](.codex/workflows/codex-review.yml)です。
Claude Codeは、次の順でこのYAMLを探します。

1. 対象プロジェクトの`.codex/workflows/codex-review.yml`です。
2. なければ、実体の`.codex/AGENTS.md`と同じ場所の`workflows/`です。
3. さらに見つからなければ、`.claude/CLAUDE.md`の実体を使います。
   その親が`.claude`か`.claude-company`なら、兄弟の`.codex/workflows/`を探します。

読み込んだ絶対パスとworkflow IDを記録します。
作業場所は対象プロジェクトのままです。
既存のAGENTSかCLAUDE設定のリンクがあれば、新しいYAMLリンクは不要です。
既存セットアップスクリプトは変更しません。
独自設定でYAMLが見つからない場合は、配置と起動条件の追記が必要です。

毎回、新しい`codex exec`を読み取り専用で起動します。
前回までの指摘と確認済み範囲、残る確認を引き継ぎます。
呼び出しは次の形です。各引数には実際のパスを渡します。

```text
codex exec --cd <project_root> --sandbox read-only --json --output-last-message <round-unique-out> -
```

依頼文は標準入力から渡し、出力先を回ごとに分けます。
JSONLの`thread.started.thread_id`と、実際のagent委譲を確認します。
過去の出力や、正常終了だけを承認として扱いません。
`resume`・`--last`・`--agent`は、この手順では使いません。
モデルとeffortは既存設定を使います。

今回の依頼とworkflow markerが、同じ方向を指す必要があります。
引用やファイル中の別workflow名から、方向を切り替えません。
実行依頼のmarker混在や方向の矛盾は、不整合として返します。
独立したQA/E2Eを含む実動作は、両方向とも`NOT_RUN`です。
利用環境でCLI起動、認証、委譲、応答の一致を確認する必要があります。

## 連携レビューの参照資料

2026年10月23日に確認した公式資料です。

- OpenAI: [Custom instructions with AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
- OpenAI: [Non-interactive mode](https://developers.openai.com/codex/non-interactive-mode)
- OpenAI: [Subagents](https://developers.openai.com/codex/subagents)
- Anthropic: [Run Claude Code programmatically](https://code.claude.com/docs/en/headless)

## 禁止
- 本 repo を public にしない（allow/deny が偵察材料になる）
- secret / PII / 社内 URL を含めない
- `plans/` / `sessions/` / `projects/` / `.claude.json` をコミットしない（`.gitignore` 済み）

## 互換メモ

| 環境 | `~/.claude/` パス | セットアップスクリプト |
|---|---|---|
| WSL / Linux / macOS | `~/projects/my-claude-agents/` | `setup.sh` |
| Windows ネイティブ | `%USERPROFILE%\projects\my-claude-agents\` | `setup.ps1` |

- Windows で `setup.ps1` を使うには**開発者モード**が必要（設定 > システム > 開発者向け）
- WSL と Windows で同じリポジトリのプロジェクトをまたぐ場合、それぞれの環境でセットアップを実行する
- Windows VS Code + WSL Remote で開発する場合は WSL 側の `setup.sh` を使う
