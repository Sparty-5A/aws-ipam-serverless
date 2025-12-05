"""
DynamoDB tables for IPAM system

Tables:
1. subnets - Subnet inventory with VLAN mapping
2. ip_allocations - Individual IP address assignments
3. vlans - VLAN database
4. audit_log - Change history with 90-day retention
"""

import pulumi
import pulumi_aws as aws

def create_ipam_storage(project_name: str, tags: dict):
    """
    Create DynamoDB tables for IPAM
    
    Args:
        project_name: Project name for resource naming
        tags: Common tags for all resources
    
    Returns:
        dict with table resources
    """
    
    # ==========================================
    # Subnets Table
    # ==========================================
    subnets_table = aws.dynamodb.Table(
        f"{project_name}-subnets",
        name=f"{project_name}-subnets",
        
        # Primary key: subnet_id (e.g., "10.0.1.0_24")
        hash_key="subnet_id",
        
        attributes=[
            aws.dynamodb.TableAttributeArgs(
                name="subnet_id",
                type="S",  # String
            ),
            aws.dynamodb.TableAttributeArgs(
                name="vlan_id",
                type="N",  # Number
            ),
            aws.dynamodb.TableAttributeArgs(
                name="site",
                type="S",  # String
            ),
        ],
        
        # Global Secondary Indexes for querying
        global_secondary_indexes=[
            # Query by VLAN
            aws.dynamodb.TableGlobalSecondaryIndexArgs(
                name="vlan-index",
                hash_key="vlan_id",
                projection_type="ALL",
                read_capacity=1,
                write_capacity=1,
            ),
            # Query by site/location
            aws.dynamodb.TableGlobalSecondaryIndexArgs(
                name="site-index",
                hash_key="site",
                projection_type="ALL",
                read_capacity=1,
                write_capacity=1,
            ),
        ],
        
        # On-demand billing (pay per request, free tier eligible)
        billing_mode="PAY_PER_REQUEST",
        
        # Enable point-in-time recovery (backups)
        point_in_time_recovery=aws.dynamodb.TablePointInTimeRecoveryArgs(
            enabled=True,
        ),
        
        tags={**tags, "Purpose": "Subnet inventory"},
    )
    
    # ==========================================
    # IP Allocations Table
    # ==========================================
    ip_allocations_table = aws.dynamodb.Table(
        f"{project_name}-ip-allocations",
        name=f"{project_name}-ip-allocations",
        
        # Primary key: ip_address (e.g., "10.0.1.10")
        hash_key="ip_address",
        
        attributes=[
            aws.dynamodb.TableAttributeArgs(
                name="ip_address",
                type="S",
            ),
            aws.dynamodb.TableAttributeArgs(
                name="subnet_id",
                type="S",
            ),
            aws.dynamodb.TableAttributeArgs(
                name="status",
                type="S",
            ),
            aws.dynamodb.TableAttributeArgs(
                name="hostname",
                type="S",
            ),
        ],
        
        global_secondary_indexes=[
            # Query all IPs in a subnet
            aws.dynamodb.TableGlobalSecondaryIndexArgs(
                name="subnet-index",
                hash_key="subnet_id",
                projection_type="ALL",
                read_capacity=1,
                write_capacity=1,
            ),
            # Query by status (active, reserved, deprecated)
            aws.dynamodb.TableGlobalSecondaryIndexArgs(
                name="status-index",
                hash_key="status",
                projection_type="ALL",
                read_capacity=1,
                write_capacity=1,
            ),
            # Query by hostname
            aws.dynamodb.TableGlobalSecondaryIndexArgs(
                name="hostname-index",
                hash_key="hostname",
                projection_type="ALL",
                read_capacity=1,
                write_capacity=1,
            ),
        ],
        
        billing_mode="PAY_PER_REQUEST",
        point_in_time_recovery=aws.dynamodb.TablePointInTimeRecoveryArgs(
            enabled=True,
        ),
        
        tags={**tags, "Purpose": "IP address allocations"},
    )
    
    # ==========================================
    # VLANs Table
    # ==========================================
    vlans_table = aws.dynamodb.Table(
        f"{project_name}-vlans",
        name=f"{project_name}-vlans",
        
        hash_key="vlan_id",
        
        attributes=[
            aws.dynamodb.TableAttributeArgs(
                name="vlan_id",
                type="N",
            ),
        ],
        
        billing_mode="PAY_PER_REQUEST",
        
        tags={**tags, "Purpose": "VLAN database"},
    )
    
    # ==========================================
    # Audit Log Table
    # ==========================================
    audit_table = aws.dynamodb.Table(
        f"{project_name}-audit-log",
        name=f"{project_name}-audit-log",
        
        hash_key="log_id",
        range_key="timestamp",
        
        attributes=[
            aws.dynamodb.TableAttributeArgs(
                name="log_id",
                type="S",
            ),
            aws.dynamodb.TableAttributeArgs(
                name="timestamp",
                type="N",
            ),
            aws.dynamodb.TableAttributeArgs(
                name="action_type",
                type="S",
            ),
        ],
        
        global_secondary_indexes=[
            aws.dynamodb.TableGlobalSecondaryIndexArgs(
                name="action-type-index",
                hash_key="action_type",
                range_key="timestamp",
                projection_type="ALL",
                read_capacity=1,
                write_capacity=1,
            ),
        ],
        
        billing_mode="PAY_PER_REQUEST",
        
        # Auto-delete old logs after 90 days
        ttl=aws.dynamodb.TableTtlArgs(
            attribute_name="ttl",
            enabled=True,
        ),
        
        tags={**tags, "Purpose": "Audit trail"},
    )
    
    # ==========================================
    # Exports
    # ==========================================
    pulumi.export("subnets_table_name", subnets_table.name)
    pulumi.export("ip_allocations_table_name", ip_allocations_table.name)
    pulumi.export("vlans_table_name", vlans_table.name)
    pulumi.export("audit_table_name", audit_table.name)
    
    return {
        "subnets_table": subnets_table,
        "ip_allocations_table": ip_allocations_table,
        "vlans_table": vlans_table,
        "audit_table": audit_table,
    }
