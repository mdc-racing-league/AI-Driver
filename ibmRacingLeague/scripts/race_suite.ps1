# race_suite.ps1 -- full experiment suite runner
#
# Usage (from repo root):
#   .\scripts\race_suite.ps1                       # run all 6 strategies in order
#   .\scripts\race_suite.ps1 -Only flat-out        # run just one strategy by id
#   .\scripts\race_suite.ps1 -Strategy run016      # alias for -Only
#   .\scripts\race_suite.ps1 -List                 # print strategy list and exit
#
# TORCS must be running in a separate window with:
#   scr_server 1 / Corkscrew / 1 lap / New Race
# The script pauses before each lap so you can reset TORCS.

param(
    [string]$Only = "",
    [string]$Strategy = "",
    [switch]$List
)

$ErrorActionPreference = "Stop"

# Accept -Strategy as an alias for -Only
if ($Strategy -ne "" -and $Only -eq "") { $Only = $Strategy }

# ---------------------------------------------------------------------------
# Strategy table
# ---------------------------------------------------------------------------
$strategies = @(
    [PSCustomObject]@{
        id          = "run016"
        name        = "Lookahead-200 Conservative"
        description = "Full throttle, brakes 200m before corners at 7 m/s^2"
        driverArgs  = "--segments telemetry\segments.yaml --lookahead 200 --lookahead-decel 7.0"
    },
    [PSCustomObject]@{
        id          = "run017"
        name        = "Lookahead-150 Moderate"
        description = "Full throttle, brakes 150m at 9 m/s^2"
        driverArgs  = "--segments telemetry\segments.yaml --lookahead 150 --lookahead-decel 9.0"
    },
    [PSCustomObject]@{
        id          = "run018"
        name        = "Lookahead-120 Aggressive"
        description = "Full throttle, brakes 120m at 11 m/s^2"
        driverArgs  = "--segments telemetry\segments.yaml --lookahead 120 --lookahead-decel 11.0"
    },
    [PSCustomObject]@{
        id          = "flat-out"
        name        = "Flat Out (130 km/h + lookahead)"
        description = "Straights uncapped at 130, braking before corners"
        driverArgs  = "--segments telemetry\segments_flat_out.yaml --lookahead 150 --lookahead-decel 9.0"
    },
    [PSCustomObject]@{
        id          = "push-straights"
        name        = "Push Straights (110 km/h)"
        description = "s08 at 110, s06/s10/s12 at 100, lookahead braking"
        driverArgs  = "--segments telemetry\segments_push.yaml --lookahead 150 --lookahead-decel 9.0"
    },
    [PSCustomObject]@{
        id          = "regression"
        name        = "Run-013 Regression Check"
        description = "Reproduce Run 013 (165.666s) to verify nothing drifted"
        driverArgs  = "--segments telemetry\segments.yaml"
    },
    [PSCustomObject]@{
        id          = "brake-test"
        name        = "Brake Calibration"
        description = "Accelerate to 100 km/h then floor brake -- measures actual decel"
        driverArgs  = "--brake-test 100"
    },
    [PSCustomObject]@{
        id          = "r2a-conservative"
        name        = "Round-2A Conservative (decel 14)"
        description = "Lookahead 60m / decel 14 -- accounts for cornering grip loss"
        driverArgs  = "--segments telemetry\segments.yaml --lookahead 60 --lookahead-decel 14.0"
    },
    [PSCustomObject]@{
        id          = "r2b-real"
        name        = "Round-2B Real (decel 18)"
        description = "Lookahead 40m / decel 18 -- trust measured 22 m/s^2 with cornering margin"
        driverArgs  = "--segments telemetry\segments.yaml --lookahead 40 --lookahead-decel 18.0"
    },
    [PSCustomObject]@{
        id          = "r2c-aggressive"
        name        = "Round-2C Aggressive (decel 21)"
        description = "Lookahead 30m / decel 21 -- peak * 0.85, latest possible braking"
        driverArgs  = "--segments telemetry\segments.yaml --lookahead 30 --lookahead-decel 21.0"
    },
    [PSCustomObject]@{
        id          = "r2a-v2"
        name        = "Round-2A v2 (decel 14 + full pedal)"
        description = "Lookahead 60m / decel 14 / brake pedal forced to 1.0 in zone"
        driverArgs  = "--segments telemetry\segments.yaml --lookahead 60 --lookahead-decel 14.0 --full-pedal-brake"
    }
)

