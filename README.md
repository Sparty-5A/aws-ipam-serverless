# 🌐 IPAM Serverless - IP Address Management System

[![Tests](https://github.com/Sparty-5A/aws-ipam-serverless/workflows/Tests/badge.svg)](https://github.com/Sparty-5A/aws-ipam-serverless/actions)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20DynamoDB%20%7C%20API%20Gateway-orange)](https://aws.amazon.com/)
[![Infrastructure as Code](https://img.shields.io/badge/IaC-Pulumi-blueviolet)](https://www.pulumi.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Production-ready serverless IP Address Management (IPAM) system built with AWS Lambda, DynamoDB, and API Gateway. Features automated testing, comprehensive documentation, and infrastructure as code using Pulumi.

---

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Development](#development)
- [Testing](#testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Deployment](#deployment)
- [Cost Analysis](#cost-analysis)
- [Project Structure](#project-structure)

---

## ✨ Features

### Core Functionality
- **Subnet Management**: Create, read, update, delete (CRUD) operations for IP subnets
- **IP Allocation**: Automatic IP address allocation and tracking within subnets
- **Subnet Calculator**: Calculate subnet divisions and available IP ranges
- **Conflict Detection**: Prevent overlapping subnet allocations
- **CIDR Validation**: Validate CIDR notation and subnet masks

### DevOps & Infrastructure
- **Infrastructure as Code**: Full Pulumi deployment for AWS resources
- **Automated Testing**: GitHub Actions runs tests on every push
- **Multi-Environment**: Separate dev and production environments
- **Test Framework**: Unit and integration test suite with pytest
- **Security Scanning**: Automated security scans with Bandit
- **Code Quality**: Linting with Pylint, formatting with Black

### AWS Services
- **AWS Lambda**: Serverless compute for all business logic
- **DynamoDB**: NoSQL database for subnet and IP allocation data
- **API Gateway**: RESTful API with authentication support
- **CloudWatch**: Logging and monitoring

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        API Gateway                          │
│            https://api.example.com/v1/                      │
└────────────────────┬────────────────────────────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
    ▼                ▼                ▼
┌─────────┐    ┌──────────┐    ┌────────────┐
│ Subnet  │    │    IP    │    │  Calculate │
│ Manager │    │ Manager  │    │  Subnets   │
│ Lambda  │    │  Lambda  │    │   Lambda   │
└────┬────┘    └─────┬────┘    └──────┬─────┘
     │               │                 │
     └───────────────┼─────────────────┘
                     │
                     ▼
            ┌─────────────────┐
            │    DynamoDB     │
            │  Subnets Table  │
            │    IPs Table    │
            └─────────────────┘
```

### Key Design Decisions

**Serverless Architecture**
- No servers to manage or patch
- Auto-scaling based on demand
- Pay-per-use pricing model

**DynamoDB for Storage**
- Single-digit millisecond latency
- Automatic scaling
- Built-in redundancy

**API Gateway Integration**
- RESTful API design
- Request validation
- Rate limiting and throttling

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- AWS CLI configured with credentials
- Pulumi CLI installed
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/Sparty-5A/aws-ipam-serverless.git
cd aws-ipam-serverless

# Install dependencies
pip install -e ".[dev]"

# Initialize Pulumi
pulumi login --local
pulumi stack init dev

# Deploy to AWS
pulumi up
```

### First API Call

```bash
# Get API Gateway URL
API_URL=$(pulumi stack output api_gateway_url)

# Create a subnet
curl -X POST $API_URL/subnets \
  -H "Content-Type: application/json" \
  -d '{
    "network": "192.168.1.0/24",
    "name": "production-subnet",
    "description": "Main production network"
  }'

# List all subnets
curl $API_URL/subnets
```

---

## 📡 API Endpoints

### Subnet Management

**Create Subnet**
```http
POST /subnets
Content-Type: application/json

{
  "network": "192.168.1.0/24",
  "name": "my-subnet",
  "description": "Optional description"
}
```

**List Subnets**
```http
GET /subnets
```

**Get Subnet**
```http
GET /subnets/{subnet_id}
```

**Update Subnet**
```http
PUT /subnets/{subnet_id}
Content-Type: application/json

{
  "name": "updated-name",
  "description": "Updated description"
}
```

**Delete Subnet**
```http
DELETE /subnets/{subnet_id}
```

### IP Address Management

**Allocate IP**
```http
POST /ips/allocate
Content-Type: application/json

{
  "subnet_id": "subnet-123",
  "hostname": "server01"
}
```

**List IPs in Subnet**
```http
GET /ips?subnet_id=subnet-123
```

**Release IP**
```http
DELETE /ips/{ip_address}
```

### Subnet Calculator

**Calculate Subnets**
```http
POST /calculate
Content-Type: application/json

{
  "parent_network": "192.168.0.0/16",
  "subnet_count": 256
}
```

**Health Check**
```http
GET /health
```

---

## 💻 Development

### Local Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
black .
pylint lambda_functions infrastructure

# Run security scan
bandit -r lambda_functions infrastructure
```

### Project Structure

```
aws-ipam-serverless/
├── infrastructure/          # Pulumi IaC code
│   ├── api.py              # API Gateway configuration
│   ├── compute.py          # Lambda function definitions
│   └── storage.py          # DynamoDB table definitions
├── lambda_functions/        # Lambda function code
│   ├── subnet_manager/     # Subnet CRUD operations
│   ├── ip_manager/         # IP allocation logic
│   └── shared/             # Shared utilities
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
├── .github/workflows/       # CI/CD pipelines
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

---

## 🧪 Testing

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit

# Integration tests only
pytest tests/integration

# With coverage report
pytest --cov=lambda_functions --cov=infrastructure --cov-report=html

# Specific test file
pytest tests/unit/test_subnet_calculator.py

# Specific test function
pytest tests/unit/test_subnet_calculator.py::test_calculate_subnets
```

### Test Framework

The project includes a comprehensive test suite:
- Unit tests for calculator functions and validators
- Integration tests for API endpoints
- Mock AWS services with `moto` for local testing
- Parameterized tests for edge cases

---

## 🔄 CI/CD Pipeline

### Current Implementation

**Automated Testing** via GitHub Actions:
- ✅ Tests run automatically on every push
- ✅ Multiple Python versions tested (3.9, 3.10, 3.11, 3.12)
- ✅ Code quality checks (Black, Pylint)
- ✅ Security scanning (Bandit)
- ✅ Test results uploaded as artifacts

**Manual Deployment**:
- Deployment to AWS is performed manually using Pulumi CLI
- This allows for controlled, reviewed deployments
- See [Deployment](#deployment) section below

### GitHub Actions Workflows

**Test Workflow** (`.github/workflows/test.yml`)
- Runs on every push and pull request
- Tests against Python 3.9, 3.10, 3.11, 3.12
- Runs code quality and security checks
- Uploads test results as artifacts

---

## 🚢 Deployment

### Deploy to Development

```bash
pulumi stack select dev
pulumi up
```

### Deploy to Production

```bash
pulumi stack select prod
pulumi config set aws:region us-east-1
pulumi up
```

### Multi-Region Deployment

```bash
# Deploy to multiple regions
for region in us-east-1 us-west-2 eu-west-1; do
  pulumi stack select prod-$region
  pulumi config set aws:region $region
  pulumi up --yes
done
```

### Environment Variables

Configure per-stack settings in `Pulumi.{stack}.yaml`:

```yaml
config:
  aws:region: us-east-1
  aws-ipam-serverless:environment: production
  aws-ipam-serverless:enableDetailedMetrics: "true"
```

---

## 💰 Cost Analysis

### Monthly Cost Breakdown

**Development Environment:**
- Lambda: $0.00 (within Free Tier: 1M requests/month)
- DynamoDB: $0.00 (within Free Tier: 25 GB storage)
- API Gateway: $0.00 (within Free Tier: 1M requests/month)
- CloudWatch Logs: ~$0.50
- **Total: ~$0.50/month**

**Production Environment (estimated 10K requests/day):**
- Lambda: $0.20 (300K requests × $0.20/1M)
- DynamoDB: $1.25 (on-demand pricing, minimal usage)
- API Gateway: $3.50 (300K requests × $3.50/1M)
- CloudWatch: $2.00 (logs + metrics)
- **Total: ~$7/month**

### Cost Optimization Tips

1. Use DynamoDB on-demand pricing for variable workloads
2. Enable Lambda reserved concurrency for predictable loads
3. Set CloudWatch log retention policies (7-30 days)
4. Use API Gateway caching for frequently accessed data

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built with [Pulumi](https://www.pulumi.com/) for Infrastructure as Code
- Uses [AWS Lambda](https://aws.amazon.com/lambda/) for serverless compute
- Testing with [pytest](https://pytest.org/) and [moto](https://github.com/getmoto/moto)
- CI/CD powered by [GitHub Actions](https://github.com/features/actions)

---

## 📞 Contact

**Author**: Scott Penry  
**Email**: scottpenry@comcast.net  
**GitHub**: [@Sparty-5A](https://github.com/Sparty-5A)

---

## ⭐ Show Your Support

Give a ⭐️ if this project helped you!

---

**Made with ❤️ using Python, AWS, and Pulumi**