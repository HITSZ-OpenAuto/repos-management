#!/bin/zsh

# GitHub Organization name and Personal Access Token (PAT)
ORG="HITSZ-OpenAuto"
PAT="Your GitHub PAT with repo and workflow permissions"

# File path to modify in the repositories
FILE_PATH=".github/workflows/trigger-workflow.yml"
BRANCH_NAME="replace-hoa-moe-with-hoa-moe"

# Function to replace string and create a PR for each repository
replace_string_and_create_pr() {
    REPO_NAME=$1

    # Step 1: Check if the file exists in the repository
    if gh api repos/$ORG/$REPO_NAME/contents/$FILE_PATH > /dev/null 2>&1; then
        echo "File $FILE_PATH found in $REPO_NAME. Proceeding..."

        # Step 2: Create a new branch using GitHub CLI
        gh repo clone $ORG/$REPO_NAME -- -q
        cd $REPO_NAME
        git checkout -b $BRANCH_NAME

        # Replace "hoa.moe" with "hoa-moe" using sed
        sed -i '' 's/hoa\.moe/hoa-moe/g' $FILE_PATH

        # Step 4: Check if any changes were made
        if git diff --quiet; then
            echo "No changes detected in $REPO_NAME. Skipping PR creation."
            cd ..
            rm -rf $REPO_NAME
            return
        fi

        # Step 5: Update the file in the repository
        echo "Changes detected. Committing and pushing..."
        git add $FILE_PATH
        git commit -m "Replace hoa.moe with hoa-moe in $FILE_PATH"
        git push origin $BRANCH_NAME

        # Step 6: Create a pull request
        gh pr create --repo $ORG/$REPO_NAME --head $BRANCH_NAME --base main \
            --title "Replace hoa.moe with hoa-moe" \
            --body "This PR replaces all occurrences of 'hoa.moe' with 'hoa-moe' in $FILE_PATH."

        # Step 7: Cleanup
        cd ..
        rm -rf $REPO_NAME

    else
        echo "File $FILE_PATH not found in $REPO_NAME. Skipping..."
    fi
}

# Get the list of repositories in the organization
REPOS=$(gh api orgs/$ORG/repos --paginate -q '.[].name')

# Loop through each repository and replace the string
for REPO in $REPOS; do
    replace_string_and_create_pr $REPO
done
