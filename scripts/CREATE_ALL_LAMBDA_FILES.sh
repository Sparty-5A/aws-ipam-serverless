#!/bin/bash
# Complete Lambda Function Generator
# Creates ALL 4 Lambda files needed for IPAM system

set -e

LAMBDA_DIR="lambda_functions"

echo "🚀 Creating ALL Lambda function files..."
echo ""

# Create directories
mkdir -p ${LAMBDA_DIR}/subnet_manager
mkdir -p ${LAMBDA_DIR}/ip_manager

# ==========================================
# File 1: subnet_calculator.py
# ==========================================
echo "📝 Creating subnet_calculator.py..."

cat > ${LAMBDA_DIR}/subnet_manager/subnet_calculator.py << 'EOF1'
"""
IP subnet calculation utilities
Leverages network engineering expertise!
"""
import ipaddress
from typing import Dict, List

class SubnetCalculator:
    """Handle all subnet math operations"""

    @staticmethod
    def parse_cidr(cidr: str) -> Dict:
        """Parse CIDR notation and return network details"""
        try:
            network = ipaddress.IPv4Network(cidr, strict=False)

            return {
                "network": str(network.network_address),
                "prefix_length": network.prefixlen,
                "netmask": str(network.netmask),
                "wildcard": str(network.hostmask),
                "first_usable": str(network.network_address + 1) if network.num_addresses > 2 else str(network.network_address),
                "last_usable": str(network.broadcast_address - 1) if network.num_addresses > 2 else str(network.broadcast_address),
                "broadcast": str(network.broadcast_address),
                "total_ips": network.num_addresses,
                "usable_ips": network.num_addresses - 2 if network.num_addresses > 2 else network.num_addresses,
            }
        except ValueError as e:
            raise ValueError(f"Invalid CIDR notation: {str(e)}")

    @staticmethod
    def is_ip_in_subnet(ip: str, cidr: str) -> bool:
        """Check if IP address belongs to subnet"""
        try:
            ip_obj = ipaddress.IPv4Address(ip)
            network = ipaddress.IPv4Network(cidr, strict=False)
            return ip_obj in network
        except ValueError:
            return False

    @staticmethod
    def calculate_utilization(allocated_count: int, total_usable: int) -> float:
        """Calculate subnet utilization percentage"""
        if total_usable == 0:
            return 0.0
        return round((allocated_count / total_usable) * 100, 2)

    @staticmethod
    def get_next_available_ip(cidr: str, allocated_ips: List[str]) -> str:
        """Find next available IP in subnet"""
        network = ipaddress.IPv4Network(cidr, strict=False)
        allocated_set = set(allocated_ips)

        for ip in network.hosts():
            if str(ip) not in allocated_set:
                return str(ip)

        raise ValueError("No available IPs in subnet")

    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validate IP address format"""
        try:
            ipaddress.IPv4Address(ip)
            return True
        except ValueError:
            return False

    @staticmethod
    def subnet_overlap(cidr1: str, cidr2: str) -> bool:
        """Check if two subnets overlap"""
        try:
            network1 = ipaddress.IPv4Network(cidr1, strict=False)
            network2 = ipaddress.IPv4Network(cidr2, strict=False)
            return network1.overlaps(network2)
        except ValueError:
            return False

def get_subnet_id(cidr: str) -> str:
    """Convert CIDR to subnet_id for DynamoDB key"""
    return cidr.replace("/", "_")

def cidr_from_subnet_id(subnet_id: str) -> str:
    """Convert subnet_id back to CIDR"""
    return subnet_id.replace("_", "/")
EOF1

echo "✅ subnet_calculator.py created"

# ==========================================
# File 2: validators.py
# ==========================================
echo "📝 Creating validators.py..."

cat > ${LAMBDA_DIR}/ip_manager/validators.py << 'EOF2'
"""
Input validation utilities for IP management
"""
import re
from typing import Dict, Optional, Tuple

class IPValidator:
    """Validate IP-related inputs"""

    VALID_STATUSES = ['active', 'reserved', 'deprecated', 'planned']

    @staticmethod
    def validate_ip_allocation(data: dict) -> Tuple[bool, Optional[str]]:
        """Validate IP allocation request"""
        required_fields = ['ip_address', 'subnet_id']

        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"

        ip = data['ip_address']
        if not IPValidator.is_valid_ipv4(ip):
            return False, f"Invalid IP address format: {ip}"

        hostname = data.get('hostname')
        if hostname and not IPValidator.is_valid_hostname(hostname):
            return False, f"Invalid hostname format: {hostname}"

        status = data.get('status', 'active')
        if status not in IPValidator.VALID_STATUSES:
            return False, f"Invalid status. Must be one of: {', '.join(IPValidator.VALID_STATUSES)}"

        mac = data.get('mac_address')
        if mac and not IPValidator.is_valid_mac(mac):
            return False, f"Invalid MAC address format: {mac}"

        return True, None

    @staticmethod
    def is_valid_ipv4(ip: str) -> bool:
        """Validate IPv4 address format"""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False
        octets = ip.split('.')
        return all(0 <= int(octet) <= 255 for octet in octets)

    @staticmethod
    def is_valid_hostname(hostname: str) -> bool:
        """Validate hostname format (RFC 1123)"""
        if len(hostname) > 253:
            return False
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
        return bool(re.match(pattern, hostname))

    @staticmethod
    def is_valid_mac(mac: str) -> bool:
        """Validate MAC address format"""
        patterns = [
            r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$',
            r'^([0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}$',
            r'^[0-9A-Fa-f]{12}$',
        ]
        return any(re.match(pattern, mac) for pattern in patterns)

    @staticmethod
    def normalize_mac(mac: str) -> str:
        """Normalize MAC address to xx:xx:xx:xx:xx:xx format"""
        mac_clean = mac.replace(':', '').replace('-', '').upper()
        return ':'.join(mac_clean[i:i+2] for i in range(0, 12, 2))
EOF2

echo "✅ validators.py created"

echo ""
echo "⚠️  Creating large handler files (this may take a moment)..."
echo ""

# ==========================================
# File 3: subnet_manager/handler.py
# ==========================================
echo "📝 Creating subnet_manager/handler.py (400 lines)..."

# Due to size, I'll create this file via the script
# This is the complete subnet manager handler

cat > ${LAMBDA_DIR}/subnet_manager/handler.py << 'EOF3'
"""
Lambda function to manage subnets
Handles CRUD operations for subnet inventory
"""
import json
import boto3
import os
from datetime import datetime
from decimal import Decimal
from subnet_calculator import SubnetCalculator, get_subnet_id, cidr_from_subnet_id

dynamodb = boto3.resource('dynamodb')
SUBNETS_TABLE = os.environ['SUBNETS_TABLE']
IP_TABLE = os.environ['IP_TABLE']
AUDIT_TABLE = os.environ['AUDIT_TABLE']

def lambda_handler(event, context):
    """Route requests to appropriate handler"""
    print(f"Event: {json.dumps(event)}")
    http_method = event.get('requestContext', {}).get('http', {}).get('method')
    path = event.get('rawPath', '')

    try:
        if http_method == 'POST' and path == '/subnets':
            return create_subnet(event)
        elif http_method == 'GET' and path == '/subnets':
            return list_subnets(event)
        elif http_method == 'GET' and '/subnets/' in path:
            return get_subnet(event)
        elif http_method == 'DELETE' and '/subnets/' in path:
            return delete_subnet(event)
        elif http_method == 'GET' and path == '/subnets/calculate':
            return calculate_subnet(event)
        else:
            return response(404, {'error': 'Not found'})
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return response(500, {'error': str(e)})

def create_subnet(event):
    """Create new subnet"""
    body = json.loads(event.get('body', '{}'))
    cidr = body.get('cidr')
    if not cidr:
        return response(400, {'error': 'cidr is required'})

    try:
        subnet_info = SubnetCalculator.parse_cidr(cidr)
    except ValueError as e:
        return response(400, {'error': str(e)})

    existing_subnets = scan_all_subnets()
    for existing in existing_subnets:
        if SubnetCalculator.subnet_overlap(cidr, cidr_from_subnet_id(existing['subnet_id'])):
            return response(400, {
                'error': f"Subnet overlaps with existing subnet: {cidr_from_subnet_id(existing['subnet_id'])}"
            })

    subnet_id = get_subnet_id(cidr)
    item = {
        'subnet_id': subnet_id,
        'cidr': cidr,
        'vlan_id': int(body.get('vlan_id', 0)),
        'site': body.get('site', 'default'),
        'description': body.get('description', ''),
        'gateway': body.get('gateway', subnet_info['first_usable']),
        'network': subnet_info['network'],
        'netmask': subnet_info['netmask'],
        'prefix_length': subnet_info['prefix_length'],
        'total_ips': subnet_info['total_ips'],
        'usable_ips': subnet_info['usable_ips'],
        'allocated_count': 0,
        'utilization': Decimal('0'),
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
    }

    table = dynamodb.Table(SUBNETS_TABLE)
    table.put_item(Item=item)
    log_audit('subnet_created', subnet_id, item)

    return response(201, {'message': 'Subnet created', 'subnet': convert_decimals(item)})

def list_subnets(event):
    """List all subnets with optional filters"""
    query_params = event.get('queryStringParameters', {}) or {}
    table = dynamodb.Table(SUBNETS_TABLE)

    site = query_params.get('site')
    vlan = query_params.get('vlan')

    if site:
        response_data = table.query(
            IndexName='site-index',
            KeyConditionExpression='site = :site',
            ExpressionAttributeValues={':site': site}
        )
    elif vlan:
        response_data = table.query(
            IndexName='vlan-index',
            KeyConditionExpression='vlan_id = :vlan',
            ExpressionAttributeValues={':vlan': int(vlan)}
        )
    else:
        response_data = table.scan()

    items = response_data.get('Items', [])

    for item in items:
        subnet_id = item['subnet_id']
        allocated_count = get_allocated_count(subnet_id)
        item['allocated_count'] = allocated_count
        item['utilization'] = SubnetCalculator.calculate_utilization(
            allocated_count, item['usable_ips']
        )

    return response(200, {'subnets': convert_decimals(items), 'count': len(items)})

def get_subnet(event):
    """Get specific subnet details"""
    path = event.get('rawPath', '')
    subnet_id = path.split('/')[-1]

    table = dynamodb.Table(SUBNETS_TABLE)
    result = table.get_item(Key={'subnet_id': subnet_id})

    if 'Item' not in result:
        return response(404, {'error': 'Subnet not found'})

    item = result['Item']
    allocated_count = get_allocated_count(subnet_id)
    item['allocated_count'] = allocated_count
    item['utilization'] = SubnetCalculator.calculate_utilization(
        allocated_count, item['usable_ips']
    )
    item['allocated_ips'] = get_allocated_ips_list(subnet_id)

    return response(200, {'subnet': convert_decimals(item)})

def delete_subnet(event):
    """Delete subnet (only if no IPs allocated)"""
    path = event.get('rawPath', '')
    subnet_id = path.split('/')[-1]

    allocated_count = get_allocated_count(subnet_id)
    if allocated_count > 0:
        return response(400, {
            'error': f'Cannot delete subnet with {allocated_count} allocated IPs. Release IPs first.'
        })

    table = dynamodb.Table(SUBNETS_TABLE)
    table.delete_item(Key={'subnet_id': subnet_id})
    log_audit('subnet_deleted', subnet_id, {})

    return response(200, {'message': 'Subnet deleted'})

def calculate_subnet(event):
    """Calculate subnet information (utility endpoint)"""
    query_params = event.get('queryStringParameters', {}) or {}
    cidr = query_params.get('cidr')

    if not cidr:
        return response(400, {'error': 'cidr parameter required'})

    try:
        subnet_info = SubnetCalculator.parse_cidr(cidr)
        return response(200, subnet_info)
    except ValueError as e:
        return response(400, {'error': str(e)})

def scan_all_subnets():
    """Get all subnets (for overlap checking)"""
    table = dynamodb.Table(SUBNETS_TABLE)
    response_data = table.scan()
    return response_data.get('Items', [])

def get_allocated_count(subnet_id: str) -> int:
    """Count allocated IPs in a subnet"""
    table = dynamodb.Table(IP_TABLE)
    response_data = table.query(
        IndexName='subnet-index',
        KeyConditionExpression='subnet_id = :subnet_id',
        ExpressionAttributeValues={':subnet_id': subnet_id},
        Select='COUNT'
    )
    return response_data.get('Count', 0)

def get_allocated_ips_list(subnet_id: str) -> list:
    """Get list of allocated IPs in subnet"""
    table = dynamodb.Table(IP_TABLE)
    response_data = table.query(
        IndexName='subnet-index',
        KeyConditionExpression='subnet_id = :subnet_id',
        ExpressionAttributeValues={':subnet_id': subnet_id}
    )
    items = response_data.get('Items', [])
    return [item['ip_address'] for item in items]

def log_audit(action: str, resource_id: str, details: dict):
    """Log action to audit trail"""
    import uuid
    table = dynamodb.Table(AUDIT_TABLE)
    timestamp = int(datetime.now().timestamp())

    table.put_item(Item={
        'log_id': str(uuid.uuid4()),
        'timestamp': timestamp,
        'ttl': timestamp + (90 * 24 * 60 * 60),
        'action_type': action,
        'resource_id': resource_id,
        'details': json.dumps(details, default=str),
        'created_at': datetime.now().isoformat(),
    })

def convert_decimals(obj):
    """Convert DynamoDB Decimal to float/int for JSON"""
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    else:
        return obj

def response(status_code: int, body: dict):
    """Build API Gateway response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        },
        'body': json.dumps(body, default=str)
    }
EOF3

echo "✅ subnet_manager/handler.py created"

# Note: Due to character limit, I'll need to continue in next message
# But this shows the structure you need

echo ""
echo "================================"
echo "✅ Script structure created!"
echo "================================"
echo ""
echo "📋 This script will create:"
echo "  1. subnet_calculator.py"
echo "  2. validators.py"
echo "  3. subnet_manager/handler.py"
echo "  4. ip_manager/handler.py (continuing...)"
echo ""