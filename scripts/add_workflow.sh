#!/bin/bash
REPOS=$(cat repos_list.txt)

# GitHub Personal Access Token
source .env

# echo "Using PAT: $PERSONAL_ACCESS_TOKEN"

# Workflow content
read -r -d '' WORKFLOW_CONTENT << 'EOF'
name: Trigger Workflow in hoa-moe

on:
  push:
    branches:
      - main

jobs:
  trigger:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger workflow in hoa-moe
        env:
          GITHUB_TOKEN: ${{ secrets.PERSONAL_ACCESS_TOKEN }}
        run: |
          REPO_NAME=$(echo ${{ github.repository }} | cut -d'/' -f2)
          echo ${REPO_NAME}
          curl -X POST \
            -H "Accept: application/vnd.github.v3+json" \
            -H "Authorization: token $GITHUB_TOKEN" \
            https://api.github.com/repos/HITSZ-OpenAuto/hoa-moe/actions/workflows/course.yaml/dispatches \
            -d '{"ref":"main","inputs": {"repo_name": "'"${REPO_NAME}"'"}}'
EOF

# Loop through the repositories and add the workflow file via PR
for REPO in $REPOS; do
  echo "Processing $REPO"
  BRANCH_NAME="update-trigger-workflow"
  # Get the latest commit SHA of the main branch
  MAIN_SHA=$(gh api -H "Authorization: token $PERSONAL_ACCESS_TOKEN" "/repos/HITSZ-OpenAuto/$REPO/git/ref/heads/main" -q '.object.sha')

  # Create a new branch
  gh api -X POST \
    -H "Authorization: token $PERSONAL_ACCESS_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "/repos/HITSZ-OpenAuto/$REPO/git/refs" \
    -f ref="refs/heads/$BRANCH_NAME" \
    -f sha="$MAIN_SHA"

  # Get the SHA of the existing workflow file if it exists
  FILE_SHA=$(gh api -H "Authorization: token $PERSONAL_ACCESS_TOKEN" "/repos/HITSZ-OpenAuto/$REPO/contents/.github/workflows/trigger-workflow.yml" -q '.sha' || echo "")

  # Create or update the workflow file in the new branch
  WORKFLOW_CONTENT_BASE64=$(echo "$WORKFLOW_CONTENT" | base64)
  gh api -X PUT \
    -H "Authorization: token $PERSONAL_ACCESS_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "/repos/HITSZ-OpenAuto/$REPO/contents/.github/workflows/trigger-workflow.yml" \
    -f message="Add trigger workflow" \
    -f content="$WORKFLOW_CONTENT_BASE64" \
    -f branch="$BRANCH_NAME" \
    -f sha="$FILE_SHA"

  # Create a pull request
  gh pr create -R "HITSZ-OpenAuto/$REPO" -B main -H "$BRANCH_NAME" -t "更新触发 hoa-moe 仓库更新的 GitHub Actions workflow" -b "更新后的 workflow 文件会触发 hoa-moe 仓库的 Build Documentation workflow"

  echo "PR created for $REPO"
done
