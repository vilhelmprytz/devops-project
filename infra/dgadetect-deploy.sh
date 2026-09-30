#!/usr/bin/env bash
# Usage: dgadetect-deploy VERSION
#
# Runs ghcr.io/vilhelmprytz/devops-project:VERSION as the "dgadetect" container.
# If /health doesn't report that version within 60 seconds, the previous image
# is started again and the script exits with 1.
set -euo pipefail

version=${1:?usage: dgadetect-deploy VERSION}
[[ $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "not a version: $version" >&2; exit 2; }
image="${IMAGE:-ghcr.io/vilhelmprytz/devops-project}:$version"
name=dgadetect

healthy() { # healthy VERSION SECONDS
  local body
  for _ in $(seq "$2"); do
    body=$(curl -fsS localhost:8000/health 2>/dev/null || true)
    [[ $body == *"\"version\":\"$1\""* ]] && return 0
    sleep 1
  done
  return 1
}

start() {
  docker rm -f "$name" >/dev/null 2>&1 || true
  docker run -d --name "$name" --restart unless-stopped -p 8000:8000 "$1" >/dev/null
}

previous=$(docker inspect --format '{{.Config.Image}}' "$name" 2>/dev/null || true)
if [[ $previous == "$image" ]] && healthy "$version" 2; then
  echo "already running $version"
  exit 0
fi

docker pull --quiet "$image"
start "$image"
if healthy "$version" 60; then
  echo "deployed $version"
  exit 0
fi

echo "$version did not become healthy; last log lines:" >&2
docker logs --tail 20 "$name" >&2 || true
if [[ -n $previous && $previous != "$image" ]]; then
  echo "rolling back to $previous" >&2
  start "$previous"
  if healthy "${previous##*:}" 60; then
    echo "rolled back to ${previous##*:}" >&2
  else
    echo "rollback to ${previous##*:} is not healthy either" >&2
  fi
fi
exit 1
