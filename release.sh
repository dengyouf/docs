#!/usr/bin/env bash
# 构建并发布文档站点
# 发布信息（版本 / 提交者 / 摘要）通过环境变量注入 overrides/main.html 的顶部通告栏，
# 不再回写源文件，避免每次发布都把仓库搞脏。
set -euo pipefail

baseDir="$(cd "$(dirname "$0")" && pwd)"
cd "$baseDir"

# 有未提交改动时提示一下，发布信息仍以最后一次提交为准
if [ -n "$(git status --porcelain)" ]; then
  echo "⚠️  工作区存在未提交的改动，发布信息以最后一次提交为准"
fi

export GIT_COMMIT_HASH="$(git log -1 --pretty=format:'%h')"
export GIT_COMMIT_DATE="$(git log -1 --pretty=format:'%ci')"
export GIT_COMMIT_AUTHOR="$(git log -1 --pretty=format:'%ae')"
export GIT_COMMIT_MESSAGE="$(git log -1 --pretty=format:'%s')"
# 用于 sitemap / canonical 的站点地址，部署时按实际域名覆盖
export SITE_URL="${SITE_URL:-http://127.0.0.1:8000/}"

echo "构建: ${GIT_COMMIT_HASH} @ ${GIT_COMMIT_DATE}"

# 容器内构建（需要镜像时打开）
# docker run --rm -v "${baseDir}:/docs" \
#   -e SITE_URL -e GIT_COMMIT_HASH -e GIT_COMMIT_DATE \
#   -e GIT_COMMIT_AUTHOR -e GIT_COMMIT_MESSAGE \
#   harbor.devops.io/library/mkdocs-material:v9.6 build

mkdocs build

RSYNC_TARGET="${RSYNC_TARGET:-root@172.16.162.250:/var/www/html}"
rsync -av --delete --exclude=pdf/ site/ "${RSYNC_TARGET}"
