# claude-config (personal)

個人用 Claude Code エージェント・設定リポジトリ。`~/projects/my-claude-agents/` に置く。Claude Code / Copilot はリンク、Codex の TOML は実ファイルコピーで展開する。

## 方針
- 単一正は `~/projects/my-claude-agents/`（Windows: `%USERPROFILE%\projects\my-claude-agents\`）。Codex TOML のみ実ファイルで展開し、更新は `setup` で同期する。
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

### Codex定義の統合と既存環境の移行

Codexの定義は、正式名ごとに1ファイルへ統合しています。
短縮名は入力用のaliasとして残し、起動時に正式名へ変換します。

| 入力alias | 正式名・定義ファイル |
| --- | --- |
| `h:` / `hq:` | `hq-coder` / `hq-coder.toml` |
| `p:` / `pl:` | `req-pl` / `req-pl.toml` |
| `q:` / `qa:` | `test-qa` / `test-qa.toml` |
| `rp:` / `plan:` | `review-planner` / `review-planner.toml` |

担当を明示した`hq`・`pl`・`qa`の依頼も、同じ正式名へ変換します。
alias用のTOMLや同名定義のシンボリックリンクは追加しません。

設定の更新後は、導入済みの各プロジェクトでsetupを再実行してください。
Codexの新しい `agents/*.toml` は自動検出・追加されます。既存の管理コピーも、手動編集がなければ更新されます。
原本から消えたTOMLは誤削除を防ぐため自動削除しません（旧名 `hq/pl/qa` の管理リンクだけは削除します）。

```bash
git -C ~/projects/my-claude-agents pull --ff-only origin exp/xml-agents
bash ~/projects/my-claude-agents/setup.sh --profile company /path/to/your-project
```

Windowsネイティブでは、PowerShell版を再実行します。

```powershell
git -C "$env:USERPROFILE\projects\my-claude-agents" pull --ff-only origin exp/xml-agents
pwsh "$env:USERPROFILE\projects\my-claude-agents\setup.ps1" -Profile company -Target C:\path\to\your-project
```

profileは現在使用中の`personal`または`company`に合わせます。
setupは、この設定リポジトリを参照する旧`hq.toml`・`pl.toml`・`qa.toml`のリンクを除去します。
リンク先が削除済みでも、管理元が一致すれば移行できます。
別の設定を参照するリンクや、プロジェクト独自の実ファイルは保持します。
管理下の実ファイルは `.git/info/codex-setup-managed.tsv` に前回同期時のSHA-256を記録し、手動変更があれば上書きしません。
すでに手動で実ファイル化したTOMLは、原本と完全一致する場合に限り管理下へ引き継ぎます。
Gitで追跡中のファイルは、リンクも含めて一切上書きしません。
`CONFLICT preserved`が出た場合は、残った定義を確認してください。`SKIP upstream`は管理外ファイルの保護です。
`.gitignore` は使わず、対象リポジトリの `.git/info/exclude` と `.git/info/` 内の管理履歴だけを更新します。
展開後は新規Codexセッションで正式名の読み込みと起動を確認します。

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
5. `~/projects/my-claude-agents/.codex/AGENTS.md` をシンボリックリンク、`.codex/config.toml` を実ファイルコピーで展開
   - 旧管理リンクは実ファイルへ移行。プロジェクト独自設定や追跡済みファイルは保持
6. `~/projects/my-claude-agents/.codex/agents/*.toml` を `.codex/agents/` へ実ファイルコピーで同期
   - 新しい定義も次回 `setup` で検出。管理コピーの更新は前回同期のSHA-256で保護
   - 旧管理リンクはコピーへ移行し、管理外ファイルは保護
7. 配置したパスを `.git/info/exclude` に登録し、管理履歴を `.git/info/codex-setup-managed.tsv` に保存（`.gitignore` は変更しない）

### Codex Desktop（Windowsアプリ + WSLエンジン）の注意点

プロジェクトごとの `.codex/config.toml` と `.codex/agents/*.toml` は、WSL側の `setup.sh` で実体コピーにします。
Desktopの `CODEX_HOME/agents/` へ定義をコピーする `sync_codex_desktop.py` は別の手順です。そちらを実行しても、プロジェクト側の古いシンボリックリンクは自動解消されません。
コピーした定義の内容は、原本更新後に `setup` を再実行するまで更新されません。追加・変更のあとには、新しいCodexスレッドで起動を確認してください。

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
| Codex | Claude Code(基本は単層。四層のQA → E2E-QA → Cr → advは明示した場合のみ) | `Claude codeにレビューしてもらって修正入れようか` |
| Claude Code | CodexのQA → E2E-QA → Cr → adv | `Codexにレビューしてもらって修正入れようか` |

どちらも、全指摘の解消と再レビューを繰り返します(どちらの方向も🔴🟡と🟢Lowが対象で、🟢Infoは指摘ではありません)。
実装上の疑問は、調整役から上村さんへ質問します。
四層モードでは、4段階が同じ最新差分を承認したら、未コミットで停止します。Claude Codeの単層モードは、その層の承認で止まり、最終承認ではありません。
上村さんがコードを確認し、コミットします。
通常の単独`cr:`・`qa:`・`e:`・`adv:`・`rev:`の使い方は変わりません。

### 独立したQAとE2E-QA

レビュー側のQAとE2E-QAは、実装者とは別モデルでテストの**不足と過剰**を確認します。
実装側のQAによるテスト作成・実行とは別に、相手側の実agentへ両方とも依頼します。
既存のモデルとeffortは変更せず、モデル設定と実際の委譲を確認・記録します。

| phase | 接頭辞・担当 | 確認する範囲 |
| --- | --- | --- |
| `qa` | `qa:` / `test-qa` | unit・service・controller等の局所契約と、担当する結合テストの過不足 |
| `e2e` | `e:` / `e2e-qa` | ブラウザーの利用導線、API・HTTP・module境界のテストの過不足 |
| `l1_5` | `cr:` / `code-quality-reviewer` | L1.5のコード品質 |
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
🟢Lowを含む全指摘を実装側が修正し、担当レビュアーが解消を確認するまで繰り返します(どちらの方向も🟢Lowまで。Infoは指摘ではありません)。
誤検知は根拠を示し、指摘したレビュアーが撤回します。

CodexからClaudeへのレビューでは、QA/E2Eはテストの過不足とCodexの実行証拠を確認します。テスト実行と修正はCodexが担当します。
CR/ADVはGit・読取・検索で確認し、アプリ・テスト・ビルド等は実行しません。
逆方向の外部Codexレビューは、既存の読み取り専用・実行禁止を保ちます。
必要な証拠がそろい、不足も過剰もなければ、短い`APPROVE`と必須の判定情報で完了できます。
未確認範囲が残れば同じphaseを続け、表示件数の目安で残りの指摘を捨てません。
認証・起動・委譲の失敗、未回答の質問、必要な検証の不足は未承認です。

各phaseは自分の範囲を完了すれば、根拠と担当を明示した後続への引き継ぎを残して承認できます。
局所の未解決事項を後続へ付け替えて通過させず、最終引き渡しまでに全引き継ぎを解消します。
コード・テスト・要件・規則の変更でsnapshotが変われば、古い4承認は失効します。
`qa → e2e → cr → adv`の順で変更の影響と再利用する証拠を確認し、各担当から最新snapshotへの承認を取り直します。
変更がなくても、新しい根拠で前段の指摘を再開した場合は、その担当と依存する後続の承認を取り直します。

### Claude Codeの実行権限

- 自律的なレビューでは、型チェック・テスト・CIを自動実行しません。
- Codexから依頼されたレビューでは、Claudeはレビュー専用です。実行と修正はCodexが担当します。
- ユーザーが通常のClaude Codeセッションへ直接指示した場合は、型チェック・lint・build・テスト・Playwright・CIを、利用可能な権限で実行できます。
- Codexが起動した制限付きセッションの権限は、途中の指示で広げません。直接実行する場合は通常のClaudeセッションを使います。

## CodexからClaude Codeへレビューを依頼する

対象プロジェクトのCodexに、Claude Codeを名指しして依頼します。基本は単層モードで、層名で動きが決まります。

```text
Claude codeにレビューしてもらって修正入れようか
```

| 依頼の書き方 | 動き |
| --- | --- |
| 層名なし(上の例。`コードレビュー`、`ローカル`などの一般語は層名ではありません) | `qa`を単層で実行し、続けて`cr`を単層で実行します(並列にしません)。 |
| 層名あり(`cr` / `L1.5`、`qa`、`e2e`、`adv` / `L2`) | その層だけを単層で実行し、先へ進みません。 |
| `四層`、`全層`、`crからadvまで`のような範囲を示す表現 | 四層モードです。`qa → e2e → cr → adv`の順に、新規の初回として実行します。 |
| `crとadv`のような列挙 | 定義がないため、上村さんへ1つ質問します。 |

層名がない依頼の進め方は、次のとおりです。
1. Codexが実装し、実装側のHQ/QAが必要な検証を行います。実装済みなら、その変更から始めます。
2. Claude Codeの`qa:`が局所契約等のテスト過不足を確認します。
3. Codexが同じチャットの記録で、`qa`の単層APPROVEを確認できた場合だけ、`e:`(E2E・API等のテスト過不足)へ進みます。
4. Claude Codeの`cr:`がL1.5レビューを行います。
5. Codexが同じチャットの記録で、`cr`の単層APPROVEを確認できた場合だけ、`adv:`(L2レビュー)へ進みます。
6. 確認できなければ次へ進まず、不足を報告して上村さんへ1つ質問します。

確認する記録は、`mode=single-layer phase=<直前のphase>`を含むWorkflow Result、APPROVE、COMPLETE、現在のsnapshot一致です。承認後に変更があれば進みません。
実行する順は`qa`、`e2e`、`cr`、`adv`で、四層の順と同じ向きです。

各層は、🔴🟡と🟢Lowの全指摘を修正・再確認し、その層の承認を得てから次へ進めます。
軽微な🟢は、LowとInfoに分けます。Lowは指摘で、IDを付けて閉鎖まで追跡し、1層・1回のレポートで重要度の高いものから最大5件です。Infoは指摘ではなく、ID・追跡・修正・再レビューが不要で、1行ずつ簡潔に書くか省略できます。超える分は重要度の低いものをInfoにします。一度Infoと分類した所見は、再レビューでも、Lowが5件に満たなくても、Lowへ格上げも付け替えもしません。再レビューで新たに見つけた根拠付きのLowは、新しい指摘として出せます(最大5件に含まれ、再レビューの上限規則の対象です)。🔴🟡、質問、handoff、必須証拠の欠落は、LowやInfoに下げて隠しません。
単層の承認は、その層と確認したsnapshotにだけ有効です。承認がいくつそろっても、四層の最終承認や引渡し可にはなりません。
四層モードが必要なら、その旨を明示して新規の初回として依頼します。単層の結論は、承認の代わりにならず、Supplied証拠として添えるだけです。

実装上の疑問は、すべてCodexから上村さんへ質問します。
Claude Codeはレビューを担当し、修正はCodex側が担当します。
必要な検証と専門相談は、既存の担当エージェントが行います。
Claudeを名指ししない`cr:`だけの依頼は、この流れを始めません。

四層モードで、どの段階の修正でもsnapshotが変われば、QA → E2E-QA → Cr → advの順に再承認を得ます。単層では、その層だけを再確認します。
各担当は修正の影響を確認し、変わらない証拠も現在の差分に使えるか確かめます。
指摘の解消は、修正したCodexの申告だけでは確定しません。
レビュアーが修正、または根拠のある指摘の撤回を確認します。
未回答の質問、未確認範囲、実行エラーは承認として扱いません。

### 単層承認と他層への引継ぎ

単層は、自層の確認が完了し、指摘・質問・未確認がゼロなら承認します。
必要な証拠・必須相談と、その層のnative判定条件も満たす必要があります。
他層の独立した引継ぎだけが残る場合、`decision: APPROVE`として未了事項を保持します。
CRの`L1.5_APPROVE_WITH_NOTES`も、残りが担当自身の根拠付き引継ぎだけなら対象です。
自層の判断に必要な証拠や回答待ちは、引継ぎへ移して承認しません。
単層承認で他層の義務は閉じず、最終引渡しでは全必須引継ぎの解消を待ちます。
判定欄が矛盾する場合は、元の担当が訂正します。Codexが書き換えることはありません。

CRの引継ぎ件数は上限を設けません。既存の4項目と台帳のID・状態を保ちます。
関連する問いをまとめても別の義務を落とさず、再開だけで範囲を広げません。
これは調査範囲の拡大や、追加レイヤーの起動を指示するものではありません。

### レビューのモデルと読み込み量

Claudeの親はSonnet / medium、L2担当はOpus 5.5 / highを使います。
L1.5、QA、E2E、React/Nest等は既存のSonnet設定を使います。
親の設定を子のモデルへ上書きしません。利用者の明示指定を優先します。
Opus 5.5を使えない場合は、L2の承認を保留します。

初回は必要な規則と対象全体を確認します。
再レビューは同じ担当で、修正差分と影響を確認します。
不変資料は読み直さず、新しいテスト結果と質問への回答を渡します。
専門相談は必要な質問をまとめ、同じ責務の調査を重複させません。
確認範囲、必須相談、🟢Lowまでの解消条件は減らしません。
設定の短縮だけでは、実際の消費量や精度の同等性は証明できません。

### Codexの資料読みと指摘の根拠

レビューの目的は、変更が受入条件と必須規則を満たすかの判断です。
対象操作・出典・期待する変更前後を、既存台帳へ`Review objective`として記録します。
確認IDと専門相談を、その目的または必須規則・未解決IDに対応させます。
終了時に目的と全確認範囲を照合し、未確認と担当を残します。
必読資料、反証、独立レビュー、QA/E2E、React/Nestの必須相談は維持します。
目的を短くするために、必要な経路や既存の未解決事項を落としません。

Codexは、資料の版と読み済みの節を既存の確認記録に残します。
同じ資料は初回の途中でも再利用し、引用のための全文再読を避けます。
必読の設計書と規則、例外、専門担当自身の初回確認は残します。
長い資料は節ごとに分け、各呼出しと集約結果の出力上限を守ります。
独立した節は`read_review_source.py --batch`でまとめて取得します。
既定の合計上限は12,000文字です。ファイルごとの上限ではありません。
各結果の`next_line`を使い、不足した必読範囲だけを続けます。
出力が切れた場合は、不足した範囲だけを取り直します。

AdviserとReact/Nestは、通常経路と意味のある失敗経路を優先します。
指摘前に、変更前後、実際に届く入力、反証、期待する結果を確認します。
入力や要件が未確認のものは、質問として残します。
条件付きのLow指摘や修正要求にはしません。必須規則の違反は別途判定します。
共通処理の変更は、他の正当な入力元と利用先への波及も確認します。
文言や状態の変更は、操作全体で利用者に伝わる意味を確認します。
見出し・バッジ・通知等は、各自の役割と要件で照合します。
異なる役割の文言を一律にそろえたり、全画面を調べたりはしません。
既存の確認記録へ結論をまとめ、資料の読み足しは必要な範囲に絞ります。
モデルと権限は維持します。効果は次の実行ログで確認します。

Adviserは最小限の経路確認後、専門担当ごとの質問をまとめます。
質問ID、期待する契約、対象範囲、担当、足りない証拠を台帳へ残します。
Reactは状態・再取得・表示、Nestは認可・応答契約を担当します。
他担当の確認は出典付きの提供証拠として扱います。
矛盾や未確認の契約があれば、必要な原本と反証を確認します。
必須相談、各担当の初回確認、未解決事項の保持は続けます。

初回レビューは、短い依頼文から新規の親を起動できます。
`tools/start_codex_review.py`は新規の読取り専用`codex exec`を使います。
長い実装チャットの履歴を引き継ぎません。
依頼文はそのまま渡し、モデルとeffortを上書きしません。
親は指定された実reviewerと必須専門担当へ委譲します。
依頼文には役割、実際の依頼、base/head、未コミットの版を記します。
対象・除外、規則の参照先、提供された未解決事項も含めます。
既存担当への継続・再レビューには、この起動方法を使いません。
逆方向のworkflowでは、従来どおり毎回新規execを使います。
Desktopチャットの自動作成や、現在の履歴削除は行いません。

```bash
python3 -I -B /absolute/path/to/my-claude-agents/tools/start_codex_review.py \
  --project /absolute/path/to/project \
  --request-file /tmp/review-request.txt --out-dir /tmp/new-codex-review
```

このコマンドは実際にCodexを起動します。記録保存用とは別です。
出力先には未使用のフォルダーを指定します。
依頼文、JSONL、最終返答、終了コードを保存します。
JSONLはCLIの出力です。応答別使用量がなければ集計は不明です。
完全な使用量記録には、明示した親子のネイティブログを使います。

### 初回の資料確認と内部advisor

担当は、注入済み・原文を読んだ節・未確認を初回に記録します。
未注入の必須節と、適用する設計書の節・例外を先に確認します。
既知の絶対パスは直接読み、検索0件だけで不存在としません。
変更hunkと関数・必要な呼び出し先を確認し、必要な場合だけ範囲を広げます。
利用者やprojectが全文確認を求めた場合は、その指示を優先します。

`codex-claude-review`では、初回・再開とも内部advisorを無効にします。
起動プロセスへ`CLAUDE_CODE_DISABLE_ADVISOR_TOOL=1`を渡し、契約の`--settings`も保ちます。
通常の`adviser` Agentと、そのモデル設定は変えません。
根拠: [Claude Code公式資料「Turn the advisor off」](https://code.claude.com/docs/en/advisor#turn-the-advisor-off)。

同じ委譲の初回・再開では、一時`--settings`に`"autoCompactWindow":200000`を指定します。
管理設定や既存の圧縮用環境変数を上書きしません。
親子の履歴を約20万トークンを目安に自動圧縮し、毎回扱う入力を抑えます。
キャッシュは有効なままです。応答数やモデルは変えません。
設定済みでも、動作と削減量の確認は実ログが必要です。
集計の`context_inputs_by_transcript`で、担当別の入力中央値と最大値を確認します。
`recorded_compaction_boundaries`は、記録された圧縮境界の件数です。
圧縮後も全未解決事項と必要証拠を保持し、不足だけを原本から回収します。
根拠: [Claude Code公式資料「Context window and auto-compaction」](https://code.claude.com/docs/en/model-config#context-window-and-auto-compaction)。

起動後と再開前、完了時に、Codexが次を実行します。
親JSONLと同セッション配下の子JSONLを検査します。

```bash
python3 -I -B tools/summarize_claude_session.py /absolute/path/session.jsonl --check-review-boundary
```

終了コードは、0が記録上の制限一致、1が禁止ツール検出、2が記録不足です。
1・2では承認せず、不足や違反を保持します。実行中の違反はCodexが停止します。
これはログ検査で、起動前の通信防止やOSの隔離、レビュー承認を保証しません。
集計は内部advisorの追加使用量も含め、通常Agentとserver toolを別に数えます。

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
Claude Codeへ短く依頼し、Claudeが共有規則と実差分を自分で確認します。
契約全文・差分コピー・packetの事前送信は必須にしません。
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
各レビュー段階で🟢Lowを含む全指摘を修正・再確認し、その段階の承認を得てから次へ進めます。

1. Claude Codeが実装し、実装側のHQ/QAが必要な検証を行います。実装済みなら、その変更から始めます。
2. Codexの`qa:`が局所契約等のテスト過不足を確認します。
3. Codexの`e:`がE2E・API等のテスト過不足を確認します。
4. Codexの`cr:`がL1.5レビューを行います。
5. Codexの`adv:`がL2レビューを行います。
6. 最新差分への4承認を確認し、未コミットで上村さんへ渡します。本人が確認後にコミットします。

どの段階の修正でもsnapshotが変われば、QA → E2E-QA → Cr → advの順に確認し直します。
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

## レビューログのHTML保存と効率確認

設定には、実際のセッションログからレポートを作る補助スクリプトがあります。これらは**レビューの実行エンジンではありません**。先にCodexからClaude Codeへレビューを依頼し、親セッションのJSONLを取得します。

`tools/render_review_record.py` はCodex/Claudeの会話を時系列のHTMLに変換します。共有を考える場合は `--redact-personal --omit-thinking` を指定します。認証情報以外の業務情報を完全に伏せる機能ではないため、出力内容を人が点検してから共有してください。

`tools/review_efficiency_report.py` はClaude親/子のトークン・子起動・SendMessage・規則の読込みを集計し、本文を含まないHTMLを出します。別担当の初回確認、別の行範囲、検索、同じ範囲の再参照を区別します。再参照を直ちに無駄と判定しません。

`tools/summarize_claude_session.py` はClaudeのモデル別・層別トークンをJSONで出します。Claude用の集計ツールは、親JSONLと同じセッション配下から子JSONLを取得します。`context_inputs_by_compaction` には記録済み圧縮境界ごとの入力統計とcache read/writeを出します。分割応答は応答IDの初出区間へまとめ、重複境界は除きます。空区間から削減効果を推定しません。`source_reads_by_transcript` はReadの明示的な開始行・行数の有無を、ツールIDで重複を除いて数えます。範囲指定の欠落は調査候補であり、不具合や無駄と自動判定しません。

`tools/summarize_codex_session.py` は、明示したCodex親子ログと期間の使用量をJSONで出します。応答IDで重複を除き、遅れる場合がある累計イベントは合算しません。最終結果は `task_complete` を優先し、なければ `phase` または `channel` が `final` の発言を使います。使用量の欠落は `NOT_AVAILABLE`、壊れた行がある場合は `PARTIAL` です。実請求額や改善率は算出しません。既存のHTML変換と組み合わせ、案件ごとの集計スクリプト作成を避けます。

`tools/capture_codex_review.py` は、同じ集計とHTML変換を1コマンドで行います。
明示した親子ログと期間を一度だけ採取します。ログ探索やレビューは行いません。
使用量JSON・Markdown、担当別の最終返答と会話、会話HTML、入口を保存します。
内部推論とsystem/developer発言は出力しません。
元ログを保ち、既存フォルダーへの上書きを拒否します。
壊れた行や使用量不足は、不完全・不明として残します。
保存結果をLLMへ読み戻して整形する必要はありません。
差分、ソースの版、相談の呼出し証拠は従来どおり保持します。

`tools/read_review_source.py` は、一度の出力量を制限してソースをJSONで返します。本文は行番号付きで、行の途中では切りません。続きは `next_line` から読みます。上限にはJSON全体を含みます。`complete` は指定した開始行から末尾まで読めたことだけを表します。全文必読の場合は1行目から続けます。1行も収まらないときは失敗し、同じ行の再読を求めます。

例（パスは各環境の実ログに置き換えてください）：

```bash
AGENTS="$HOME/projects/my-claude-agents"
REPORTS="$HOME/review-audit"
CLAUDE_LOG="/absolute/path/to/claude-parent.jsonl"
CODEX_LOG="/absolute/path/to/codex-rollout.jsonl"
python3 -I -B "$AGENTS/tools/render_review_record.py" \
  --redact-personal --omit-thinking \
  --out "$REPORTS/full-record.html" "$CODEX_LOG" "$CLAUDE_LOG"
python3 -I -B "$AGENTS/tools/review_efficiency_report.py" \
  --out "$REPORTS/efficiency.html" "$CLAUDE_LOG"
python3 -I -B "$AGENTS/tools/summarize_claude_session.py" \
  "$CLAUDE_LOG" > "$REPORTS/usage.json"
python3 -I -B "$AGENTS/tools/summarize_codex_session.py" \
  --parent "$CODEX_LOG" --child "cr=/absolute/path/to/codex-child.jsonl" \
  --since "2026-11-02T01:10:45.846Z" --until "2026-11-02T01:20:06.962Z" \
  --out "$REPORTS/codex-usage.json"
python3 -I -B "$AGENTS/tools/read_review_source.py" \
  /absolute/path/to/rule.md --start-line 1 --max-chars 6000
python3 -I -B "$AGENTS/tools/read_review_source.py" \
  --batch /tmp/review-reads.json --max-chars 12000
python3 -I -B "$AGENTS/tools/capture_codex_review.py" \
  --parent "$CODEX_LOG" --child "adviser=/absolute/path/to/adviser.jsonl" \
  --child "react=/absolute/path/to/react.jsonl" --child "nest=/absolute/path/to/nest.jsonl" \
  --since "2026-11-02T01:10:45.846Z" --until "2026-11-02T01:20:06.962Z" \
  --out-dir "$REPORTS/new-codex-record" --redact-personal
```

`review-reads.json`は、次の形式で必要な範囲を指定します。
終了行を省くと、出力上限まで読みます。行番号は両端を含みます。

```json
[
  {"path": "/absolute/path/to/rule.md", "start_line": 40, "end_line": 85},
  {"path": "/absolute/path/to/component.tsx", "start_line": 20, "end_line": 70}
]
```

`$REPORTS` はリポジトリ外を推奨します。Git作業ツリー内では、`setup.sh` が `.git/info/exclude` に登録した `.codex/review-records/` だけが出力可能です。既存の `.gitignore` は参照・変更しません。生成したHTMLは所有者のみ読み取り可能な権限（Unix: 0600）で保存します。

合成ログによるテストと実際のCodex/Claude起動テストは別です。`docs/review-efficiency-validation.md` の手順で両方を確認してください。

品質維持は、[レビュー目的と品質の比較](docs/review-quality-validation.md)で確認します。
`tools/review_quality_report.py`は、同条件の実行結果と独立採点を比較します。
見逃し、誤指摘、範囲判断の誤り、必須確認不足を、消費量と分けて扱います。
未実行・未採点・条件不一致は`INCONCLUSIVE`です。
合成テストだけで、実レビューの品質維持を主張しません。

層の追加は、仕事が重ならず、品質と総使用量の比較で有利な場合の候補です。
既存のCR・L2・QA/E2Eを使い、要件の未確定時だけ`req-pl`へ相談します。
L2は変更した境界の判断を担当し、親が他層の未了と全体のマージ条件を管理します。
L2自身が必要とする証拠の不足は、その層の未了として残します。
必須の独立確認・専門相談・既存の指摘解消条件は維持します。
追加層を比較する際は`review_quality_report.py --require-benefit`を使います。
親・全担当の総トークンと経過時間を含め、未測定の候補は常設しません。
この設定では新しい常設層や、自動のレビュー連鎖を追加していません。

## 修正差分と検証結果をまとめる再レビュー

`codex-claude-review`では、初回レビューを完了し、指摘を一括修正した後、必要な予定済み検証を行います。その結果を修正差分と一緒に、元の同じ親子へ一度に渡します。通常は、修正だけ先に送り、結果を後から追補する形を避けます。

対象差分はstaged・unstaged・untrackedを区別し、新規内容と実sourceを識別します。正確な利用者回答・制約、実コマンド・ケース・終了コード・検証対象source、結果と限界を添えます。検証したtest/scriptへの狭い参照、または必要なassertionと実際の読み込み対象も、Claudeが許可されたReadで同時に確認できる形にします。PASSのケース名だけでは、検証内容の証拠としません。除外されたreports全体の公開は不要です。

短い依頼と必要な参照・抜粋で構いません。巨大manifest、全差分・全テスト本文・未変更資料の再送、毎回のhash照合は追加しません。再依頼の基準は、予定した検証結果が失敗も含めてそろうことです。全テスト成功を一律の条件にはしません。

検証不要の明示指示、検証不能、失敗、未実行、部分中断は、その状態・理由と未了義務を残します。先にレビュー判断が必要な質問や利用者の明示指示など、根拠のある早期継続も認めます。通常の一括提供とは区別して記録します。Claudeの読取り専用、Codexの実行所有、同じ担当の再開、各層の独立承認は維持します。逆方向の契約は変更しません。

## サブエージェントへの規則の事前読込

Claudeの全担当は、`skills`指定で`engineering-review-core`を起動時に読み込みます。ReactとNestには、それぞれの担当範囲の追加スキルも渡します。ガバナンスと人のレビュー方針から節単位で原文を抽出し、禁止事項・条件・例外を保持します。設計書は変更に関係する部分を別途確認します。

正本は`.claude/knowledge/`の2資料です。`.claude-company/knowledge/`との一致を確認し、`tools/sync_engineering_preloads.py --write`で両profileとCodexの`.agents/skills/`を生成します。通常の実行は変更せず、出典の変更や生成物の欠落を検出します。生成物には原文のSHA-256と収録節を記録します。

Codex用の生成物も、実際に届いた原文の節だけを読取り済みとして扱います。未収録の必須規則は別途確認します。原文の`.claude/knowledge/`を架空の`.Codex/knowledge/`へ置き換えません。Claudeのシェル禁止と、Codexの許可された読取りツールを区別し、スキルで権限を広げません。

規則の比較実験は、両profileの原文を持つ隔離コピーで行えます。`python3 -I -B tools/sync_engineering_preloads.py --root /tmp/rule-candidate --write`は、そのコピーだけに生成します。共有の既定設定を実験中に書き換える必要はありません。

CodexからClaudeへのレビューでは、各phase初回に2資料の解決済み絶対パスとSHA-256だけを一度渡し、Claude親から各担当へ引き継ぎます。同じ担当の再開では保持済みの値を使い、原文変更時だけ更新します。

初回の`Rules loaded`には、実際に渡されたスキル・収録節・版を残します。原文の全文読了とは区別します。担当が持たない節、原文と版が合わない場合、判断が曖昧な場合は、許可された読取り手段で必要な原文と例外を確認します。レビュー専用Claudeへ確認用のBash実行を求めません。

既存の導入先では、新しいスキルを見つけるため、利用中profileの`setup.sh`または`setup.ps1`を再実行し、新しいClaudeセッションを始めます。定義の更新だけで、既存セッションや個別リンクへ新規ディレクトリが追加されたとは扱いません。導入先の既存実ファイルは従来どおり保護します。構成テストの成功は、実際の方針順守やトークン削減の証明ではありません。

公式仕様: [Claude Code — Preload skills into subagents](https://code.claude.com/docs/en/sub-agents#preload-skills-into-subagents)

Claudeの各担当は、原本と対応を確認できる注入済みの自己定義・規則を再取得しません。初回の親がworkflow全文を確認し、各担当へ原本の場所・版・担当する節を渡します。各担当は`review_entry.role_sections`が指定する原文と例外を自分で読みます。Codex用`AGENTS.md`の全文を一律には課しません。project共通指示、未注入の必須節、設計書、変更ファイル全文を求める規則は維持します。

Adviserは最小限の境界確認後、ReactとNestへ責務別の質問をまとめます。相談は前景実行を優先し、実回答を受けて一度で統合します。実toolに`run_in_background`があれば`false`を使います。直接呼出しが使えなければ、親がまとめて実相談し、アクセス可能な回答原本と実IDを同じ担当へ戻します。実ID、質問・回答原本、採否と根拠は残します。起動確認や回答待ちを完了とは扱いません。権限やtoolを増やさず、取得できない回答は未了として残します。

前景実行の仕様: [Claude Code — Run subagents in foreground or background](https://code.claude.com/docs/en/sub-agents#run-subagents-in-foreground-or-background)（2026-11-01確認）。実行版のtool定義を優先し、未対応の引数は作りません。

使用量の目標は、1アカウントの5時間枠で初回4層が33％以内、再レビュー込みで約40％です。初回には必読不足の回収と必須専門相談を含めます。修正後の再レビューとCodexとの比較実験は初回から除きます。同じアカウント・同じリセット窓で、開始前、各層後、初回完了、再レビュー完了の使用率を記録します。開始時との差分（％ポイント）で、使用枠の消費量を確認します。比較実験の分は別記します。開始・終了時刻、実行版とsource snapshotも残します。窓やアカウントが変わった区間は分け、目標達成を断定しません。キャッシュ込みトークン累計や参考ドル額を使用枠％へ換算しません。今回の設定だけでは削減率を証明できません。

キャッシュTTLは変更しません。5分を超えて待つ担当だけを1時間TTLの検討対象にし、採用時に実行版の公式仕様と実測を確認します。短い作業での書込み単価の増加も含め、全体へ一律適用しません。

## 補助スクリプト

`tools/sync_reviewer_body.py`は、`reviewer`の本文を`.claude`・`.claude-company`・`.codex`の3ファイルで同期します。`reviewer`の本文を変更したときに、引数なしで検証し、`--dry-run`で確認して`--write`で同期します。

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

## Desktop サブエージェントの更新

Desktop の実効 CODEX_HOME へコピーする場合は、[専用の更新手順](desktop-subagent-sync.md)を使います。初期動作は差分確認だけです。既存のプロジェクト用 setup スクリプトとは対象が異なります。
