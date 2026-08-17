#!/usr/bin/env bash
#
# FAUE workspace bootstrap.
#
# Clones missing repositories and updates existing ones, driven by repos.yaml.
# The workspace root is deliberately NOT a git repository — this script is the
# monorepo substitute.
#
# Usage:
#   ./scripts/bootstrap.sh            clone missing, fast-forward existing
#   ./scripts/bootstrap.sh --status   report branch and dirty state, change nothing
#   ./scripts/bootstrap.sh --stage MVP  operate only on repos at the given stage
#
# Safe to re-run. Never force-pushes, never discards local work, never runs
# `git init` at the workspace root.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCS_DIR="$(dirname "$SCRIPT_DIR")"
WORKSPACE="$(dirname "$DOCS_DIR")"
MANIFEST="$DOCS_DIR/repos.yaml"

MODE="sync"
STAGE_FILTER=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --status) MODE="status"; shift ;;
    --stage)  STAGE_FILTER="${2:-}"; shift 2 ;;
    -h|--help)
      sed -n '3,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

[[ -f "$MANIFEST" ]] || { echo "manifest not found: $MANIFEST" >&2; exit 1; }
command -v git >/dev/null || { echo "git is required" >&2; exit 1; }
command -v python3 >/dev/null || { echo "python3 is required to parse the manifest" >&2; exit 1; }

red()   { printf '\033[31m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
dim()   { printf '\033[2m%s\033[0m\n' "$*"; }

# Emit "dir<TAB>repo<TAB>stage" per repository. Uses PyYAML when available and
# falls back to a minimal parser so a fresh machine needs no pip install first.
read_manifest() {
  python3 - "$MANIFEST" <<'PY'
import sys, re
path = sys.argv[1]
try:
    import yaml
    data = yaml.safe_load(open(path))
    base = data.get("remote_base", "")
    for r in data.get("repos", []):
        print("\t".join([r["dir"], r["repo"], r.get("stage", ""), base]))
except ImportError:
    text = open(path).read()
    base = ""
    m = re.search(r"^remote_base:\s*(\S+)", text, re.M)
    if m:
        base = m.group(1)
    block = text.split("\nrepos:", 1)[1].split("\nplanned:", 1)[0]
    entries = re.split(r"\n  - ", block)
    for e in entries[1:]:
        d = re.search(r"dir:\s*(\S+)", e)
        r = re.search(r"repo:\s*(\S+)", e)
        s = re.search(r"stage:\s*(\S+)", e)
        if d and r:
            print("\t".join([d.group(1), r.group(1), s.group(1) if s else "", base]))
PY
}

failures=0

while IFS=$'\t' read -r dir repo stage base; do
  [[ -n "$dir" ]] || continue
  if [[ -n "$STAGE_FILTER" && "$stage" != "$STAGE_FILTER" ]]; then
    continue
  fi

  target="$WORKSPACE/$dir"
  remote="$base/$repo.git"

  if [[ "$MODE" == "status" ]]; then
    if [[ -d "$target/.git" ]]; then
      branch="$(git -C "$target" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
      if [[ -n "$(git -C "$target" status --porcelain 2>/dev/null)" ]]; then
        red   "  dirty    $dir ($branch)"
      else
        green "  clean    $dir ($branch)"
      fi
    else
      dim   "  missing  $dir  ->  $remote"
    fi
    continue
  fi

  if [[ -d "$target/.git" ]]; then
    if [[ -n "$(git -C "$target" status --porcelain)" ]]; then
      red "  skipped  $dir — uncommitted changes, not touching it"
      continue
    fi
    if git -C "$target" pull --ff-only --quiet; then
      green "  updated  $dir"
    else
      red   "  failed   $dir — pull was not a fast-forward, resolve manually"
      failures=$((failures + 1))
    fi
  elif [[ -e "$target" ]]; then
    red "  skipped  $dir — path exists but is not a git repository"
  else
    if git clone --quiet "$remote" "$target"; then
      green "  cloned   $dir"
    else
      red   "  failed   $dir — clone from $remote"
      failures=$((failures + 1))
    fi
  fi
done < <(read_manifest)

if [[ "$MODE" == "sync" ]]; then
  echo
  if [[ $failures -eq 0 ]]; then
    green "workspace is in sync"
  else
    red "$failures repository operation(s) failed"
    exit 1
  fi
fi
