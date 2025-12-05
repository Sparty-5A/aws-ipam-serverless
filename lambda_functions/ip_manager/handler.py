"""
Lambda function to manage IP allocations
Handles IP assignment, release, and tracking
"""
import json
import boto3
import os
from datetime import datetime
from decimal import Decimal
from validators import IPValidator

dynamodb = boto3.resource('dynamodb')
SUBNETS_TABLE = os.environ['SUBNETS_TABLE']
IP_TABLE = os.environ['IP_TABLE']
AUDIT_TABLE = os.environ['AUDIT_TABLE']


def lambda_handler(event, context):
    """Route IP management requests"""

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
        if http_method == 'POST' and path == '/ips':
            return allocate_ip(event)
        elif http_method == 'POST' and path == '/ips/auto':
            return auto_allocate_ip(event)
        elif http_method == 'GET' and path == '/ips':
            return list_ips(event)
        elif http_method == 'GET' and '/ips/' in path:
            return get_ip(event)
        elif http_method == 'PUT' and '/ips/' in path:
            return update_ip(event)
        elif http_method == 'DELETE' and '/ips/' in path:
            return release_ip(event)
        elif http_method == 'GET' and path == '/search':
            return search(event)
        else:
            return response(404, {'error': 'Not found'})

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return response(500, {'error': str(e)})


def allocate_ip(event):
    """
    Manually allocate specific IP address

    Body:
    {
        "ip_address": "10.0.1.10",
        "subnet_id": "10.0.1.0_24",
        "hostname": "web-server-01",
        "description": "Production web server",
        "status": "active",
        "mac_address": "00:11:22:33:44:55",
        "owner": "IT Department"
    }
    """
    body = json.loads(event.get('body', '{}'))

    # Validate input
    is_valid, error = IPValidator.validate_ip_allocation(body)
    if not is_valid:
        return response(400, {'error': error})

    ip_address = body['ip_address']
    subnet_id = body['subnet_id']

    # Check if subnet exists
    subnet = get_subnet_info(subnet_id)
    if not subnet:
        return response(404, {'error': f'Subnet not found: {subnet_id}'})

    # Check if IP is in subnet range
    from subnet_calculator import SubnetCalculator, cidr_from_subnet_id
    cidr = cidr_from_subnet_id(subnet_id)

    if not SubnetCalculator.is_ip_in_subnet(ip_address, cidr):
        return response(400, {'error': f'IP {ip_address} is not in subnet {cidr}'})

    # Check if IP already allocated
    if is_ip_allocated(ip_address):
        return response(409, {'error': f'IP {ip_address} is already allocated'})

    # Normalize MAC address if provided
    mac_address = body.get('mac_address')
    if mac_address:
        mac_address = IPValidator.normalize_mac(mac_address)

    # Create allocation
    item = {
        'ip_address': ip_address,
        'subnet_id': subnet_id,
        'hostname': body.get('hostname', ''),
        'description': body.get('description', ''),
        'status': body.get('status', 'active'),
        'mac_address': mac_address or '',
        'owner': body.get('owner', ''),
        'device_type': body.get('device_type', ''),
        'location': body.get('location', ''),
        'allocated_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
    }

    # Store in DynamoDB
    table = dynamodb.Table(IP_TABLE)
    table.put_item(Item=item)

    # Update subnet utilization
    update_subnet_utilization(subnet_id)

    # Log to audit
    log_audit('ip_allocated', ip_address, item)

    return response(201, {
        'message': 'IP allocated successfully',
        'ip': convert_decimals(item)
    })


