#!/bin/zsh

# List of repositories
REPOS=$(cat repos_list2.txt)

# GitHub Personal Access Token
PAT=$(cat .env)

# Workflow content
read -r -d '' WORKFLOW_CONTENT << 'EOF'
name: Trigger Workflow in hoa.moe

on:
  push:
    branches:
      - main

jobs:
  trigger:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger workflow in hoa.moe
        env:
          GITHUB_TOKEN: ${{ secrets.PERSONAL_ACCESS_TOKEN }}
        run: |
          curl -X POST \
            -H "Accept: application/vnd.github.v3+json" \
            -H "Authorization: token $GITHUB_TOKEN" \
            https://api.github.com/repos/HITSZ-OpenAuto/hoa.moe/actions/workflows/course.yaml/dispatches \
            -d '{"ref":"main"}'
EOF

# Loop through the repositories and add the workflow file via PR
for REPO in $REPOS; do
  echo "Processing $REPO"

  # Get the latest commit SHA of the main branch
  MAIN_SHA=$(gh api -H "Authorization: token $PAT" "/repos/HITSZ-OpenAuto/$REPO/git/ref/heads/main" -q '.object.sha')

  # Create a new branch
  BRANCH_NAME="add-trigger-workflow"
  gh api -X POST \
    -H "Authorization: token $PAT" \
    -H "Accept: application/vnd.github.v3+json" \
    "/repos/HITSZ-OpenAuto/$REPO/git/refs" \
    -f ref="refs/heads/$BRANCH_NAME" \
    -f sha="$MAIN_SHA"

  # Create the workflow file in the new branch
  WORKFLOW_CONTENT_BASE64=$(echo "$WORKFLOW_CONTENT" | base64)
  gh api -X PUT \
    -H "Authorization: token $PAT" \
    -H "Accept: application/vnd.github.v3+json" \
    "/repos/HITSZ-OpenAuto/$REPO/contents/.github/workflows/trigger-workflow.yml" \
    -f message="Add trigger workflow" \
    -f content="$WORKFLOW_CONTENT_BASE64" \
    -f branch="$BRANCH_NAME"

  # Create a pull request
  gh pr create -R "HITSZ-OpenAuto/$REPO" -B main -H "$BRANCH_NAME" -t " git push 推送自动触发网站更新" -b "这个 PR 用于添加一个触发 hoa.moe 网站更新的 GitHub Actions workflow"

  echo "PR created for $REPO"
done