# ---------------------------------------------------------------------------
# -List flag: print strategies and exit
# ---------------------------------------------------------------------------
if ($List) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  RACE SUITE -- STRATEGY LIST" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    $i = 1
    foreach ($s in $strategies) {
        Write-Host ("  {0}. [{1}] {2}" -f $i, $s.id, $s.name) -ForegroundColor White
        Write-Host ("     {0}" -f $s.description) -ForegroundColor Gray
        Write-Host ("     Args: {0}" -f $s.driverArgs) -ForegroundColor DarkGray
        Write-Host ""
        $i++
    }
    exit 0
}

# ---------------------------------------------------------------------------
# Determine which strategies to run
# ---------------------------------------------------------------------------
if ($Only -ne "") {
    $run_strategies = $strategies | Where-Object { $_.id -eq $Only }
    if (-not $run_strategies) {
        Write-Error "Unknown strategy id: '$Only'. Use -List to see valid ids."
        exit 1
    }
} else {
    $run_strategies = $strategies
}

$total = @($run_strategies).Count
$completed = 0

# Session summary tracking
$summary = @()

# ---------------------------------------------------------------------------
# Helper: run post-lap analysis for a given run folder
# ---------------------------------------------------------------------------
function Invoke-PostAnalysis {
    param([string]$runFolder)
    Write-Host ""
    Write-Host "[1/3] Validating schema..." -ForegroundColor Yellow
    python scripts\validate_run.py telemetry\runs\$runFolder --segments-file telemetry\segments.txt

    Write-Host ""
    Write-Host "[2/3] Scanning for off-tracks..." -ForegroundColor Yellow
    python scripts\find_offtracks.py telemetry\runs\$runFolder --threshold 1.0

    Write-Host ""
    Write-Host "[3/3] Generating segment report..." -ForegroundColor Yellow
    python scripts\segment_report.py telemetry\runs\$runFolder
}

