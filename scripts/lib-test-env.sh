#!/usr/bin/env bash

hb_repo_root() {
  git rev-parse --show-toplevel
}

hb_select_python() {
  if [ -x ".venv/bin/python" ]; then
    printf '%s\n' ".venv/bin/python"
  else
    printf '%s\n' "python"
    printf '%s\n' "Using fallback python from PATH because .venv/bin/python is not available." >&2
  fi
}

hb_run_pytest() {
  local python
  python="$(hb_select_python)"
  "$python" -m pytest "$@" -q
}

hb_fast_fingerprint() {
  {
    git rev-parse HEAD
    git ls-files --cached --others --exclude-standard | sort | while IFS= read -r path; do
      [ -n "$path" ] || continue
      if [ -f "$path" ]; then
        printf 'file %s\n' "$path"
        git hash-object -- "$path"
      else
        printf 'missing %s\n' "$path"
      fi
    done
  } | shasum -a 256 | awk '{print $1}'
}

hb_fast_stamp_path() {
  printf '%s\n' ".pytest_cache/harness-builder-test-fast.stamp"
}

hb_write_fast_stamp() {
  local stamp_path tmp_path
  stamp_path="$(hb_fast_stamp_path)"
  mkdir -p "$(dirname "$stamp_path")"
  tmp_path="${stamp_path}.$$"
  {
    printf 'fingerprint=%s\n' "$(hb_fast_fingerprint)"
    printf 'recorded_at=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  } > "$tmp_path"
  mv "$tmp_path" "$stamp_path"
}

hb_fast_stamp_matches() {
  local stamp_path expected actual
  stamp_path="$(hb_fast_stamp_path)"
  [ -f "$stamp_path" ] || return 1
  expected="$(sed -n 's/^fingerprint=//p' "$stamp_path" | head -n 1)"
  [ -n "$expected" ] || return 1
  actual="$(hb_fast_fingerprint)"
  [ "$expected" = "$actual" ]
}
