# 🚀 IPAM Serverless - Setup & Installation Guide

Complete guide to setting up the IPAM Serverless project with CI/CD pipeline.

---

## 📋 Prerequisites

### Required Software

- **Python 3.9 or higher** ([Download](https://www.python.org/downloads/))
- **AWS CLI** ([Install Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html))
- **Pulumi CLI** ([Install Guide](https://www.pulumi.com/docs/get-started/install/))
- **Git** ([Download](https://git-scm.com/downloads))

### AWS Account Setup

1. **Create AWS Account** (if you don't have one)
2. **Create IAM User** with programmatic access
3. **Attach policies**:
   - `AWSLambdaFullAccess`
   - `AmazonDynamoDBFullAccess`
   - `AmazonAPIGatewayAdministrator`
   - `CloudWatchLogsFullAccess`
4. **Save credentials**:
   - Access Key ID
   - Secret Access Key

---

## 🛠️ Installation Steps

### 1. Clone Repository

```bash
# If you haven't created a GitHub repo yet, initialize it
cd ~/Pulumi_projects/ipam-serverless
git init
git add .
git commit -m "Initial commit: IPAM Serverless project"

# Create GitHub repo (via GitHub web interface or CLI)
# Then push
git remote add origin https://github.com/yourusername/ipam-serverless.git
git push -u origin main
```

### 2. Configure AWS Credentials

```bash
# Configure AWS CLI
aws configure

# Enter when prompted:
AWS Access Key ID: YOUR_ACCESS_KEY
AWS Secret Access Key: YOUR_SECRET_KEY
Default region name: us-east-1
Default output format: json

# Verify configuration
aws sts get-caller-identity
```

### 3. Install Python Dependencies

```bash
cd ~/Pulumi_projects/ipam-serverless

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install project in development mode
pip install -e ".[dev]"

# Or install from requirements.txt
pip install -r requirements.txt
```

### 4. Initialize Pulumi

```bash
# Login to Pulumi (local state storage)
pulumi login --local

# Or use Pulumi Cloud (free tier available)
pulumi login

# Create dev stack
pulumi stack init dev

# Set AWS region
pulumi config set aws:region us-east-1

# View current configuration
pulumi config
```

### 5. Deploy Infrastructure

```bash
# Preview changes
pulumi preview

# Deploy to AWS
pulumi up

# Type 'yes' when prompted

# Save outputs
API_URL=$(pulumi stack output api_gateway_url)
echo "API Gateway URL: $API_URL"
```

---

## 🔧 Setting Up CI/CD

### 1. Add Files to Project

Copy these files into your project:

```bash
# Create .github/workflows directory
mkdir -p .github/workflows

# Add workflow files
cp path/to/test.yml .github/workflows/
cp path/to/deploy-dev.yml .github/workflows/
cp path/to/deploy-prod.yml .github/workflows/

# Add other files
cp path/to/pyproject.toml .
cp path/to/.gitignore .
cp path/to/requirements.txt .

# Create test directories
mkdir -p tests/unit tests/integration tests/fixtures

# Add test files
cp path/to/test_*.py tests/unit/
cp path/to/test_api_integration.py tests/integration/
```

### 2. Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

**Add these secrets:**

1. **AWS_ACCESS_KEY_ID**
   - Value: Your AWS Access Key ID

2. **AWS_SECRET_ACCESS_KEY**
   - Value: Your AWS Secret Access Key

3. **PULUMI_ACCESS_TOKEN** (optional, if using Pulumi Cloud)
   - Get from: https://app.pulumi.com/account/tokens
   - Click "Create token"
   - Copy and save as secret

### 3. Update Workflow Files

Edit `.github/workflows/*.yml` files:

**In deploy-prod.yml**, update line with `approvers`:
```yaml
approvers: your-github-username  # Replace with YOUR username
```

**In all workflow files**, verify AWS region matches your config:
```yaml
aws-region: us-east-1  # Change if using different region
```

### 4. Push to GitHub

```bash
# Add all files
git add .

# Commit
git commit -m "Add CI/CD pipeline and testing infrastructure"

# Push to GitHub
git push origin main
```

This will automatically trigger the **Test** workflow!

---

## ✅ Verification

### 1. Check GitHub Actions

Go to: https://github.com/yourusername/ipam-serverless/actions

You should see workflows running:
- ✅ Tests
- ✅ Deploy to Dev (if you pushed to dev branch)

### 2. Test the API

```bash
# Get API URL
API_URL=$(pulumi stack output api_gateway_url)

# Health check
curl $API_URL/health

# Create a subnet
curl -X POST $API_URL/subnets \
  -H "Content-Type: application/json" \
  -d '{
    "network": "192.168.1.0/24",
    "name": "test-subnet",
    "description": "My first subnet"
  }'

# List subnets
curl $API_URL/subnets
```

### 3. Verify AWS Resources

```bash
# List Lambda functions
aws lambda list-functions --query 'Functions[?contains(FunctionName, `ipam`)].FunctionName'

# List DynamoDB tables
aws dynamodb list-tables --query 'TableNames[?contains(@, `ipam`)]'

# Get API Gateway endpoints
aws apigateway get-rest-apis --query 'items[?contains(name, `ipam`)]'
```

---

## 🧪 Running Tests Locally

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=lambda_functions --cov=infrastructure --cov-report=html

# Run specific test types
pytest tests/unit          # Unit tests only
pytest tests/integration   # Integration tests only

# Run code quality checks
black --check .           # Check formatting
pylint lambda_functions   # Run linter
bandit -r lambda_functions # Security scan
```

---

## 🌿 Development Workflow

### Create Feature Branch

```bash
# Create and switch to feature branch
git checkout -b feature/add-ip-validation

# Make changes to code

# Run tests locally
pytest

# Commit changes
git add .
git commit -m "Add IP address validation"

# Push to GitHub
git push origin feature/add-ip-validation
```

This will trigger:
1. ✅ Test workflow
2. ✅ Deploy to Dev (if configured)

### Create Pull Request

1. Go to GitHub repository
2. Click "Compare & pull request"
3. Review changes
4. Create PR

This will:
1. Run all tests
2. Deploy to dev environment
3. Add comment with dev URL
4. Wait for code review

### Merge to Production

1. Get PR approved
2. Merge to main branch

This will:
1. Deploy to production (after manual approval)
2. Run smoke tests
3. Create release tag
4. Send notifications

---

## 📊 Monitoring

### CloudWatch Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/ipam-subnet-manager --follow

# View API Gateway logs
aws logs tail /aws/apigateway/ipam-api --follow
```

### Pulumi Stack Outputs

```bash
# View all outputs
pulumi stack output

# View specific output
pulumi stack output api_gateway_url
pulumi stack output lambda_function_arns
```

### DynamoDB Table Stats

```bash
# Describe table
aws dynamodb describe-table --table-name ipam-subnets

# Get item count
aws dynamodb scan --table-name ipam-subnets --select "COUNT"
```

---

## 🔄 Updating the System

### Update Lambda Code

```bash
# Make changes to lambda_functions/

# Test locally
pytest

# Deploy changes
pulumi up

# Verify deployment
pulumi stack output api_gateway_url
curl $(pulumi stack output api_gateway_url)/health
```

### Update Infrastructure

```bash
# Modify infrastructure/*.py files

# Preview changes
pulumi preview

# Apply changes
pulumi up
```

---

## 🗑️ Cleanup

### Destroy Dev Environment

```bash
pulumi stack select dev
pulumi destroy
```

### Destroy Prod Environment

```bash
pulumi stack select prod
pulumi destroy
```

### Remove Pulumi Stack

```bash
pulumi stack rm dev
pulumi stack rm prod
```

---

## 🐛 Troubleshooting

### Issue: Pulumi commands fail

**Solution:**
```bash
# Re-login to Pulumi
pulumi login --local

# Or reset state
rm -rf ~/.pulumi
pulumi login --local
```

### Issue: AWS credentials error

**Solution:**
```bash
# Reconfigure AWS
aws configure

# Verify identity
aws sts get-caller-identity
```

### Issue: Lambda deployment timeout

**Solution:**
```bash
# Increase Lambda timeout in infrastructure/compute.py
timeout=300  # 5 minutes
```

### Issue: DynamoDB capacity exceeded

**Solution:**
```bash
# Switch to on-demand mode in infrastructure/storage.py
billing_mode="PAY_PER_REQUEST"
```

### Issue: Tests fail locally

**Solution:**
```bash
# Reinstall dependencies
pip install -e ".[dev]" --force-reinstall

# Clear pytest cache
pytest --cache-clear

# Run with verbose output
pytest -vv
```

---

## 📚 Next Steps

1. ✅ **Customize the API**: Add more endpoints for your use case
2. ✅ **Add Authentication**: Integrate AWS Cognito or API keys
3. ✅ **Enable Monitoring**: Set up CloudWatch dashboards
4. ✅ **Add More Tests**: Increase test coverage to 90%+
5. ✅ **Optimize Costs**: Review and adjust Lambda memory/timeout
6. ✅ **Add Documentation**: Create API reference docs

---

## 🤝 Getting Help

- Check the [README](../README.md) for feature documentation
- Review [Architecture Guide](docs/architecture.md) for system design
- Open an issue on GitHub for bugs or questions
- Contact the maintainer (see README for contact info)

---

**Happy coding! 🚀**
