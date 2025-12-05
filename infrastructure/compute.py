"""
Lambda functions for IPAM system
"""
import pulumi
import pulumi_aws as aws
import json

def create_lambda_functions(project_name: str, tables: dict, tags: dict):
    """
    Create Lambda functions for IPAM operations
    
    Args:
        project_name: Project name
        tables: DynamoDB tables from storage.py
        tags: Common tags
    """
    
    # IAM Role for Lambda
    lambda_role = aws.iam.Role(
        f"{project_name}-lambda-role",
        assume_role_policy=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Action": "sts:AssumeRole",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Effect": "Allow",
            }]
        }),
        tags=tags,
    )
    
    # Attach basic Lambda execution policy
    aws.iam.RolePolicyAttachment(
        f"{project_name}-lambda-basic",
        role=lambda_role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    )
    
    # Custom policy for DynamoDB access
    lambda_policy = aws.iam.RolePolicy(
        f"{project_name}-lambda-policy",
        role=lambda_role.id,
        policy=pulumi.Output.all(
            tables['subnets_table'].arn,
            tables['ip_allocations_table'].arn,
            tables['vlans_table'].arn,
            tables['audit_table'].arn,
        ).apply(lambda arns: json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "dynamodb:PutItem",
                    "dynamodb:GetItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                "Resource": [
                    arns[0],
                    f"{arns[0]}/index/*",
                    arns[1],
                    f"{arns[1]}/index/*",
                    arns[2],
                    arns[3],
                    f"{arns[3]}/index/*",
                ]
            }]
        }))
    )
    
    # Environment Variables for Lambda
    lambda_env = {
        "SUBNETS_TABLE": tables['subnets_table'].name,
        "IP_TABLE": tables['ip_allocations_table'].name,
        "VLANS_TABLE": tables['vlans_table'].name,
        "AUDIT_TABLE": tables['audit_table'].name,
    }
    
    # Subnet Manager Lambda
    subnet_function = aws.lambda_.Function(
        f"{project_name}-subnet-manager",
        name=f"{project_name}-subnet-manager",
        runtime="python3.11",
        handler="handler.lambda_handler",
        role=lambda_role.arn,
        timeout=30,
        memory_size=256,
        code=pulumi.AssetArchive({
            '.': pulumi.FileArchive("./lambda_functions/subnet_manager")
        }),
        environment=aws.lambda_.FunctionEnvironmentArgs(
            variables=lambda_env
        ),
        tags={**tags, "Function": "SubnetManager"},
    )
    
    # IP Manager Lambda  
    ip_function = aws.lambda_.Function(
        f"{project_name}-ip-manager",
        name=f"{project_name}-ip-manager",
        runtime="python3.11",
        handler="handler.lambda_handler",
        role=lambda_role.arn,
        timeout=30,
        memory_size=256,
        code=pulumi.AssetArchive({
            'handler.py': pulumi.FileAsset("./lambda_functions/ip_manager/handler.py"),
            'validators.py': pulumi.FileAsset("./lambda_functions/ip_manager/validators.py"),
            'subnet_calculator.py': pulumi.FileAsset("./lambda_functions/subnet_manager/subnet_calculator.py"),
        }),
        environment=aws.lambda_.FunctionEnvironmentArgs(
            variables=lambda_env
        ),
        tags={**tags, "Function": "IPManager"},
    )
    
    pulumi.export("subnet_function_name", subnet_function.name)
    pulumi.export("ip_function_name", ip_function.name)
    
    return {
        "subnet_function": subnet_function,
        "ip_function": ip_function,
        "lambda_role": lambda_role,
    }
