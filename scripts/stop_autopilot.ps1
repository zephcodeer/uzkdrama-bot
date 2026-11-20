# ==============================================================================
# Stop Autopilot Daemon and Supervisors
# ==============================================================================
$ErrorActionPreference = "Continue"

$BaseDir = "E:\Agent\Drama Bot"
$FlagPath = Join-Path $BaseDir "scripts\.autopilot_stop"
$PidFilePath = Join-Path $BaseDir "scripts\.autopilot_supervisor.pid"

# Set stop flag first so any active loop can detect it
try {
    Set-Content -Path $FlagPath -Value "STOP" -Encoding utf8 -Force
} catch {}

$stopped = 0
$currentPid = $PID

# 1. Stop supervisor via PID file if present
if (Test-Path $PidFilePath) {
    $existingPidStr = (Get-Content -Path $PidFilePath -Raw -ErrorAction SilentlyContinue).Trim()
    if ($existingPidStr -match '^\d+$') {
        $existingPid = [int]$existingPidStr
        if ($existingPid -ne $currentPid) {
            try {
                Stop-Process -Id $existingPid -Force -ErrorAction SilentlyContinue
                Write-Host "[OK] Supervisor to'xtatildi (PID: $existingPid)" -ForegroundColor Green
                $stopped++
            } catch {}
        }
    }
}

# 2. Terminate any remaining supervisor processes
$supervisors = Get-CimInstance Win32_Process | Where-Object {
    $_.ProcessId -ne $currentPid -and
    $_.CommandLine -like "*autopilot_supervisor.ps1*"
}
foreach ($proc in $supervisors) {
    try {
        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "[OK] Supervisor jarayoni to'xtatildi (PID: $($proc.ProcessId))" -ForegroundColor Green
        $stopped++
    } catch {}
}

# 3. Terminate any running listeners
$listeners = Get-CimInstance Win32_Process | Where-Object {
    $_.ProcessId -ne $currentPid -and
    $_.CommandLine -like "*autopilot_donor_listener.py*"
}
foreach ($proc in $listeners) {
    try {
        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "[OK] Listener jarayoni to'xtatildi (PID: $($proc.ProcessId))" -ForegroundColor Green
        $stopped++
    } catch {}
}

Start-Sleep -Seconds 1

# Clean flags
if (Test-Path $FlagPath) {
    Remove-Item -Path $FlagPath -Force -ErrorAction SilentlyContinue
}
if (Test-Path $PidFilePath) {
    Remove-Item -Path $PidFilePath -Force -ErrorAction SilentlyContinue
}

if ($stopped -eq 0) {
    Write-Host "[INFO] Autopilot faol emas edi (hech qanday jarayon topilmadi)." -ForegroundColor Cyan
} else {
    Write-Host "[OK] Jami $stopped ta autopilot jarayoni to'liq to'xtatildi." -ForegroundColor Green
}
