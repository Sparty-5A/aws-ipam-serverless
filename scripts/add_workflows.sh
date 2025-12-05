#!/bin/bash
# Add missing GitHub Actions workflows

cd ~/Pulumi_projects/ipam-serverless/.github/workflows

# Create deploy-dev.yml
cat > deploy-dev.yml << 'EOF'
name: Deploy to Dev

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ dev ]

jobs:
  deploy-dev:
    runs-on: ubuntu-latest
    environment: development

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pulumi pulumi-aws

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1

    - name: Install Pulumi CLI
      uses: pulumi/actions@v5

    - name: Select Pulumi stack (dev)
      run: |
        pulumi login --local
        pulumi stack select dev || pulumi stack init dev
      working-directory: .

    - name: Pulumi preview (dry-run)
      run: |
        pulumi preview --diff --stack dev
      working-directory: .
      env:
        PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}

    - name: Pulumi up (deploy)
      run: |
        pulumi up --yes --stack dev
      working-directory: .
      env:
        PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}

    - name: Get API Gateway URL
      id: outputs
      run: |
        API_URL=$(pulumi stack output api_gateway_url --stack dev)
        echo "api_url=$API_URL" >> $GITHUB_OUTPUT
      working-directory: .
      env:
        PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}

    - name: Run smoke tests
      run: |
        curl -f ${{ steps.outputs.outputs.api_url }}/health || exit 1
        echo "✅ Dev environment deployed successfully!"

    - name: Comment on PR
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v7
      with:
        script: |
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: `✅ Dev deployment succeeded!\n\n**API Gateway URL:** ${{ steps.outputs.outputs.api_url }}\n\nTest the changes before merging.`
          })
EOF

# Create deploy-prod.yml
cat > deploy-prod.yml << 'EOF'
name: Deploy to Production

on:
  push:
    branches: [ main ]
  workflow_dispatch:  # Allow manual trigger

jobs:
  deploy-prod:
    runs-on: ubuntu-latest
    environment: production

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pulumi pulumi-aws

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1

    - name: Install Pulumi CLI
      uses: pulumi/actions@v5

    - name: Select Pulumi stack (prod)
      run: |
        pulumi login --local
        pulumi stack select prod || pulumi stack init prod
      working-directory: .

    - name: Pulumi preview (dry-run)
      run: |
        pulumi preview --diff --stack prod
      working-directory: .
      env:
        PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}

    - name: Wait for approval
      uses: trstringer/manual-approval@v1
      if: github.event_name != 'workflow_dispatch'
      with:
        secret: ${{ github.TOKEN }}
        approvers: yourgithubusername
        minimum-approvals: 1
        issue-title: "Approve Production Deployment"
        issue-body: "Please review the Pulumi preview and approve deployment to production."

    - name: Pulumi up (deploy)
      run: |
        pulumi up --yes --stack prod
      working-directory: .
      env:
        PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}

    - name: Get API Gateway URL
      id: outputs
      run: |
        API_URL=$(pulumi stack output api_gateway_url --stack prod)
        echo "api_url=$API_URL" >> $GITHUB_OUTPUT
      working-directory: .
      env:
        PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}

    - name: Run smoke tests
      run: |
        curl -f ${{ steps.outputs.outputs.api_url }}/health || exit 1
        echo "✅ Production deployment successful!"

    - name: Create release tag
      if: success()
      run: |
        TAG="v$(date +'%Y.%m.%d')-${{ github.run_number }}"
        git tag $TAG
        git push origin $TAG
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

    - name: Send Slack notification (optional)
      if: always()
      run: |
        echo "Production deployment completed!"
        echo "Status: ${{ job.status }}"
        echo "API URL: ${{ steps.outputs.outputs.api_url }}"
        # Add Slack webhook here if desired
EOF

echo "✅ Created deploy-dev.yml"
echo "✅ Created deploy-prod.yml"
echo ""
echo "⚠️  IMPORTANT: Edit deploy-prod.yml and change 'yourgithubusername' to your actual GitHub username!"
echo ""
ls -la