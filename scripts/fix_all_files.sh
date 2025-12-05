#!/bin/bash
# Fix Pulumi config files and add GitHub Actions workflows

set -e

echo "🔧 Fixing IPAM Serverless project files..."
echo ""

cd ~/Pulumi_projects/ipam-serverless

# Backup current files
echo "📦 Creating backups..."
cp Pulumi.yaml Pulumi.yaml.backup 2>/dev/null || true
cp Pulumi.dev.yaml Pulumi.dev.yaml.backup 2>/dev/null || true
echo "  ✅ Backed up existing Pulumi files"

# Create proper Pulumi.yaml
echo "📝 Creating proper Pulumi.yaml..."
cat > Pulumi.yaml << 'EOF'
name: ipam-serverless
runtime:
  name: python
  options:
    virtualenv: venv
description: Production-ready serverless IP Address Management (IPAM) system with AWS Lambda, DynamoDB, and API Gateway
main: __main__.py
EOF
echo "  ✅ Created Pulumi.yaml"

# Create proper Pulumi.dev.yaml
echo "📝 Creating proper Pulumi.dev.yaml..."
cat > Pulumi.dev.yaml << 'EOF'
config:
  aws:region: us-east-1
  ipam-serverless:environment: development
EOF
echo "  ✅ Created Pulumi.dev.yaml"

# Create optional Pulumi.prod.yaml
echo "📝 Creating Pulumi.prod.yaml (optional)..."
cat > Pulumi.prod.yaml << 'EOF'
config:
  aws:region: us-east-1
  ipam-serverless:environment: production
EOF
echo "  ✅ Created Pulumi.prod.yaml"

# Create GitHub Actions workflows
echo "📋 Creating GitHub Actions workflows..."
mkdir -p .github/workflows

# Create test.yml (in case it's also wrong)
cat > .github/workflows/test.yml << 'EOF'
name: Tests

on:
  push:
    branches: [ main, dev ]
  pull_request:
    branches: [ main, dev ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Cache pip dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/pyproject.toml') }}
        restore-keys: |
          ${{ runner.os }}-pip-

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"

    - name: Run Black (code formatter check)
      run: |
        black --check .

    - name: Run Pylint (linting)
      run: |
        pylint lambda_functions infrastructure --exit-zero

    - name: Run Bandit (security scan)
      run: |
        bandit -r lambda_functions infrastructure -f json -o bandit-report.json || true
        bandit -r lambda_functions infrastructure

    - name: Run unit tests
      run: |
        pytest tests/unit --cov=lambda_functions --cov=infrastructure --cov-report=xml --cov-report=term

    - name: Run integration tests
      run: |
        pytest tests/integration --cov=lambda_functions --cov-report=xml --cov-report=term
      env:
        AWS_DEFAULT_REGION: us-east-1

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
        fail_ci_if_error: false

    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: test-results-${{ matrix.python-version }}
        path: |
          htmlcov/
          bandit-report.json
          coverage.xml
EOF
echo "  ✅ Created test.yml"

# Create deploy-dev.yml
cat > .github/workflows/deploy-dev.yml << 'EOF'
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
echo "  ✅ Created deploy-dev.yml"

# Create deploy-prod.yml
cat > .github/workflows/deploy-prod.yml << 'EOF'
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
echo "  ✅ Created deploy-prod.yml"

echo ""
echo "✅ All files created successfully!"
echo ""
echo "📂 File locations:"
echo "  - Pulumi.yaml (root)"
echo "  - Pulumi.dev.yaml (root)"
echo "  - Pulumi.prod.yaml (root)"
echo "  - .github/workflows/test.yml"
echo "  - .github/workflows/deploy-dev.yml"
echo "  - .github/workflows/deploy-prod.yml"
echo ""
echo "⚠️  IMPORTANT: Edit .github/workflows/deploy-prod.yml"
echo "   Change 'yourgithubusername' to your actual GitHub username!"
echo ""
echo "🧪 Next steps:"
echo "  1. Edit deploy-prod.yml (change GitHub username)"
echo "  2. Test Pulumi: pulumi preview"
echo "  3. Test workflows: git add . && git commit && git push"