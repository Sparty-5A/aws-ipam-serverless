"""
IPAM System - IP Address Management on AWS
Complete serverless infrastructure using DynamoDB, Lambda, API Gateway

Author: Network Engineer turned Cloud Engineer
Purpose: Showcase AWS serverless + network expertise

Architecture:
- DynamoDB: 4 tables (subnets, IPs, VLANs, audit log)
- Lambda: 2 functions (subnet manager, IP manager)
- API Gateway: RESTful API with 12+ endpoints
- Cost: $0-2/month (free tier eligible)

Deploy:
    pulumi up

Test:
    curl $(pulumi stack output api_endpoint)/subnets

Destroy:
    pulumi destroy
"""

import pulumi

# Import infrastructure modules
from infrastructure.storage import create_ipam_storage
from infrastructure.compute import create_lambda_functions
from infrastructure.api import create_ipam_api

# Configuration
config = pulumi.Config()
project_name = pulumi.get_project()
stack = pulumi.get_stack()

# Common tags for all resources
tags = {
    "Project": project_name,
    "Stack": stack,
    "ManagedBy": "Pulumi",
    "Purpose": "IPAM System",
    "Owner": config.get("owner") or "DevOps",
}

print(f"🚀 Deploying {project_name} to stack: {stack}")
print(f"📍 Region: {config.get('aws:region') or 'us-east-1'}")

# ==========================================
# Step 1: Create DynamoDB Tables
# ==========================================
print("\n📊 Creating DynamoDB tables...")
print("   • subnets - Subnet inventory")
print("   • ip_allocations - IP address tracking")
print("   • vlans - VLAN database")
print("   • audit_log - Change history")

tables = create_ipam_storage(project_name, tags)

# ==========================================
# Step 2: Create Lambda Functions
# ==========================================
print("\n⚡ Creating Lambda functions...")
print("   • subnet-manager - CRUD operations for subnets")
print("   • ip-manager - IP allocation and tracking")

functions = create_lambda_functions(project_name, tables, tags)

# ==========================================
# Step 3: Create API Gateway
# ==========================================
print("\n🌐 Creating API Gateway...")
print("   • 12+ REST API endpoints")
print("   • CORS enabled")
print("   • Production stage")

api = create_ipam_api(project_name, functions, tags)

# ==========================================
# Exports & Summary
# ==========================================
print("\n✅ Deployment complete!")
print("\n" + "="*60)
print("IPAM SYSTEM DEPLOYMENT SUMMARY")
print("="*60)

# API Endpoint
pulumi.export("api_endpoint", api['api_endpoint'])

# Table names
pulumi.export("tables", {
    "subnets": tables['subnets_table'].name,
    "ips": tables['ip_allocations_table'].name,
    "vlans": tables['vlans_table'].name,
    "audit": tables['audit_table'].name,
})

# Lambda functions
pulumi.export("functions", {
    "subnet_manager": functions['subnet_function'].name,
    "ip_manager": functions['ip_function'].name,
})

# Quick start guide
pulumi.export("quick_start", {
    "1_test_api": "curl $(pulumi stack output api_endpoint)/subnets",
    "2_create_subnet": "See scripts/test_api.sh for examples",
    "3_allocate_ip": "See scripts/populate_sample_data.sh",
    "4_view_logs": "aws logs tail /aws/lambda/$(pulumi stack output functions.subnet_manager) --follow",
})

# API endpoints reference
pulumi.export("api_endpoints", {
    "subnets": {
        "create": "POST /subnets",
        "list": "GET /subnets",
        "get": "GET /subnets/{id}",
        "delete": "DELETE /subnets/{id}",
        "calculate": "GET /subnets/calculate?cidr=10.0.1.0/24",
    },
    "ips": {
        "allocate": "POST /ips",
        "auto_allocate": "POST /ips/auto",
        "list": "GET /ips",
        "get": "GET /ips/{ip}",
        "update": "PUT /ips/{ip}",
        "release": "DELETE /ips/{ip}",
    },
    "search": {
        "global": "GET /search?q=web-server",
    }
})

# Cost estimate
pulumi.export("cost_estimate", {
    "lambda_requests": "1M free per month",
    "api_gateway": "1M requests free per month",
    "dynamodb": "25GB storage + 25 RCU/WCU free",
    "estimated_monthly_cost": "$0-2 (within free tier)",
})

# Next steps
pulumi.export("next_steps", [
    "✅ Deployment complete!",
    "",
    "🧪 Test the API:",
    "   export API_ENDPOINT=$(pulumi stack output api_endpoint)",
    "   curl $API_ENDPOINT/subnets",
    "",
    "📝 Create your first subnet:",
    "   ./scripts/test_api.sh create_subnet",
    "",
    "📊 View in AWS Console:",
    "   DynamoDB → Tables",
    "   Lambda → Functions",
    "   API Gateway → APIs",
    "",
    "📖 Full documentation: README.md",
])

print("\n" + "="*60)
print(f"API Endpoint: {api['api_endpoint']}")
print("="*60)
print("\nRun 'pulumi stack output' to see all outputs")
print("Run './scripts/test_api.sh' to test the API\n")
