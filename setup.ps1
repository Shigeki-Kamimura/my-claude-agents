# Why: upstream リポジトリを汚さずに個人用 agents/skills/settings を各プロジェクトへ展開するため（Windows ネイティブ環境向け）。
# Scope: Claude/Copilot はリンク、Codex TOML は管理下の実ファイルを同期。.git/info のみ使用し upstream を保護。
# Usage: pwsh ~/.claude/setup.ps1 [-Target C:\path\to\your-project] [-p|-Profile personal|company]
# 前提: 開発者モード ON（管理者権限不要でシンボリックリンクが使えるようになる）
#   設定 > システム > 開発者向け > 開発者モード: オン

param(
    [string]$Target  = (Get-Location).Path,
    [Alias("p")]
    [string]$Profile = "company"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# --- パス解決 ---
$SelfDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SrcClaudeRoot = if ($Profile -eq "company") {
    Join-Path $SelfDir ".claude-company"
} else {
    Join-Path $SelfDir ".claude"
}

$SrcAgents = Join-Path $SrcClaudeRoot "agents"
$SrcSkills = Join-Path $SrcClaudeRoot "skills"
$SrcKnowledge = Join-Path $SrcClaudeRoot "knowledge"
$SrcSettings = Join-Path $SrcClaudeRoot "settings.json"
$SrcClaudeMd = Join-Path $SrcClaudeRoot "CLAUDE.md"
$SrcSkillMd = Join-Path $SrcClaudeRoot "SKILL.md"
$SrcCodexAgents = Join-Path $SelfDir ".codex\agents"
$SrcCodexInstructions = Join-Path $SelfDir ".codex\AGENTS.md"
$SrcCodexConfig = Join-Path $SelfDir ".codex\config.toml"
$SrcCopilotInstructions = Join-Path $SelfDir ".copilot\copilot-instructions.md"
$SrcCopilotAgents = Join-Path $SelfDir ".copilot\agents"

$Target = (Resolve-Path $Target).Path
$ClaudeDir   = Join-Path $Target ".claude"
$CodexDir    = Join-Path $Target ".codex"
$CopilotDir  = Join-Path $Target ".copilot"
$ExcludeFile = Join-Path $Target ".git\info\exclude"

# git リポジトリかチェック
if (-not (Test-Path (Join-Path $Target ".git"))) {
    Write-Error "ERROR: $Target は git リポジトリではありません"
    exit 1
}

# 自分自身への展開を防止（循環シンボリックリンクになるため）
if ($SelfDir -eq $Target) {
    Write-Error "ERROR: ソースリポジトリ自身には展開できません"
    exit 1
}

# 開発者モード（シンボリックリンク権限）の確認
# StrictMode 下でプロパティ不在による例外を防ぐため try/catch で包む
$devMode = $null
try {
    $regKey = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" -ErrorAction Stop
    if ($null -ne $regKey -and (Get-Member -InputObject $regKey -Name "AllowDevelopmentWithoutDevLicense" -MemberType NoteProperty -ErrorAction SilentlyContinue)) {
        $devMode = $regKey.AllowDevelopmentWithoutDevLicense
    }
} catch {
    # レジストリキー自体が存在しない場合は警告のみ
}
if ($devMode -ne 1) {
    Write-Warning "開発者モードが OFF の可能性があります。シンボリックリンク作成に失敗する場合は設定を確認してください。"
    Write-Warning "設定 > システム > 開発者向け > 開発者モード: オン"
}

Write-Host "=== claude-config セットアップ: $Target ===" -ForegroundColor Cyan

# --- .git/info/exclude にエントリを追加（重複しない） ---
function Add-Exclude {
    param([string]$Pattern)
    $lines = if (Test-Path $ExcludeFile) { Get-Content $ExcludeFile } else { @() }
    if ($lines -notcontains $Pattern) {
        Add-Content -Path $ExcludeFile -Value $Pattern
        Write-Host "  [exclude] $Pattern"
    }
}

# Gitで追跡中のファイルやシンボリックリンクを変更しません。
function Test-TrackedPath {
    param([string]$Relative)
    $found = @(git -C $Target ls-files --cached -- "$Relative")
    if ($LASTEXITCODE -ne 0) { throw "git ls-files に失敗しました: $Relative" }
    return ($found.Count -gt 0)
}

# --- agents: ファイル単位でリンク（upstream 実ファイルは skip） ---
New-Item -ItemType Directory -Path (Join-Path $ClaudeDir "agents") -Force | Out-Null
Add-Exclude ".claude/agents"

$linkedAgents = 0; $skippedAgents = 0
foreach ($src in (Get-ChildItem -Path $SrcAgents -Filter "*.md" -File)) {
    $dest = Join-Path $ClaudeDir "agents\$($src.Name)"

    if ((Test-TrackedPath ".claude/agents/$($src.Name)") -or ((Test-Path $dest) -and (Get-Item $dest).LinkType -ne "SymbolicLink")) {
        # upstream に実ファイルが存在 → 上書き禁止
        Write-Host "  [SKIP upstream] agents/$($src.Name)"
        $skippedAgents++
    } else {
        if (Test-Path $dest) { Remove-Item $dest -Force }
        New-Item -ItemType SymbolicLink -Path $dest -Target $src.FullName | Out-Null
        Write-Host "  [LINK] agents/$($src.Name) -> $($src.FullName)"
        $linkedAgents++
    }
}

# --- skills: ディレクトリ単位でリンク（upstream 実ディレクトリは skip） ---
New-Item -ItemType Directory -Path (Join-Path $ClaudeDir "skills") -Force | Out-Null
Add-Exclude ".claude/skills"

$linkedSkills = 0; $skippedSkills = 0
if (Test-Path $SrcSkills) {
    foreach ($src in (Get-ChildItem -Path $SrcSkills -Directory)) {
        $dest = Join-Path $ClaudeDir "skills\$($src.Name)"

        if ((Test-TrackedPath ".claude/skills/$($src.Name)") -or ((Test-Path $dest) -and (Get-Item $dest).LinkType -ne "SymbolicLink")) {
            Write-Host "  [SKIP upstream] skills/$($src.Name)/"
            $skippedSkills++
        } else {
            if (Test-Path $dest) { Remove-Item $dest -Force }
            New-Item -ItemType SymbolicLink -Path $dest -Target $src.FullName | Out-Null
            Write-Host "  [LINK] skills/$($src.Name)/ -> $($src.FullName)"
            $linkedSkills++
        }
    }
}

# --- knowledge: ファイル単位でリンク（upstream 実ファイルは skip） ---
New-Item -ItemType Directory -Path (Join-Path $ClaudeDir "knowledge") -Force | Out-Null
Add-Exclude ".claude/knowledge"

$linkedKnowledge = 0; $skippedKnowledge = 0
if (Test-Path $SrcKnowledge) {
    foreach ($src in (Get-ChildItem -Path $SrcKnowledge -Filter "*.md" -File)) {
        $dest = Join-Path $ClaudeDir "knowledge\$($src.Name)"

        if ((Test-TrackedPath ".claude/knowledge/$($src.Name)") -or ((Test-Path $dest) -and (Get-Item $dest).LinkType -ne "SymbolicLink")) {
            Write-Host "  [SKIP upstream] knowledge/$($src.Name)"
            $skippedKnowledge++
        } else {
            if (Test-Path $dest) { Remove-Item $dest -Force }
            New-Item -ItemType SymbolicLink -Path $dest -Target $src.FullName | Out-Null
            Write-Host "  [LINK] knowledge/$($src.Name) -> $($src.FullName)"
            $linkedKnowledge++
        }
    }
}

# --- CLAUDE.md: upstream が持っていれば触らない ---
$claudeMdDest = Join-Path $ClaudeDir "CLAUDE.md"
if ((Test-TrackedPath ".claude/CLAUDE.md") -or ((Test-Path $claudeMdDest) -and (Get-Item $claudeMdDest).LinkType -ne "SymbolicLink")) {
    Write-Host "  [SKIP upstream] CLAUDE.md（upstream 優先）"
} else {
    if (Test-Path $claudeMdDest) { Remove-Item $claudeMdDest -Force }
    New-Item -ItemType SymbolicLink -Path $claudeMdDest -Target $SrcClaudeMd | Out-Null
    Add-Exclude ".claude/CLAUDE.md"
    Write-Host "  [LINK] CLAUDE.md -> $SrcClaudeMd"
}

# --- SKILL.md: upstream が持っていれば触らない ---
if (Test-Path $SrcSkillMd) {
    $skillMdDest = Join-Path $ClaudeDir "SKILL.md"
    if ((Test-TrackedPath ".claude/SKILL.md") -or ((Test-Path $skillMdDest) -and (Get-Item $skillMdDest).LinkType -ne "SymbolicLink")) {
        Write-Host "  [SKIP upstream] SKILL.md（upstream 優先）"
    } else {
        if (Test-Path $skillMdDest) { Remove-Item $skillMdDest -Force }
        New-Item -ItemType SymbolicLink -Path $skillMdDest -Target $SrcSkillMd | Out-Null
        Add-Exclude ".claude/SKILL.md"
        Write-Host "  [LINK] SKILL.md -> $SrcSkillMd"
    }
}

# --- settings.json: upstream が持っていれば触らない ---
$settingsDest = Join-Path $ClaudeDir "settings.json"
if ((Test-TrackedPath ".claude/settings.json") -or ((Test-Path $settingsDest) -and (Get-Item $settingsDest).LinkType -ne "SymbolicLink")) {
    Write-Host "  [SKIP upstream] settings.json（upstream 優先）"
} else {
    if (Test-Path $settingsDest) { Remove-Item $settingsDest -Force }
    New-Item -ItemType SymbolicLink -Path $settingsDest -Target $SrcSettings | Out-Null
    Add-Exclude ".claude/settings.json"
    Write-Host "  [LINK] settings.json -> $SrcSettings"
}

# --- Codex: AGENTS.md ---
# フォルダー全体のリンクへコピーすると共有元を変更するため禁止。
foreach ($dir in @($CodexDir, (Join-Path $CodexDir "agents"))) {
    $item = Get-Item -LiteralPath $dir -Force -ErrorAction SilentlyContinue
    if ($null -ne $item -and $item.LinkType -in @("SymbolicLink", "Junction")) {
        throw "Codex フォルダーがリンクです。共有先への書き込みを避けるため停止します: $dir"
    }
}
New-Item -ItemType Directory -Path $CodexDir -Force | Out-Null
Add-Exclude ".codex"

$codexInstructionsDest = Join-Path $CodexDir "AGENTS.md"
if ((Test-TrackedPath ".codex/AGENTS.md") -or ((Test-Path $codexInstructionsDest) -and (Get-Item $codexInstructionsDest).LinkType -ne "SymbolicLink")) {
    Write-Host "  [SKIP upstream] .codex/AGENTS.md（upstream 優先）"
} else {
    if (Test-Path $codexInstructionsDest) { Remove-Item $codexInstructionsDest -Force }
    New-Item -ItemType SymbolicLink -Path $codexInstructionsDest -Target $SrcCodexInstructions | Out-Null
    Write-Host "  [LINK] .codex/AGENTS.md -> $SrcCodexInstructions"
}

# --- Codex TOML: 管理下のファイルだけ実体コピーして同期 ---
# 管理履歴は .git/info 配下に保存します。.gitignore は変更しません。
New-Item -ItemType Directory -Path (Join-Path $CodexDir "agents") -Force | Out-Null
$codexStateFile = Join-Path $Target ".git\info\codex-setup-managed.tsv"
$codexState = @{}
if (Test-Path -LiteralPath $codexStateFile) {
    foreach ($line in (Get-Content -LiteralPath $codexStateFile)) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $parts = $line.Split([char]9, 2)
        if ($parts.Length -ne 2 -or $parts[1] -notmatch '^[a-fA-F0-9]{64}$') {
            throw "Codex同期の管理履歴が不正です: $codexStateFile"
        }
        $codexState[$parts[0]] = $parts[1].ToLowerInvariant()
    }
}

