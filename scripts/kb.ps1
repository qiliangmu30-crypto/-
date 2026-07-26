param(
    [Parameter(Position = 0)]
    [ValidateSet("setup", "build", "test", "check", "query", "context")]
    [string]$Action = "check",
    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$Rest
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$TaskPython = if (Test-Path (Join-Path $RepoRoot ".venv\Scripts\python.exe")) {
    Join-Path $RepoRoot ".venv\Scripts\python.exe"
} else {
    "python"
}
Push-Location $RepoRoot
try {
    switch ($Action) {
        "setup" {
            if (-not (Test-Path ".venv")) { python -m venv .venv }
            & ".\.venv\Scripts\python.exe" -m pip install -e ".[dev]"
        }
        "build" { & $TaskPython -m relationship_kb build --backend hashing }
        "test" { & $TaskPython -m pytest }
        "check" {
            & $TaskPython -m pytest
            & $TaskPython -m relationship_kb lint --strict
            & $TaskPython -m relationship_kb build --backend hashing
        }
        "query" { & $TaskPython -m relationship_kb query ($Rest -join " ") }
        "context" { & $TaskPython -m relationship_kb context ($Rest -join " ") }
    }
}
finally {
    Pop-Location
}
