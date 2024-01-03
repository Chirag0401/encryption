import boto3
import os
from botocore.exceptions import ClientError

def create_session():
    """Create a Boto3 session using environment variables."""
    return boto3.Session(
        region_name=os.environ.get('AWS_DEFAULT_REGION'),
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.environ.get('AWS_SESSION_TOKEN')
    )

def get_resolver_rule_id(client, rule_name):
    """Get the ID of the resolver rule by name."""
    paginator = client.get_paginator('list_resolver_rules')
    for page in paginator.paginate():
        for rule in page['ResolverRules']:
            if rule['Name'] == rule_name:
                return rule['Id']
    return None

def create_resolver_rule(client, rule_name, domain, targets, resolver_endpoint_id):
    """Create a new resolver rule."""
    try:
        response = client.create_resolver_rule(
            CreatorRequestId=f'create_{rule_name}',
            Name=rule_name,
            RuleType='FORWARD',
            DomainName=domain,
            TargetIps=targets,
            ResolverEndpointId=resolver_endpoint_id
        )
        return response['ResolverRule']['Id']
    except ClientError as e:
        print(f"Error creating rule for {domain}: {e}")
        return None

def associate_resolver_rule(client, rule_id, vpc_id, rule_name):
    """Associate a resolver rule with a VPC."""
    try:
        client.associate_resolver_rule(
            ResolverRuleId=rule_id,
            VPCId=vpc_id,
            Name=rule_name
        )
    except ClientError as e:
        print(f"Error associating rule {rule_name} with VPC {vpc_id}: {e}")

# Create a Boto3 session
session = create_session()

# Initialize the Route 53 Resolver client
client = session.client('route53resolver')

# List of domains and target IPs
domains = [
    "ops.ped.local", "patch.bcs.local", "develop.bcs.local",
    "sit.bcs.local", "ppe.bcs.local", "ppe.shp.local", "ppe.wpt.local"
]

targets = [
    {'Ip': '10.140.206.43', 'Port': 53},
    {'Ip': '10.140.206.76', 'Port': 53},
    {'Ip': '10.140.206.181', 'Port': 53},
    {'Ip': '10.141.17.26', 'Port': 53},
    {'Ip': '10.141.17.97', 'Port': 53},
    {'Ip': '10.141.17.233', 'Port': 53}
]

for domain in domains:
    print(f"\nProcessing domain: {domain}")
    vpc_id = input("Enter the VPC ID to associate with the rule: ")
    resolver_endpoint_id = input("Enter the Resolver Endpoint ID: ")

    rule_name = domain.replace('.', '-')
    rule_id = get_resolver_rule_id(client, rule_name)

    if rule_id:
        print(f"Rule {rule_name} already exists.")
    else:
        rule_id = create_resolver_rule(client, rule_name, domain, targets, resolver_endpoint_id)
        if rule_id:
            print(f"Created rule {rule_name}: {rule_id}")
            associate_resolver_rule(client, rule_id, vpc_id, rule_name)
            print(f"Associated rule {rule_name} with VPC {vpc_id}")




# [ec2-user@ip-10-140-241-119 route_resolver]$ python3 rule_resolver.py                                                                                      Enter the VPC ID to associate with the rules: vpc-05398baa4fb7c969c
# Enter the Resolver Endpoint ID: rslvr-out-17e0606ca0094a219
# Rule ops-ped-local already exists.
# Rule patch-bcs-local already exists.
# Traceback (most recent call last):
#   File "rule_resolver.py", line 83, in <module>
#     rule_id = create_resolver_rule(client, rule_name, domain, targets, resolver_endpoint_id)
#   File "rule_resolver.py", line 33, in create_resolver_rule
#     RuleAction='FORWARD'
#   File "/home/ec2-user/.local/lib/python3.7/site-packages/botocore/client.py", line 553, in _api_call
#     return self._make_api_call(operation_name, kwargs)
#   File "/home/ec2-user/.local/lib/python3.7/site-packages/botocore/client.py", line 967, in _make_api_call
#     headers=additional_headers,
#   File "/home/ec2-user/.local/lib/python3.7/site-packages/botocore/client.py", line 1037, in _convert_to_request_dict
#     api_params, operation_model
#   File "/home/ec2-user/.local/lib/python3.7/site-packages/botocore/validate.py", line 381, in serialize_to_request
#     raise ParamValidationError(report=report.generate_report())
# botocore.exceptions.ParamValidationError: Parameter validation failed:
# Unknown parameter in input: "RuleAction", must be one of: CreatorRequestId, Name, RuleType, DomainName, TargetIps, ResolverEndpointId, Tags
