param(
  [ValidateSet("scan", "checkfix", "full")]
  [string]$Mode = "full",
  [string]$ProjectRoot = "."
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Step {
  param(
    [Parameter(Mandatory = $true)][string]$Title,
    [Parameter(Mandatory = $true)][scriptblock]$Action
  )
  Write-Host "`n== $Title ==" -ForegroundColor Cyan
  & $Action
}

Push-Location $ProjectRoot
try {
  if (-not (Get-Command rg -ErrorAction SilentlyContinue)) {
    throw "rg command is required for ux-audit.ps1"
  }

  if ($Mode -eq "scan" -or $Mode -eq "full") {
    Invoke-Step -Title "UX chain keyword scan" -Action {
      rg -n "provider|baseURL|model|apiKey|loadModels|testConnection|chatStream|handleCopy|useMessage" packages
    }

    Invoke-Step -Title "Event + feedback handlers" -Action {
      rg -n "@click|@copy|@send|message\.success|message\.error|warning\(" packages/web/src packages/ui/src
    }

    Invoke-Step -Title "Known UX risk markers" -Action {
      rg -n "TODO|FIXME|HACK|XXX" packages docs
    }
  }

  if ($Mode -eq "checkfix" -or $Mode -eq "full") {
    if (Test-Path "pnpm-workspace.yaml") {
      Invoke-Step -Title "Build core" -Action { pnpm -F @prompt-matrix/core build }
      Invoke-Step -Title "Build ui" -Action { pnpm -F @prompt-matrix/ui build }
      Invoke-Step -Title "Build web" -Action { pnpm -F @prompt-matrix/web build }
    }
    elseif (Test-Path "package.json") {
      Invoke-Step -Title "Build project" -Action { npm run build }
    }
    else {
      Write-Warning "No workspace build config found. Run project-specific checks manually."
    }
  }
}
finally {
  Pop-Location
}
