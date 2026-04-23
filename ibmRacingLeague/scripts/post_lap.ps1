# post_lap.ps1 -- standardized post-lap analysis
# Usage: .\scripts\post_lap.ps1
# Run from repo root after every lap.

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"

$run = (Get-ChildItem telemetry\runs\ | Sort-Object LastWriteTime -Descending | Select-Object -First 1).Name
if (-not $run) { Write-Error "No run archives found."; exit 1 }

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  POST-LAP ANALYSIS -- $run" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Validate
Write-Host "`n[1/3] Validating schema..." -ForegroundColor Yellow
python scripts\validate_run.py telemetry\runs\$run --segments-file telemetry\segments.txt

# 2. Off-tracks
Write-Host "`n[2/3] Scanning for off-tracks..." -ForegroundColor Yellow
python scripts\find_offtracks.py telemetry\runs\$run --threshold 1.0

# 3. Segment report
Write-Host "`n[3/3] Generating segment report..." -ForegroundColor Yellow
python scripts\segment_report.py telemetry\runs\$run

# 4. Checklist
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
Write-Host "     git add telemetry\runs\$run" -ForegroundColor Yellow
Write-Host "     # After screenshot: copy it to docs\screenshots\ then:" -ForegroundColor Gray
Write-Host "     git add docs\screenshots\<screenshot-filename>" -ForegroundColor Yellow
$msg = '     git commit -m "telemetry: ' + $run + ' - <lap-time> <damages>"'
Write-Host $msg -ForegroundColor Yellow
Write-Host "     git push" -ForegroundColor Yellow
Write-Host ""
Write-Host "  3. RESTART TORCS for next run" -ForegroundColor White
Write-Host "     Get-Process wtorcs -ErrorAction SilentlyContinue | Stop-Process -Force" -ForegroundColor Yellow
Write-Host "     cd C:\torcs\torcs; .\wtorcs.exe" -ForegroundColor Yellow
Write-Host "     Race -> Quick Race -> Corkscrew -> scr_server 1 -> 1 lap -> New Race" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
