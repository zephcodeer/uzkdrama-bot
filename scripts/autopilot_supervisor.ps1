# ==============================================================================
# Autopilot Kdrama Donor Listener - Resilient PowerShell Supervisor Daemon
# ==============================================================================
param (
    [switch]$DryRun,
    [switch]$Foreground
)

$ErrorActionPreference = "Continue"

$BaseDir = "E:\Agent\Drama Bot"
$ScriptPath = Join-Path $BaseDir "scripts\autopilot_donor_listener.py"
$LogPath = Join-Path $BaseDir "scripts\autopilot.log"
$StopFlagPath = Join-Path $BaseDir "scripts\.autopilot_stop"
$PidFilePath = Join-Path $BaseDir "scripts\.autopilot_supervisor.pid"

function Write-SupervisorLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss,fff")
    $logLine = "$timestamp [$Level] [SUPERVISOR] $Message"
    try {
        Add-Content -Path $LogPath -Value $logLine -Encoding utf8 -ErrorAction SilentlyContinue
    } catch {}
    if ($Foreground -or [Environment]::UserInteractive) {
        Write-Host $logLine
    }
}

# 1. Single Instance Supervisor Guard using PID file and active process check
$currentPid = $PID
if (Test-Path $PidFilePath) {
    $existingPidStr = (Get-Content -Path $PidFilePath -Raw -ErrorAction SilentlyContinue).Trim()
    if ($existingPidStr -match '^\d+$') {
        $existingPid = [int]$existingPidStr
        if ($existingPid -ne $currentPid) {
            $existingProc = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
            if ($existingProc -and ($existingProc.ProcessName -like "*powershell*" -or $existingProc.ProcessName -like "*pwsh*")) {
                Write-SupervisorLog "Another supervisor instance is already active (PID: $existingPid). Exiting duplicate." "WARNING"
                exit 0
            }
        }
    }
}

# Clean stale stop flag and record our PID
if (Test-Path $StopFlagPath) {
    Remove-Item -Path $StopFlagPath -Force -ErrorAction SilentlyContinue
}
Set-Content -Path $PidFilePath -Value $currentPid -Encoding utf8 -Force

Write-SupervisorLog "Supervisor started with PID $currentPid. Target script: $ScriptPath"

# 2. Resolve Python Executable
$PythonCandidates = @(
    "C:\Users\MuhammadSodiq\.gemini\antigravity\scratch\TG AI PERSON\.venv\Scripts\python.exe",
    "C:\Python313\python.exe",
    (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
)

$PythonExe = $null
foreach ($cand in $PythonCandidates) {
    if ($cand -and (Test-Path $cand)) {
        $PythonExe = $cand
        break
    }
}

if (-not $PythonExe) {
    Write-SupervisorLog "CRITICAL: No valid Python executable found! Aborting supervisor." "ERROR"
    exit 1
}

Write-SupervisorLog "Using Python executable: $PythonExe"

# 3. Terminate any orphaned listener instances before clean start
$orphaned = Get-CimInstance Win32_Process | Where-Object {
    $_.ProcessId -ne $currentPid -and
    $_.CommandLine -like "*autopilot_donor_listener.py*"
}
if ($orphaned) {
    foreach ($p in $orphaned) {
        Write-SupervisorLog "Terminating orphaned listener PID $($p.ProcessId)" "INFO"
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
}

# 4. Supervisor Monitoring Loop
$restartHistory = [System.Collections.Generic.List[datetime]]::new()

try {
    while ($true) {
        if (Test-Path $StopFlagPath) {
            Write-SupervisorLog "Stop flag detected (.autopilot_stop). Exiting supervisor loop gracefully." "INFO"
            Remove-Item -Path $StopFlagPath -Force -ErrorAction SilentlyContinue
            break
        }

        $now = Get-Date
        # Filter crash history within the last 60 seconds
        $recentCrashes = $restartHistory | Where-Object { ($now - $_).TotalSeconds -lt 60 }
        $restartHistory = [System.Collections.Generic.List[datetime]]::new([datetime[]]@($recentCrashes))

        if ($restartHistory.Count -ge 5) {
            Write-SupervisorLog "High crash frequency detected (5 restarts in 60s). Backing off for 30s..." "WARNING"
            Start-Sleep -Seconds 30
        }

        $argsList = @("`"$ScriptPath`"")
        if ($DryRun) {
            $argsList += "--dry-run"
        }

        Write-SupervisorLog "Spawning autopilot_donor_listener process..." "INFO"
        $startTime = Get-Date
        $process = Start-Process -FilePath $PythonExe `
            -ArgumentList $argsList `
            -WorkingDirectory $BaseDir `
            -WindowStyle Hidden `
            -PassThru

        Write-SupervisorLog "autopilot_donor_listener is running with PID $($process.Id)" "INFO"

        # Supervise child process
        while (-not $process.HasExited) {
            if (Test-Path $StopFlagPath) {
                Write-SupervisorLog "Stop signal received. Killing listener PID $($process.Id)..." "INFO"
                Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
                Remove-Item -Path $StopFlagPath -Force -ErrorAction SilentlyContinue
                exit 0
            }
            Start-Sleep -Seconds 2
        }

        $exitCode = $process.ExitCode
        $duration = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 1)
        $restartHistory.Add((Get-Date))

        Write-SupervisorLog "Listener process PID $($process.Id) exited with code $exitCode (Ran for ${duration}s)." $(if ($exitCode -eq 0) { "INFO" } else { "WARNING" })

        if (Test-Path $StopFlagPath) {
            Write-SupervisorLog "Stop flag present after exit. Exiting supervisor." "INFO"
            Remove-Item -Path $StopFlagPath -Force -ErrorAction SilentlyContinue
            break
        }

        Write-SupervisorLog "Restarting listener daemon in 5 seconds..." "INFO"
        Start-Sleep -Seconds 5
    }
} finally {
    if (Test-Path $PidFilePath) {
        $storedPid = (Get-Content -Path $PidFilePath -Raw -ErrorAction SilentlyContinue).Trim()
        if ($storedPid -eq "$currentPid") {
            Remove-Item -Path $PidFilePath -Force -ErrorAction SilentlyContinue
        }
    }
    Write-SupervisorLog "Supervisor shutdown complete." "INFO"
}