def auto_allocate_ip(event):
    """
    Automatically allocate next available IP in subnet

    Body:
    {
        "subnet_id": "10.0.1.0_24",
        "hostname": "web-server-02",
        "description": "Auto-assigned IP",
        "status": "active"
    }
    """
    body = json.loads(event.get('body', '{}'))

    subnet_id = body.get('subnet_id')
    if not subnet_id:
        return response(400, {'error': 'subnet_id is required'})

    # Get subnet info
    subnet = get_subnet_info(subnet_id)
    if not subnet:
        return response(404, {'error': f'Subnet not found: {subnet_id}'})

    # Get all allocated IPs in subnet
    allocated_ips = get_allocated_ips_in_subnet(subnet_id)

    # Find next available IP
    from subnet_calculator import SubnetCalculator, cidr_from_subnet_id
    cidr = cidr_from_subnet_id(subnet_id)

    try:
        next_ip = SubnetCalculator.get_next_available_ip(cidr, allocated_ips)
    except ValueError as e:
        return response(400, {'error': str(e)})

    # Create allocation with found IP
    body['ip_address'] = next_ip
    body['subnet_id'] = subnet_id

    # Use regular allocate function
    event['body'] = json.dumps(body)
    return allocate_ip(event)


def list_ips(event):
    """
    List IP allocations with filters

    Query params:
    - subnet_id: Filter by subnet
    - status: Filter by status
    - search: Search in hostname/description
    """
    query_params = event.get('queryStringParameters', {}) or {}

    table = dynamodb.Table(IP_TABLE)

    subnet_id = query_params.get('subnet_id')
    status = query_params.get('status')
    search_term = query_params.get('search', '').lower()

    # Query by index or scan
    if subnet_id:
        response_data = table.query(
            IndexName='subnet-index',
            KeyConditionExpression='subnet_id = :subnet_id',
            ExpressionAttributeValues={':subnet_id': subnet_id}
        )
    elif status:
        response_data = table.query(
            IndexName='status-index',
            KeyConditionExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': status}
        )
    else:
        response_data = table.scan()

    items = response_data.get('Items', [])

    # Apply search filter if provided
    if search_term:
        items = [
            item for item in items
            if search_term in item.get('hostname', '').lower()
               or search_term in item.get('description', '').lower()
               or search_term in item.get('ip_address', '').lower()
        ]

    return response(200, {
        'ips': convert_decimals(items),
        'count': len(items)
    })


def get_ip(event):
    """Get specific IP allocation details"""
    path = event.get('rawPath', '')
    ip_address = path.split('/')[-1]

    table = dynamodb.Table(IP_TABLE)
    result = table.get_item(Key={'ip_address': ip_address})

    if 'Item' not in result:
        return response(404, {'error': 'IP not found'})

    return response(200, {'ip': convert_decimals(result['Item'])})


def update_ip(event):
    """
    Update IP allocation details

    Body:
    {
        "hostname": "new-hostname",
        "description": "Updated description",
        "status": "deprecated"
    }
    """
    path = event.get('rawPath', '')
    ip_address = path.split('/')[-1]

    body = json.loads(event.get('body', '{}'))

    # Check if IP exists
    table = dynamodb.Table(IP_TABLE)
    result = table.get_item(Key={'ip_address': ip_address})

    if 'Item' not in result:
        return response(404, {'error': 'IP not found'})

    # Build update expression
    update_expr = "SET updated_at = :updated_at"
    expr_values = {':updated_at': datetime.now().isoformat()}

    updatable_fields = ['hostname', 'description', 'status', 'mac_address',
                        'owner', 'device_type', 'location']

    for field in updatable_fields:
        if field in body:
            update_expr += f", {field} = :{field}"
            expr_values[f':{field}'] = body[field]

    # Update item
    table.update_item(
        Key={'ip_address': ip_address},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_values
    )

    # Get updated item
    result = table.get_item(Key={'ip_address': ip_address})

    # Log to audit
    log_audit('ip_updated', ip_address, body)

    return response(200, {
        'message': 'IP updated successfully',
        'ip': convert_decimals(result['Item'])
    })


