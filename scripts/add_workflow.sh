#!/bin/bash
REPOS=$(cat repos_list.txt)

# GitHub Personal Access Token
source .env

# echo "Using PAT: $PERSONAL_ACCESS_TOKEN"

# Initialize timezone hour counter
TIMEZONE_HOUR=0

# Function to generate full workflow content with specific hour
generate_full_workflow_content() {
  local hour=$1
  cat << EOF
name: Update Worktree and Trigger Workflow

on:
  push:
    branches: [ "main" ]

  schedule:
    - cron: '0 ${hour} * * *'

  workflow_dispatch:

jobs:
  trigger:
    runs-on: ubuntu-latest
    permissions: write-all

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: \${{ secrets.PERSONAL_ACCESS_TOKEN }}
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Download and run collect_worktree_info.py
        run: |
          # Download the script
          curl -o collect_worktree_info.py \
            https://raw.githubusercontent.com/HITSZ-OpenAuto/repos-management/main/scripts/collect_worktree_info.py
          
          # Make it executable and run it
          chmod +x collect_worktree_info.py
          python3 collect_worktree_info.py
          
          # Clean up the downloaded script
          rm collect_worktree_info.py
      
      - name: Commit worktree info changes
        run: |
          # Configure git
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Actions"
          
          # Add changes if any exist
          if [ -n "\$(git status --porcelain)" ]; then
            git add .hoa/worktree.json
            git commit -m "Update worktree [skip ci]"
            git push origin main
            echo "Worktree updated and committed to main branch"
          else
            echo "No changes to commit"
          fi

      - name: Trigger workflow in hoa-moe
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        env:
          GITHUB_TOKEN: \${{ secrets.PERSONAL_ACCESS_TOKEN }}
        run: |
          curl -X POST \\
            -H "Accept: application/vnd.github.v3+json" \\
            -H "Authorization: token \$GITHUB_TOKEN" \\
            https://api.github.com/repos/HITSZ-OpenAuto/hoa-moe/actions/workflows/course.yaml/dispatches \\
            -d '{"ref":"main"}'

EOF
}

# Initialize timezone hour counter
TIMEZONE_HOUR=0

# Loop through the repositories and add the workflow file via PR
for REPO in $REPOS; do
  echo "Processing $REPO (timezone hour: $TIMEZONE_HOUR)"
  
  # Generate workflow content with current timezone hour
  WORKFLOW_CONTENT=$(generate_full_workflow_content $TIMEZONE_HOUR)
  
  BRANCH_NAME="update-worktree-workflow"
  # Get the latest commit SHA of the main branch
  MAIN_SHA=$(gh api -H "Authorization: token $PERSONAL_ACCESS_TOKEN" "/repos/HITSZ-OpenAuto/$REPO/git/ref/heads/main" -q '.object.sha')

  # Check if the branch already exists
  BRANCH_CHECK_RESULT=$(gh api -H "Authorization: token $PERSONAL_ACCESS_TOKEN" "/repos/HITSZ-OpenAuto/$REPO/git/ref/heads/$BRANCH_NAME" 2>&1)
  BRANCH_CHECK_EXIT_CODE=$?
  
  if [ $BRANCH_CHECK_EXIT_CODE -eq 0 ]; then
    echo "Branch $BRANCH_NAME already exists, skipping branch creation"
    BRANCH_EXISTS="true"
  else
    echo "Creating new branch: $BRANCH_NAME"
    # Create a new branch
    CREATE_RESULT=$(gh api -X POST \
      -H "Authorization: token $PERSONAL_ACCESS_TOKEN" \
      -H "Accept: application/vnd.github.v3+json" \
      "/repos/HITSZ-OpenAuto/$REPO/git/refs" \
      -f ref="refs/heads/$BRANCH_NAME" \
      -f sha="$MAIN_SHA" 2>&1)
    CREATE_EXIT_CODE=$?
    
    if [ $CREATE_EXIT_CODE -eq 0 ]; then
      echo "Branch created successfully"
      BRANCH_EXISTS="true"
    else
      echo "Failed to create branch: $CREATE_RESULT"
      continue
    fi
  fi

  # Get the SHA of the existing workflow file if it exists
  # Try to get file SHA from the branch first, fall back to main, or use empty if doesn't exist
  FILE_SHA=$(gh api -H "Authorization: token $PERSONAL_ACCESS_TOKEN" "/repos/HITSZ-OpenAuto/$REPO/contents/.github/workflows/trigger-workflow.yml?ref=$BRANCH_NAME" -q '.sha' 2>/dev/null || \
             gh api -H "Authorization: token $PERSONAL_ACCESS_TOKEN" "/repos/HITSZ-OpenAuto/$REPO/contents/.github/workflows/trigger-workflow.yml" -q '.sha' 2>/dev/null || \
             echo "")
  
  if [ -n "$FILE_SHA" ]; then
    echo "Found existing workflow file with SHA: $FILE_SHA"
  else
    echo "No existing workflow file found, creating new file"
  fi

  # Create or update the workflow file in the branch
  WORKFLOW_CONTENT_BASE64=$(echo "$WORKFLOW_CONTENT" | base64)
  
  if [ -n "$FILE_SHA" ]; then
    echo "Updating existing workflow file..."
    UPDATE_RESULT=$(gh api -X PUT \
      -H "Authorization: token $PERSONAL_ACCESS_TOKEN" \
      -H "Accept: application/vnd.github.v3+json" \
      "/repos/HITSZ-OpenAuto/$REPO/contents/.github/workflows/trigger-workflow.yml" \
      -f message="ci: fix permission issue in workflow" \
      -f content="$WORKFLOW_CONTENT_BASE64" \
      -f branch="$BRANCH_NAME" \
      -f sha="$FILE_SHA" 2>&1)
  else
    echo "Creating new workflow file..."
    UPDATE_RESULT=$(gh api -X PUT \
      -H "Authorization: token $PERSONAL_ACCESS_TOKEN" \
      -H "Accept: application/vnd.github.v3+json" \
      "/repos/HITSZ-OpenAuto/$REPO/contents/.github/workflows/trigger-workflow.yml" \
      -f message="ci: fix permission issue in workflow" \
      -f content="$WORKFLOW_CONTENT_BASE64" \
      -f branch="$BRANCH_NAME" 2>&1)
  fi
  
  UPDATE_EXIT_CODE=$?
  if [ $UPDATE_EXIT_CODE -eq 0 ]; then
    echo "Workflow file updated successfully for $REPO"
  else
    echo "Failed to update workflow file for $REPO: $UPDATE_RESULT"
    continue
  fi

  # Create a pull request
  PR_RESULT=$(gh pr create -R "HITSZ-OpenAuto/$REPO" -B main -H "$BRANCH_NAME" -t "ci: fix permission issue in workflow" -b "更新后的 workflow 文件会生成一份 worktree 信息" 2>&1)
  PR_EXIT_CODE=$?
  
  if [ $PR_EXIT_CODE -eq 0 ]; then
    echo "PR created successfully for $REPO: $PR_RESULT"
  else
    echo "Failed to create PR for $REPO (might already exist): $PR_RESULT"
  fi
  
  # Increment timezone hour and reset after 23
  TIMEZONE_HOUR=$((TIMEZONE_HOUR + 1))
  if [ $TIMEZONE_HOUR -gt 23 ]; then
    TIMEZONE_HOUR=0
  fi
done
