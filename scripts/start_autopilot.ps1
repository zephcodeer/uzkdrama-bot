# ==============================================================================
# Start Autopilot Daemon and Supervisor
# ==============================================================================
$ErrorActionPreference = "Continue"

$BaseDir = "E:\Agent\Drama Bot"
$SupervisorScript = Join-Path $BaseDir "scripts\autopilot_supervisor.ps1"
$PidFilePath = Join-Path $BaseDir "scripts\.autopilot_supervisor.pid"
$LogPath = Join-Path $BaseDir "scripts\autopilot.log"

# Check if already running via PID file
if (Test-Path $PidFilePath) {
    $existingPidStr = (Get-Content -Path $PidFilePath -Raw -ErrorAction SilentlyContinue).Trim()
    if ($existingPidStr -match '^\d+$') {
        $existingPid = [int]$existingPidStr
        $existingProc = Get-CimInstance Win32_Process -Filter "ProcessId = $existingPid" -ErrorAction SilentlyContinue
        if ($existingProc -and $existingProc.CommandLine -like "*autopilot_supervisor.ps1*") {
            Write-Host "[!] Autopilot xizmati allaqachon fonda ishlamoqda!" -ForegroundColor Yellow
            Write-Host "    Supervisor PID: $existingPid" -ForegroundColor Yellow
            Write-Host "Xizmatni to'xtatish uchun: stop_autopilot.bat dan foydalaning." -ForegroundColor Cyan
            exit 0
        }
    }
}

# Check running listener or supervisor processes directly
$runningSupervisors = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -like "*autopilot_supervisor.ps1*"
}
$runningListeners = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -like "*autopilot_donor_listener.py*"
}

if ($runningSupervisors -or $runningListeners) {
    Write-Host "[!] Autopilot xizmati allaqachon fonda ishlamoqda!" -ForegroundColor Yellow
    if ($runningSupervisors) {
        Write-Host "    Supervisor PID: $(($runningSupervisors | Select-Object -ExpandProperty ProcessId) -join ', ')" -ForegroundColor Yellow
    }
    if ($runningListeners) {
        Write-Host "    Listener PID:   $(($runningListeners | Select-Object -ExpandProperty ProcessId) -join ', ')" -ForegroundColor Yellow
    }
    Write-Host "Xizmatni to'xtatish uchun: stop_autopilot.bat dan foydalaning." -ForegroundColor Cyan
    exit 0
}

Write-Host "Autopilot supervisor fonda ishga tushirilmoqda..." -ForegroundColor Cyan

# Launch PowerShell supervisor in background hidden window
Start-Process powershell.exe `
    -ArgumentList "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$SupervisorScript`"" `
    -WorkingDirectory $BaseDir `
    -WindowStyle Hidden

Start-Sleep -Seconds 3

# Verify supervisor is alive
$activeSupervisorPid = $null
if (Test-Path $PidFilePath) {
    $activeSupervisorPid = (Get-Content -Path $PidFilePath -Raw -ErrorAction SilentlyContinue).Trim()
}

if ($activeSupervisorPid) {
    Write-Host "[OK] Autopilot muvaffaqiyatli ishga tushdi!" -ForegroundColor Green
    Write-Host "    Supervisor PID: $activeSupervisorPid" -ForegroundColor Green
    Write-Host "    Jurnal fayli:   $LogPath" -ForegroundColor Gray
} else {
    $found = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*autopilot_supervisor.ps1*" }
    if ($found) {
        Write-Host "[OK] Autopilot muvaffaqiyatli ishga tushdi!" -ForegroundColor Green
        Write-Host "    Supervisor PID: $(($found | Select-Object -ExpandProperty ProcessId) -join ', ')" -ForegroundColor Green
        Write-Host "    Jurnal fayli:   $LogPath" -ForegroundColor Gray
    } else {
        Write-Host "[XATO] Supervisor ishga tushmadi. Jurnalni tekshiring: $LogPath" -ForegroundColor Red
    }
}
