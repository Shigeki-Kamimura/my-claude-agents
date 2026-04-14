# Why: upstream リポジトリを汚さずに個人用 agents/skills/settings を各プロジェクトへ展開するため（Windows ネイティブ環境向け）。
# Scope: .claude と .codex のシンボリックリンク作成と .git/info/exclude への登録のみ。upstream ファイルは変更しない。
# Usage: pwsh ~/.claude/setup.ps1 [-Target C:\path\to\your-project]
# 前提: 開発者モード ON（管理者権限不要でシンボリックリンクが使えるようになる）
#   設定 > システム > 開発者向け > 開発者モード: オン

param(
    [string]$Target = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# --- パス解決 ---
$SelfDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$SrcAgents = Join-Path $SelfDir ".claude\agents"
$SrcSkills = Join-Path $SelfDir ".claude\skills"
$SrcSettings = Join-Path $SelfDir ".claude\settings.json"
$SrcClaudeMd = Join-Path $SelfDir ".claude\CLAUDE.md"
$SrcCodexAgents = Join-Path $SelfDir ".codex\agents"
$SrcCodexInstructions = Join-Path $SelfDir ".codex\AGENTS.md"

$Target = (Resolve-Path $Target).Path
$ClaudeDir   = Join-Path $Target ".claude"
$CodexDir    = Join-Path $Target ".codex"
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
$devMode = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" -ErrorAction SilentlyContinue).AllowDevelopmentWithoutDevLicense
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

# --- agents: ファイル単位でリンク（upstream 実ファイルは skip） ---
New-Item -ItemType Directory -Path (Join-Path $ClaudeDir "agents") -Force | Out-Null
Add-Exclude ".claude/agents"

$linkedAgents = 0; $skippedAgents = 0
foreach ($src in (Get-ChildItem -Path $SrcAgents -Filter "*.md" -File)) {
    $dest = Join-Path $ClaudeDir "agents\$($src.Name)"

    if ((Test-Path $dest) -and (Get-Item $dest).LinkType -ne "SymbolicLink") {
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

        if ((Test-Path $dest) -and (Get-Item $dest).LinkType -ne "SymbolicLink") {
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

# --- CLAUDE.md: upstream が持っていれば触らない ---
$claudeMdDest = Join-Path $ClaudeDir "CLAUDE.md"
if ((Test-Path $claudeMdDest) -and (Get-Item $claudeMdDest).LinkType -ne "SymbolicLink") {
    Write-Host "  [SKIP upstream] CLAUDE.md（upstream 優先）"
} else {
    if (Test-Path $claudeMdDest) { Remove-Item $claudeMdDest -Force }
    New-Item -ItemType SymbolicLink -Path $claudeMdDest -Target $SrcClaudeMd | Out-Null
    Add-Exclude ".claude/CLAUDE.md"
    Write-Host "  [LINK] CLAUDE.md -> $SrcClaudeMd"
}

# --- settings.json: upstream が持っていれば触らない ---
$settingsDest = Join-Path $ClaudeDir "settings.json"
if ((Test-Path $settingsDest) -and (Get-Item $settingsDest).LinkType -ne "SymbolicLink") {
    Write-Host "  [SKIP upstream] settings.json（upstream 優先）"
} else {
    if (Test-Path $settingsDest) { Remove-Item $settingsDest -Force }
    New-Item -ItemType SymbolicLink -Path $settingsDest -Target $SrcSettings | Out-Null
    Add-Exclude ".claude/settings.json"
    Write-Host "  [LINK] settings.json -> $SrcSettings"
}

# --- Codex: AGENTS.md ---
New-Item -ItemType Directory -Path $CodexDir -Force | Out-Null
Add-Exclude ".codex"

$codexInstructionsDest = Join-Path $CodexDir "AGENTS.md"
if ((Test-Path $codexInstructionsDest) -and (Get-Item $codexInstructionsDest).LinkType -ne "SymbolicLink") {
    Write-Host "  [SKIP upstream] .codex/AGENTS.md（upstream 優先）"
} else {
    if (Test-Path $codexInstructionsDest) { Remove-Item $codexInstructionsDest -Force }
    New-Item -ItemType SymbolicLink -Path $codexInstructionsDest -Target $SrcCodexInstructions | Out-Null
    Write-Host "  [LINK] .codex/AGENTS.md -> $SrcCodexInstructions"
}

# --- Codex agents: ファイル単位でリンク ---
New-Item -ItemType Directory -Path (Join-Path $CodexDir "agents") -Force | Out-Null

$linkedCodexAgents = 0; $skippedCodexAgents = 0
if (Test-Path $SrcCodexAgents) {
    foreach ($src in (Get-ChildItem -Path $SrcCodexAgents -Filter "*.toml" -File)) {
        $dest = Join-Path $CodexDir "agents\$($src.Name)"

        if ((Test-Path $dest) -and (Get-Item $dest).LinkType -ne "SymbolicLink") {
            Write-Host "  [SKIP upstream] .codex/agents/$($src.Name)"
            $skippedCodexAgents++
        } else {
            if (Test-Path $dest) { Remove-Item $dest -Force }
            New-Item -ItemType SymbolicLink -Path $dest -Target $src.FullName | Out-Null
            Write-Host "  [LINK] .codex/agents/$($src.Name) -> $($src.FullName)"
            $linkedCodexAgents++
        }
    }
}

# --- サマリ ---
Write-Host ""
Write-Host "=== 完了 ===" -ForegroundColor Green
Write-Host "  claude agents : $linkedAgents linked, $skippedAgents skipped (upstream)"
Write-Host "  claude skills : $linkedSkills linked, $skippedSkills skipped (upstream)"
Write-Host "  codex agents  : $linkedCodexAgents linked, $skippedCodexAgents skipped (upstream)"
Write-Host ""
Write-Host "upstream を汚さないために .git/info/exclude を使用しています（.gitignore は変更していません）"
