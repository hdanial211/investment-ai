<#
.SYNOPSIS
  Memantau log enjin Investment AI secara langsung (tail -f).
  Memaparkan output Rust dan Python worker dengan warna berbeza.
  Ctrl+C berhenti memantau; enjin tetap berjalan.
#>
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repository = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\\..')).Path
$logDir = Join-Path $repository 'runtime\logs'

$latest = Get-ChildItem $logDir -Filter '*.launch.json' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $latest) { Write-Host 'Tiada log ditemui.' -ForegroundColor Red; return }

$receipt = Get-Content $latest.FullName -Raw | ConvertFrom-Json
$stdoutPath = $receipt.stdout_path
$stderrPath = $receipt.stderr_path
$enginePid  = $receipt.process_id

Write-Host ''
Write-Host '  ============================================' -ForegroundColor DarkCyan
Write-Host '    INVESTMENT AI - LOG MONITOR' -ForegroundColor Cyan
Write-Host '  ============================================' -ForegroundColor DarkCyan
Write-Host ''
Write-Host "  PID Enjin   : $enginePid" -ForegroundColor Green
Write-Host "  Mode        : $($receipt.mode)" -ForegroundColor Green
Write-Host "  Engine Hash : $($receipt.engine_hash.Substring(0,16))..." -ForegroundColor DarkGray
Write-Host "  Stdout      : $stdoutPath" -ForegroundColor DarkGray
Write-Host "  Stderr      : $stderrPath" -ForegroundColor DarkGray

$proc = Get-Process -Id $enginePid -ErrorAction SilentlyContinue
if ($proc) {
    Write-Host "  Status      : AKTIF" -ForegroundColor Green
} else {
    Write-Host "  Status      : TIDAK AKTIF (PID $enginePid sudah berhenti)" -ForegroundColor Red
    return
}

# Show Python worker PIDs
$workers = @(Get-CimInstance Win32_Process | Where-Object {
    $_.ParentProcessId -eq $enginePid -and $_.Name -match '^python'
})
foreach ($w in $workers) {
    $port = if ($w.CommandLine -match '(\d{4})') { $Matches[1] } else { '?' }
    Write-Host "  Worker PID  : $($w.ProcessId) ($($w.Name))" -ForegroundColor Green
}

Write-Host ''
Write-Host '  --- Log terakhir ---' -ForegroundColor DarkGray

$existingOut = Get-Content $stdoutPath -Tail 15 -ErrorAction SilentlyContinue
foreach ($line in $existingOut) {
    $color = if ($line -match 'WARN') { 'Yellow' } elseif ($line -match 'ERROR') { 'Red' } else { 'Cyan' }
    Write-Host "  [RUST]   $line" -ForegroundColor $color
}

$existingErr = Get-Content $stderrPath -Tail 30 -ErrorAction SilentlyContinue
$shownErr = @()
foreach ($line in $existingErr) {
    if ($line -match '(ERROR|WARN|FATAL|Traceback|raise |File ".*investment_ai)') {
        $shownErr += $line
    }
}
if ($shownErr.Count -gt 10) { $shownErr = $shownErr[-10..-1] }
foreach ($line in $shownErr) {
    $color = if ($line -match '(ERROR|Traceback)') { 'Red' } else { 'Yellow' }
    Write-Host "  [WORKER] $line" -ForegroundColor $color
}

Write-Host ''
Write-Host '  --- Memantau secara langsung (Ctrl+C = berhenti monitor, enjin kekal aktif) ---' -ForegroundColor White
Write-Host ''

$stdoutStream = $null; $stderrStream = $null
$stdoutReader = $null; $stderrReader = $null

try {
    $share = [System.IO.FileShare]([System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete)
    $stdoutStream = [System.IO.FileStream]::new($stdoutPath, 'Open', 'Read', $share)
    $stderrStream = [System.IO.FileStream]::new($stderrPath, 'Open', 'Read', $share)
    $stdoutReader = [System.IO.StreamReader]::new($stdoutStream)
    $stderrReader = [System.IO.StreamReader]::new($stderrStream)

    [void]$stdoutStream.Seek(0, 'End')
    [void]$stderrStream.Seek(0, 'End')

    $idle = 0
    while ($true) {
        $hadOutput = $false

        $line = $stdoutReader.ReadLine()
        while ($null -ne $line) {
            $hadOutput = $true
            $color = if ($line -match 'ERROR') { 'Red' } elseif ($line -match 'WARN') { 'Yellow' } else { 'Cyan' }
            Write-Host "  [RUST]   $line" -ForegroundColor $color
            $line = $stdoutReader.ReadLine()
        }

        $line = $stderrReader.ReadLine()
        while ($null -ne $line) {
            $hadOutput = $true
            $color = if ($line -match '(ERROR|Traceback|Exception|raise )') { 'Red' } else { 'DarkYellow' }
            Write-Host "  [WORKER] $line" -ForegroundColor $color
            $line = $stderrReader.ReadLine()
        }

        if (-not $hadOutput) {
            Start-Sleep -Milliseconds 300
            $idle++
            if ($idle % 100 -eq 0) {
                $alive = Get-Process -Id $enginePid -ErrorAction SilentlyContinue
                $ts = Get-Date -Format 'HH:mm:ss'
                if ($alive) {
                    Write-Host "  [$ts] Enjin AKTIF (PID $enginePid)" -ForegroundColor DarkGray
                } else {
                    Write-Host "  [$ts] Enjin BERHENTI (PID $enginePid tidak ditemui)" -ForegroundColor Red
                    break
                }
            }
        } else {
            $idle = 0
        }
    }
} finally {
    if ($stdoutReader) { $stdoutReader.Dispose() }
    if ($stderrReader) { $stderrReader.Dispose() }
    if ($stdoutStream) { $stdoutStream.Dispose() }
    if ($stderrStream) { $stderrStream.Dispose() }
    Write-Host ''
    Write-Host '  Monitor berhenti. Enjin masih berjalan di latar belakang.' -ForegroundColor DarkGray
}
