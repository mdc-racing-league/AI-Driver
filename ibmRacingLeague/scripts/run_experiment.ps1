# run_experiment.ps1  —  launch a named experiment config, then run analysis.
#
# Usage (Window B, from repo root):
#   cd $env:USERPROFILE\ibmRacingLeague\ibmRacingLeague
#   .\scripts\run_experiment.ps1 016
#
# TORCS must already be running in Window A with scr_server 1 / Corkscrew / 1 lap / New Race.
#
# Defined experiment IDs:
#   016  — lookahead 200m / decel 7.0  (conservative: proves lookahead works)
#   017  — lookahead 150m / decel 9.0  (moderate: tighter brake points)
#   018  — lookahead 120m / decel 11.0 (aggressive: late braking)
#   013r — reproduce Run 013 exactly   (regression check)

param(
    [Parameter(Mandatory=$true)]
    [string]$ExperimentId
)

$segments = "telemetry\segments.yaml"

# --- experiment config table ---
$notes = ""
$driverArgs = ""

switch ($ExperimentId) {
    "016" {
        $notes   = "Run 016 - lookahead 200m/7.0 decel conservative"
        $driverArgs = "--segments $segments --lookahead 200 --lookahead-decel 7.0"
    }
    "017" {
        $notes   = "Run 017 - lookahead 150m/9.0 decel moderate"
        $driverArgs = "--segments $segments --lookahead 150 --lookahead-decel 9.0"
    }
    "018" {
        $notes   = "Run 018 - lookahead 120m/11.0 decel aggressive"
        $driverArgs = "--segments $segments --lookahead 120 --lookahead-decel 11.0"
    }
    "013r" {
        $notes   = "Run 013 regression - s08@95 s09@58 start 2380"
        $driverArgs = "--target-speed 80 --segments $segments"
    }
    default {
        Write-Error "Unknown experiment ID: $ExperimentId"
        Write-Host "Valid IDs: 016, 017, 018, 013r"
        exit 1
    }
}

Write-Host ""
Write-Host "=== Experiment $ExperimentId ===" -ForegroundColor Cyan
Write-Host "Notes  : $notes"
Write-Host "Args   : python src\driver_baseline.py $driverArgs"
Write-Host ""
Write-Host ">>> Window A: TORCS should be at 'Not Responding' (waiting for driver)"
Write-Host ">>> Press ENTER to launch driver, or Ctrl+C to abort"
Read-Host | Out-Null

# --- run driver ---
Invoke-Expression "python src\driver_baseline.py $driverArgs --notes `"$notes`""

# --- analysis ---
Write-Host ""
Write-Host "=== Post-race analysis ===" -ForegroundColor Cyan
$run = (Get-ChildItem telemetry\runs\ | Sort-Object LastWriteTime -Descending | Select-Object -First 1).Name
Write-Host "Run folder: $run"
Write-Host ""

python scripts\validate_run.py telemetry\runs\$run --segments-file telemetry\segments.txt
python scripts\find_offtracks.py telemetry\runs\$run --threshold 1.0
python scripts\segment_report.py telemetry\runs\$run

Write-Host ""
Write-Host "=== Done. Archive with: ===" -ForegroundColor Green
Write-Host "  git add telemetry\runs\$run"
Write-Host "  git commit -m `"telemetry: $ExperimentId archive`""
Write-Host "  git push"