def release_ip(event):
    """Release (delete) IP allocation"""
    path = event.get('rawPath', '')
    ip_address = path.split('/')[-1]

    # Get IP info before deleting
    table = dynamodb.Table(IP_TABLE)
    result = table.get_item(Key={'ip_address': ip_address})

    if 'Item' not in result:
        return response(404, {'error': 'IP not found'})

    item = result['Item']
    subnet_id = item['subnet_id']

    # Delete allocation
    table.delete_item(Key={'ip_address': ip_address})

    # Update subnet utilization
    update_subnet_utilization(subnet_id)

    # Log to audit
    log_audit('ip_released', ip_address, item)

    return response(200, {'message': 'IP released successfully'})


def search(event):
    """
    Global search across IPs and subnets

    Query params:
    - q: Search query
    """
    query_params = event.get('queryStringParameters', {}) or {}
    query = query_params.get('q', '').lower()

    if not query:
        return response(400, {'error': 'Search query (q) is required'})

    results = {
        'ips': [],
        'subnets': []
    }

    # Search IPs
    ip_table = dynamodb.Table(IP_TABLE)
    ip_response = ip_table.scan()
    ip_items = ip_response.get('Items', [])

    results['ips'] = [
        item for item in ip_items
        if query in item.get('ip_address', '').lower()
           or query in item.get('hostname', '').lower()
           or query in item.get('description', '').lower()
           or query in item.get('owner', '').lower()
    ]

    # Search subnets
    subnet_table = dynamodb.Table(SUBNETS_TABLE)
    subnet_response = subnet_table.scan()
    subnet_items = subnet_response.get('Items', [])

    results['subnets'] = [
        item for item in subnet_items
        if query in item.get('subnet_id', '').lower()
           or query in item.get('description', '').lower()
           or query in item.get('site', '').lower()
    ]

    return response(200, {
        'results': convert_decimals(results),
        'total': len(results['ips']) + len(results['subnets'])
    })


# Helper functions

def get_subnet_info(subnet_id: str) -> dict:
    """Get subnet from DynamoDB"""
    table = dynamodb.Table(SUBNETS_TABLE)
    result = table.get_item(Key={'subnet_id': subnet_id})
    return result.get('Item')


def is_ip_allocated(ip_address: str) -> bool:
    """Check if IP is already allocated"""
    table = dynamodb.Table(IP_TABLE)
    result = table.get_item(Key={'ip_address': ip_address})
    return 'Item' in result


def get_allocated_ips_in_subnet(subnet_id: str) -> list:
    """Get list of allocated IP addresses in subnet"""
    table = dynamodb.Table(IP_TABLE)
    response_data = table.query(
        IndexName='subnet-index',
        KeyConditionExpression='subnet_id = :subnet_id',
        ExpressionAttributeValues={':subnet_id': subnet_id}
    )
    items = response_data.get('Items', [])
    return [item['ip_address'] for item in items]


def update_subnet_utilization(subnet_id: str):
    """Recalculate and update subnet utilization"""
    # Get subnet
    subnet = get_subnet_info(subnet_id)
    if not subnet:
        return

    # Count allocated IPs
    allocated_count = len(get_allocated_ips_in_subnet(subnet_id))

    # Calculate utilization
    from subnet_calculator import SubnetCalculator
    utilization = SubnetCalculator.calculate_utilization(
        allocated_count,
        subnet['usable_ips']
    )

    # Update subnet
    table = dynamodb.Table(SUBNETS_TABLE)
    table.update_item(
        Key={'subnet_id': subnet_id},
        UpdateExpression='SET allocated_count = :count, utilization = :util, updated_at = :time',
        ExpressionAttributeValues={
            ':count': allocated_count,
            ':util': Decimal(str(utilization)),
            ':time': datetime.now().isoformat()
        }
    )


def log_audit(action: str, resource_id: str, details: dict):
    """Log action to audit trail"""
    import uuid

    table = dynamodb.Table(AUDIT_TABLE)
    timestamp = int(datetime.now().timestamp())

    table.put_item(Item={
        'log_id': str(uuid.uuid4()),
        'timestamp': timestamp,
        'ttl': timestamp + (90 * 24 * 60 * 60),  # 90 days
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