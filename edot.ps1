#Requires -Modules PSFzf

[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments)]
    [string[]]$Query
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Combine query arguments
$queryString = if ($Query) { $Query -join ' ' } else { '' }
$queryString = $queryString -replace [regex]::Escape($env:USERPROFILE), ''
$queryString = $queryString.TrimStart('\', '/')

# Get managed files, excluding fonts
$files = @(chezmoi managed --include=files,scripts --exclude=externals |
    Where-Object { $_ -notmatch '\.(ttf|otf)$' -and $_ -ne '' })

# Check for exact match first
$selected = @()
if ($queryString -and ($files -contains $queryString)) {
    $selected = @($queryString)
}
elseif ([Environment]::UserInteractive -and (Get-Command Invoke-Fzf -ErrorAction SilentlyContinue)) {
    # Fuzzy match using PSFzf
    $fzfParams = @{
        Multi = $true
        Select1 = $true
        Exit0 = $true
    }
    if ($queryString) {
        $fzfParams['Query'] = $queryString
    }
    # Add bat preview if available
    if (Get-Command bat -ErrorAction SilentlyContinue) {
        $homeVar = if ($IsWindows -or $env:OS -match 'Windows') { $env:USERPROFILE } else { $env:HOME }
        $fzfParams['Preview'] = "bat --color=always --style=header,grid --line-range :500 `"$homeVar/{}`""
        $fzfParams['PreviewWindow'] = 'right:70%:wrap'
    }
    $selected = $files | Invoke-Fzf @fzfParams
}

# Filter out empty selections
$selected = @($selected | Where-Object { $_ -and $_.Trim() })

# Handle unmanaged files
if (-not $selected -and $queryString) {
    $fullPath = Join-Path $env:USERPROFILE $queryString
    if (Test-Path $fullPath -PathType Leaf) {
        Write-Host "Adding $fullPath" -ForegroundColor Yellow
        chezmoi add $fullPath
        $selected = @($queryString)
    }
}

if (-not $selected -or $selected.Count -eq 0) {
    Write-Error "No file selected"
    exit 1
}

# Edit selected files with chezmoi - prepend home directory
# Force array to prevent unwrapping
$fullPaths = @($selected | Where-Object { $_ } | ForEach-Object {
    Join-Path $env:USERPROFILE $_
})

if ($fullPaths -and $fullPaths.Count -gt 0) {
    & chezmoi edit --watch --apply @fullPaths
}
