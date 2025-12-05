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

    # Strip stage name from path (handles /prod/subnets -> /subnets)
    if path.startswith('/prod'):
        path = path[5:]
    elif path.startswith('/dev'):
        path = path[4:]
    elif path.startswith('/test'):
        path = path[5:]

    print(f"Processed path: {path}")  # Debug log

    try:
        if http_method == 'POST' and path == '/subnets':
            return create_subnet(event)
        elif http_method == 'GET' and path == '/subnets':
            return list_subnets(event)
        elif http_method == 'GET' and path == '/subnets/calculate':
            return calculate_subnet(event)
        elif http_method == 'GET' and '/subnets/' in path:
            return get_subnet(event)
        elif http_method == 'DELETE' and '/subnets/' in path:
            return delete_subnet(event)
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
