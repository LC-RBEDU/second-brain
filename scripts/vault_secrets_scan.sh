#!/usr/bin/env bash
# F1-f hard gate (B21 / A15): fail on high-confidence secrets before vault import.
set -euo pipefail

ROOT="${1:-.}"
if [[ ! -d "$ROOT" ]]; then
  echo "usage: $0 <vault-root-dir>" >&2
  exit 2
fi

TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT

PAT1='-----BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY-----'
PAT2='xox[baprs]-[0-9A-Za-z-]{10,}'
PAT3='ghp_[0-9A-Za-z]{36}'
PAT4='github_pat_[0-9A-Za-z_]{20,}'
PAT5='AKIA[0-9A-Z]{16}'
PAT6='AIza[0-9A-Za-z_-]{35}'
PAT7='sk-[A-Za-z0-9]{20,}'

search() {
  if command -v rg >/dev/null 2>&1; then
    # macOS/homebrew rg uses --binary (not GNU --binary-files)
    rg -n --binary \
      -e "$PAT1" -e "$PAT2" -e "$PAT3" -e "$PAT4" -e "$PAT5" -e "$PAT6" -e "$PAT7" \
      "$ROOT" || true
  else
    # Fallback: grep -R (may be slower; still a hard gate)
    grep -RInE -e "$PAT1" -e "$PAT2" -e "$PAT3" -e "$PAT4" -e "$PAT5" -e "$PAT6" -e "$PAT7" \
      "$ROOT" 2>/dev/null || true
  fi
}

search >"$TMP"

if [[ -s "$TMP" ]]; then
  echo "vault_secrets_scan: FAIL — high-confidence token patterns found:" >&2
  head -n 50 "$TMP" >&2
  echo "(exclude false-positive only with explicit user OK — A15)" >&2
  exit 1
fi

echo "vault_secrets_scan: OK — no high-confidence secrets in $ROOT"
exit 0