# ---------------------------------------------------------------------------
# Helper: print commit checklist
# ---------------------------------------------------------------------------
function Write-Checklist {
    param([string]$runFolder, [string]$strategyLabel)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  ACTION CHECKLIST" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  1. SCREENSHOT" -ForegroundColor White
    Write-Host "     Take the TORCS Race Results screenshot now." -ForegroundColor Gray
    Write-Host "     Save it to Downloads. Note the filename." -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. COMMIT and PUSH" -ForegroundColor White
    Write-Host "     Run these commands (replace screenshot filename):" -ForegroundColor Gray
    Write-Host ""
    Write-Host "     git add telemetry\runs\$runFolder" -ForegroundColor Yellow
    Write-Host "     # After screenshot: copy it to docs\screenshots\ then:" -ForegroundColor Gray
    Write-Host "     git add docs\screenshots\<screenshot-filename>" -ForegroundColor Yellow
    $msg = '     git commit -m "telemetry: ' + $runFolder + ' - ' + $strategyLabel + ' - <lap-time> <damages>"'
    Write-Host $msg -ForegroundColor Yellow
    Write-Host "     git push" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  3. RESTART TORCS for next run" -ForegroundColor White
    Write-Host "     Get-Process wtorcs -ErrorAction SilentlyContinue | Stop-Process -Force" -ForegroundColor Yellow
    Write-Host "     cd C:\torcs\torcs; .\wtorcs.exe" -ForegroundColor Yellow
    Write-Host "     Race -> Quick Race -> Corkscrew -> scr_server 1 -> 1 lap -> New Race" -ForegroundColor Gray
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RACE SUITE -- $total strategies queued" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

foreach ($s in $run_strategies) {
    $strategyNum = $completed + 1

    Write-Host ""
    Write-Host "########################################" -ForegroundColor Magenta
    Write-Host ("  Strategy {0}/{1}: [{2}] {3}" -f $strategyNum, $total, $s.id, $s.name) -ForegroundColor Magenta
    Write-Host ("  {0}" -f $s.description) -ForegroundColor Gray
    Write-Host "########################################" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "  Driver args: python src\driver_baseline.py $($s.driverArgs)" -ForegroundColor DarkCyan
    Write-Host ""
    Write-Host "  TORCS SETUP:" -ForegroundColor Yellow
    Write-Host "    1. Launch TORCS (wtorcs.exe) if not running" -ForegroundColor Gray
    Write-Host "    2. Race -> Quick Race -> Corkscrew" -ForegroundColor Gray
    Write-Host "    3. Add scr_server 1 as the only driver" -ForegroundColor Gray
    Write-Host "    4. Set laps = 1" -ForegroundColor Gray
    Write-Host "    5. Click New Race -- wait for 'Not Responding' (waiting for driver)" -ForegroundColor Gray
    Write-Host ""

    Read-Host "  TORCS ready? Press ENTER to launch driver (Ctrl+C to abort suite)"

    $env:PYTHONIOENCODING = "utf-8"

    $noteStr = "$($s.id) - $($s.name)"
    $cmdArgs = "$($s.driverArgs) --notes `"$noteStr`""
    Invoke-Expression "python src\driver_baseline.py $cmdArgs"

    # Auto-detect latest run folder
    $runFolder = (Get-ChildItem telemetry\runs\ | Sort-Object LastWriteTime -Descending | Select-Object -First 1).Name
    if (-not $runFolder) {
        Write-Warning "Could not detect run folder. Skipping analysis."
        $summary += [PSCustomObject]@{ Strategy = "$($s.id) $($s.name)"; RunFolder = "(not found)"; Status = "error" }
        continue
    }

    Write-Host ""
    Write-Host "  Run folder detected: $runFolder" -ForegroundColor Cyan

    # Post-lap analysis (special path for brake-test calibration)
    Write-Host ""
    if ($s.id -eq "brake-test") {
        Write-Host "--- Brake calibration analysis ---" -ForegroundColor Cyan
        python scripts\analyze_brake_test.py telemetry\runs\$runFolder
    } else {
        Write-Host "--- Post-lap analysis ---" -ForegroundColor Cyan
        Invoke-PostAnalysis -runFolder $runFolder
    }

    # Checklist
    Write-Checklist -runFolder $runFolder -strategyLabel "$($s.id) $($s.name)"

    $completed++
    $summary += [PSCustomObject]@{
        Strategy  = "$($s.id) $($s.name)"
        RunFolder = $runFolder
        Status    = "completed"
    }

    # Progress
    Write-Host ""
    Write-Host ("  Completed {0} of {1} strategies." -f $completed, $total) -ForegroundColor Cyan

    # Pause between strategies (skip after last one)
    if ($completed -lt $total) {
        Write-Host ""
        Read-Host "  Ready for next strategy? Press ENTER (or Ctrl+C to stop suite)"
    }
}

# ---------------------------------------------------------------------------
# Session summary
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "========================================"  -ForegroundColor Cyan
Write-Host "  SESSION SUMMARY" -ForegroundColor Cyan
Write-Host "========================================"  -ForegroundColor Cyan
Write-Host ""
Write-Host ("  {0,-30} | {1,-28} | {2}" -f "Strategy", "Run folder", "Status")
Write-Host ("  {0}" -f ("-" * 72))

# Fill in skipped strategies (those not in summary yet)
foreach ($s in $strategies) {
    $entry = $summary | Where-Object { $_.Strategy -like "$($s.id)*" }
    if ($entry) {
        Write-Host ("  {0,-30} | {1,-28} | {2}" -f $entry.Strategy, $entry.RunFolder, $entry.Status)
    } elseif ($Only -eq "" -or $Only -eq $s.id) {
        # Was supposed to run but didn't (Ctrl+C)
        Write-Host ("  {0,-30} | {1,-28} | {2}" -f "$($s.id) $($s.name)", "(interrupted)", "-")
    } else {
        Write-Host ("  {0,-30} | {1,-28} | {2}" -f "$($s.id) $($s.name)", "(skipped)", "-") -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host ("  Ran {0} of {1} strategies." -f $completed, $total) -ForegroundColor Green
Write-Host ""
