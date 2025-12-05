"""
API Gateway for IPAM system
"""
import pulumi
import pulumi_aws as aws

def create_ipam_api(project_name: str, functions: dict, tags: dict):
    """Create API Gateway with routes for all IPAM operations"""
    
    subnet_function = functions['subnet_function']
    ip_function = functions['ip_function']
    
    # HTTP API Gateway
    api = aws.apigatewayv2.Api(
        f"{project_name}-api",
        name=f"{project_name}-ipam-api",
        protocol_type="HTTP",
        cors_configuration=aws.apigatewayv2.ApiCorsConfigurationArgs(
            allow_origins=["*"],
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["content-type", "authorization"],
            max_age=300,
        ),
        tags=tags,
    )
    
    # Lambda Integrations
    subnet_integration = aws.apigatewayv2.Integration(
        f"{project_name}-subnet-integration",
        api_id=api.id,
        integration_type="AWS_PROXY",
        integration_uri=subnet_function.arn,
        integration_method="POST",
        payload_format_version="2.0",
    )
    
    ip_integration = aws.apigatewayv2.Integration(
        f"{project_name}-ip-integration",
        api_id=api.id,
        integration_type="AWS_PROXY",
        integration_uri=ip_function.arn,
        integration_method="POST",
        payload_format_version="2.0",
    )
    
    # API Routes - Subnets
    aws.apigatewayv2.Route(f"{project_name}-route-create-subnet", api_id=api.id, route_key="POST /subnets", target=subnet_integration.id.apply(lambda id: f"integrations/{id}"))
    aws.apigatewayv2.Route(f"{project_name}-route-list-subnets", api_id=api.id, route_key="GET /subnets", target=subnet_integration.id.apply(lambda id: f"integrations/{id}"))
    aws.apigatewayv2.Route(f"{project_name}-route-get-subnet", api_id=api.id, route_key="GET /subnets/{id}", target=subnet_integration.id.apply(lambda id: f"integrations/{id}"))
    aws.apigatewayv2.Route(f"{project_name}-route-delete-subnet", api_id=api.id, route_key="DELETE /subnets/{id}", target=subnet_integration.id.apply(lambda id: f"integrations/{id}"))
    aws.apigatewayv2.Route(f"{project_name}-route-calculate-subnet", api_id=api.id, route_key="GET /subnets/calculate", target=subnet_integration.id.apply(lambda id: f"integrations/{id}"))
    
    # API Routes - IPs
    aws.apigatewayv2.Route(f"{project_name}-route-allocate-ip", api_id=api.id, route_key="POST /ips", target=ip_integration.id.apply(lambda id: f"integrations/{id}"))
    aws.apigatewayv2.Route(f"{project_name}-route-auto-allocate-ip", api_id=api.id, route_key="POST /ips/auto", target=ip_integration.id.apply(lambda id: f"integrations/{id}"))
    aws.apigatewayv2.Route(f"{project_name}-route-list-ips", api_id=api.id, route_key="GET /ips", target=ip_integration.id.apply(lambda id: f"integrations/{id}"))
    aws.apigatewayv2.Route(f"{project_name}-route-get-ip", api_id=api.id, route_key="GET /ips/{ip}", target=ip_integration.id.apply(lambda id: f"integrations/{id}"))
    aws.apigatewayv2.Route(f"{project_name}-route-update-ip", api_id=api.id, route_key="PUT /ips/{ip}", target=ip_integration.id.apply(lambda id: f"integrations/{id}"))
    aws.apigatewayv2.Route(f"{project_name}-route-release-ip", api_id=api.id, route_key="DELETE /ips/{ip}", target=ip_integration.id.apply(lambda id: f"integrations/{id}"))
    aws.apigatewayv2.Route(f"{project_name}-route-search", api_id=api.id, route_key="GET /search", target=ip_integration.id.apply(lambda id: f"integrations/{id}"))
    
    # API Stage
    stage = aws.apigatewayv2.Stage(
        f"{project_name}-api-stage",
        api_id=api.id,
        name="prod",
        auto_deploy=True,
        tags=tags,
    )
    
    # Lambda Permissions
    aws.lambda_.Permission(f"{project_name}-subnet-permission", action="lambda:InvokeFunction", function=subnet_function.name, principal="apigateway.amazonaws.com", source_arn=pulumi.Output.concat(api.execution_arn, "/*/*"))
    aws.lambda_.Permission(f"{project_name}-ip-permission", action="lambda:InvokeFunction", function=ip_function.name, principal="apigateway.amazonaws.com", source_arn=pulumi.Output.concat(api.execution_arn, "/*/*"))
    
    api_endpoint = pulumi.Output.concat(api.api_endpoint, "/", stage.name)
    pulumi.export("api_id", api.id)
    pulumi.export("api_endpoint", api_endpoint)
    
    return {"api": api, "api_endpoint": api_endpoint, "stage": stage}