function Get-CodexSha256 {
    param([string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Save-CodexChecksum {
    param([string]$Relative, [string]$Checksum)
    if ($codexState.ContainsKey($Relative) -and $codexState[$Relative] -eq $Checksum) { return }
    $codexState[$Relative] = $Checksum
    $lines = [string[]]@(
        $codexState.Keys | Sort-Object | ForEach-Object { "{0}{1}{2}" -f $_, [char]9, $codexState[$_] }
    )
    $tmp = Join-Path (Split-Path -Parent $codexStateFile) (
        ".codex-setup-managed-" + [guid]::NewGuid().ToString("N") + ".tmp"
    )
    try {
        [System.IO.File]::WriteAllLines($tmp, $lines, [System.Text.UTF8Encoding]::new($false))
        Move-Item -LiteralPath $tmp -Destination $codexStateFile -Force
    } finally {
        if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }
    }
}

# リンク先が消えていても、管理元の元パスで照合します。
function Test-ManagedCodexLink {
    param($Item, [string]$ExpectedTarget)
    if ($null -eq $Item -or $Item.LinkType -ne "SymbolicLink") { return $false }
    $linkTarget = [string](@($Item.Target)[0])
    if ([string]::IsNullOrEmpty($linkTarget)) { return $false }
    if (-not [System.IO.Path]::IsPathRooted($linkTarget)) {
        $linkTarget = Join-Path (Split-Path -Parent $Item.FullName) $linkTarget
    }
    $comparison = if ([System.IO.Path]::DirectorySeparatorChar -eq '\') {
        [System.StringComparison]::OrdinalIgnoreCase
    } else {
        [System.StringComparison]::Ordinal
    }
    return [string]::Equals(
        [System.IO.Path]::GetFullPath($linkTarget),
        [System.IO.Path]::GetFullPath($ExpectedTarget),
        $comparison
    )
}

function Sync-CodexToml {
    param([string]$Source, [string]$Relative)
    $dest = Join-Path $CodexDir ($Relative.Replace('/', [System.IO.Path]::DirectorySeparatorChar))

    # upstream の追跡済みファイルは、同名のリンクでも変更しません。
    $tracked = @(git -C $Target ls-files --cached -- ".codex/$Relative")
    if ($LASTEXITCODE -ne 0) { throw "git ls-files に失敗しました: .codex/$Relative" }
    if ($tracked.Count -gt 0) {
        Write-Host "  [SKIP tracked] .codex/$Relative"
        return "skipped"
    }

    $existing = Get-Item -LiteralPath $dest -Force -ErrorAction SilentlyContinue
    $sourceHash = Get-CodexSha256 $Source
    if ($null -ne $existing -and $existing.LinkType -eq "SymbolicLink") {
        if (-not (Test-ManagedCodexLink $existing $Source)) {
            Write-Warning "  [CONFLICT preserved] .codex/$Relative（外部リンク）"
            return "conflict"
        }
    } elseif ($null -ne $existing) {
        if ($existing.PSIsContainer) {
            Write-Warning "  [CONFLICT preserved] .codex/$Relative（ファイルではありません）"
            return "conflict"
        }
        $current = Get-CodexSha256 $dest
        $recorded = if ($codexState.ContainsKey($Relative)) { $codexState[$Relative] } else { $null }
        if ($null -eq $recorded -and $current -ne $sourceHash) {
            Write-Host "  [SKIP upstream] .codex/$Relative（管理外の実ファイル）"
            return "skipped"
        }
        if ($null -ne $recorded -and $current -ne $recorded -and $current -ne $sourceHash) {
            Write-Warning "  [CONFLICT preserved] .codex/$Relative（同期後に編集されています）"
            return "conflict"
        }
    }

    # 手動でリンクを実体化してあっても、原本と同じなら引き継ぎます。
    if ($null -ne $existing -and $existing.LinkType -ne "SymbolicLink" -and
        (Get-CodexSha256 $dest) -eq $sourceHash) {
        Save-CodexChecksum $Relative $sourceHash
        Write-Host "  [CURRENT] .codex/$Relative"
        return "current"
    }

    # コピーを先に完成させ、リンクの原本を触らずに置換します。
    $temp = Join-Path (Split-Path -Parent $dest) (
        ".codex-toml-" + [guid]::NewGuid().ToString("N") + ".tmp"
    )
    $linkBackup = $null
    try {
        Copy-Item -LiteralPath $Source -Destination $temp
        if ($null -ne $existing -and $existing.LinkType -eq "SymbolicLink") {
            $linkBackup = Join-Path (Split-Path -Parent $dest) (
                ".codex-old-link-" + [guid]::NewGuid().ToString("N") + ".bak"
            )
            Move-Item -LiteralPath $dest -Destination $linkBackup
        }
        try {
            Move-Item -LiteralPath $temp -Destination $dest -Force
        } catch {
            if ($null -ne $linkBackup -and (Test-Path -LiteralPath $linkBackup)) {
                Move-Item -LiteralPath $linkBackup -Destination $dest -Force
            }
            throw
        }
        if ($null -ne $linkBackup -and (Test-Path -LiteralPath $linkBackup)) {
            Remove-Item -LiteralPath $linkBackup -Force
        }
    } finally {
        if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Force }
    }
    Save-CodexChecksum $Relative (Get-CodexSha256 $dest)
    Write-Host "  [COPY] .codex/$Relative"
    return "copied"
}

if (-not (Test-Path -LiteralPath $SrcCodexConfig -PathType Leaf)) {
    throw "Codex の原本 config.toml がありません: $SrcCodexConfig"
}
$codexCopied = 0; $codexCurrent = 0; $codexSkipped = 0; $codexConflicts = 0
$allStatuses = @()
$allStatuses += (Sync-CodexToml -Source $SrcCodexConfig -Relative "config.toml")

$retiredCodexNames = @("hq.toml", "pl.toml", "qa.toml")
foreach ($retiredName in $retiredCodexNames) {
    $dest = Join-Path $CodexDir "agents\$retiredName"
    $tracked = @(git -C $Target ls-files --cached -- ".codex/agents/$retiredName")
    if ($LASTEXITCODE -ne 0) { throw "git ls-files に失敗しました: $retiredName" }
    $existing = Get-Item -LiteralPath $dest -Force -ErrorAction SilentlyContinue
    if ($tracked.Count -gt 0) {
        Write-Warning "  [CONFLICT preserved] .codex/agents/$retiredName（git追跡対象）"
        $codexConflicts++
    } elseif (Test-ManagedCodexLink $existing (Join-Path $SrcCodexAgents $retiredName)) {
        Remove-Item -LiteralPath $dest -Force
        Write-Host "  [REMOVE retired] .codex/agents/$retiredName"
    } elseif ($null -ne $existing) {
        Write-Warning "  [CONFLICT preserved] .codex/agents/$retiredName（独自ファイル・リンク）"
        $codexConflicts++
    }
}

# *.toml を都度列挙するので、新しく増えた定義も次回 setup で同期されます。
if (Test-Path -LiteralPath $SrcCodexAgents) {
    foreach ($src in (Get-ChildItem -LiteralPath $SrcCodexAgents -Filter "*.toml" -File)) {
        if ($retiredCodexNames -contains $src.Name) { continue }
        $allStatuses += (Sync-CodexToml -Source $src.FullName -Relative "agents/$($src.Name)")
    }
}
$codexCopied += @($allStatuses | Where-Object { $_ -eq "copied" }).Count
$codexCurrent += @($allStatuses | Where-Object { $_ -eq "current" }).Count
$codexSkipped += @($allStatuses | Where-Object { $_ -eq "skipped" }).Count
$codexConflicts += @($allStatuses | Where-Object { $_ -eq "conflict" }).Count

# --- Copilot: copilot-instructions.md ---
New-Item -ItemType Directory -Path $CopilotDir -Force | Out-Null
Add-Exclude ".copilot"

$copilotInstructionsDest = Join-Path $CopilotDir "copilot-instructions.md"
if ((Test-TrackedPath ".copilot/copilot-instructions.md") -or ((Test-Path $copilotInstructionsDest) -and (Get-Item $copilotInstructionsDest).LinkType -ne "SymbolicLink")) {
    Write-Host "  [SKIP upstream] .copilot/copilot-instructions.md（upstream 優先）"
} else {
    if (Test-Path $copilotInstructionsDest) { Remove-Item $copilotInstructionsDest -Force }
    New-Item -ItemType SymbolicLink -Path $copilotInstructionsDest -Target $SrcCopilotInstructions | Out-Null
    Write-Host "  [LINK] .copilot/copilot-instructions.md -> $SrcCopilotInstructions"
}

# --- Copilot agents: ファイル単位でリンク ---
New-Item -ItemType Directory -Path (Join-Path $CopilotDir "agents") -Force | Out-Null

$linkedCopilotAgents = 0; $skippedCopilotAgents = 0
if (Test-Path $SrcCopilotAgents) {
    foreach ($src in (Get-ChildItem -Path $SrcCopilotAgents -Filter "*.md" -File)) {
        $dest = Join-Path $CopilotDir "agents\$($src.Name)"

        if ((Test-TrackedPath ".copilot/agents/$($src.Name)") -or ((Test-Path $dest) -and (Get-Item $dest).LinkType -ne "SymbolicLink")) {
            Write-Host "  [SKIP upstream] .copilot/agents/$($src.Name)"
            $skippedCopilotAgents++
        } else {
            if (Test-Path $dest) { Remove-Item $dest -Force }
            New-Item -ItemType SymbolicLink -Path $dest -Target $src.FullName | Out-Null
            Write-Host "  [LINK] .copilot/agents/$($src.Name) -> $($src.FullName)"
            $linkedCopilotAgents++
        }
    }
}

# --- サマリ ---
Write-Host ""
Write-Host "=== 完了 ===" -ForegroundColor Green
Write-Host "  claude agents   : $linkedAgents linked, $skippedAgents skipped (upstream)"
Write-Host "  claude skills   : $linkedSkills linked, $skippedSkills skipped (upstream)"
Write-Host "  claude knowledge: $linkedKnowledge linked, $skippedKnowledge skipped (upstream)"
Write-Host "  codex TOML      : $codexCopied copied/updated, $codexCurrent current, $codexSkipped skipped"
Write-Host "  copilot agents  : $linkedCopilotAgents linked, $skippedCopilotAgents skipped (upstream)"
if ($codexConflicts -gt 0) {
    Write-Warning "  Codex同期: $codexConflicts 件の競合が残っています。統合完了ではありません。"
}
Write-Host ""
Write-Host "upstream を汚さないために .git/info/exclude を使用しています（.gitignore は変更していません）"
