#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Sync a Lovable-generated GitHub repository into `frontend/` in our monorepo
# Usage: ./scripts/sync_lovable.sh https://github.com/<org>/<lovable-repo>.git
# ==============================================================================

if [ $# -lt 1 ]; then
  echo "Usage: ./scripts/sync_lovable.sh <lovable-github-repo-url> [branch]"
  exit 1
fi

LOVABLE_REPO_URL="$1"
LOVABLE_BRANCH="${2:-main}"

echo "🔄 Fetching Lovable repository (${LOVABLE_REPO_URL}, branch: ${LOVABLE_BRANCH})..."
if ! git remote get-url lovable >/dev/null 2>&1; then
  git remote add lovable "${LOVABLE_REPO_URL}"
else
  git remote set-url lovable "${LOVABLE_REPO_URL}"
fi

git fetch lovable "${LOVABLE_BRANCH}"

echo "📦 Merging Lovable updates into frontend/ while preserving shared API contracts..."
git merge -s ours --no-commit --allow-unrelated-histories "lovable/${LOVABLE_BRANCH}" || true
git read-tree --prefix=frontend/ -u "lovable/${LOVABLE_BRANCH}" || true

# Ensure our frozen contract files stay intact
git checkout HEAD -- frontend/src/types/api.ts frontend/src/mocks/mockData.ts frontend/src/api/client.ts 2>/dev/null || true

echo "✅ Lovable sync staged in frontend/. Review with 'git status' and commit!"
