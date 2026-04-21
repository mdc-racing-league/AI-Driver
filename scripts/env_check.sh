#!/usr/bin/env bash
set -euo pipefail
logfile="/home/workspace/logs/env-check-$(date -u +%Y%m%dT%H%M%SZ).log"
mkdir -p /home/workspace/logs
{
  echo "=== Environment Readiness Check — $(date -u) ==="
  echo "1. Python"
  if command -v python3 >/dev/null 2>&1; then
    python3 --version
    python3 -m pip --version || true
  else
    echo "python3 not installed"
  fi
  echo
  echo "2. TORCS"
  if command -v torcs >/dev/null 2>&1; then
    torcs --version || echo "torcs command found but --version unsupported"
  else
    echo "torcs not installed"
  fi
  echo
  echo "3. Ollama"
  if command -v ollama >/dev/null 2>&1; then
    ollama status
    ollama list || true
  else
    echo "ollama not installed"
  fi
  echo
  echo "4. Granite models"
  if command -v ollama >/dev/null 2>&1; then
    if ollama list | grep -q "granite"; then
      echo "Granite models available"
    else
      echo "No granite models pulled yet"
    fi
  fi
  echo
  echo "5. TORCS data directory check"
  if [ -d "/usr/share/torcs" ] || [ -d "/usr/local/share/torcs" ]; then
    echo "TORCS data directory exists"
  else
    echo "TORCS data directory missing"
  fi
} | tee "$logfile"

echo "Logs saved to $logfile"
