import boto3
import os
import pandas as pd
import ipaddress

AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')
AWS_SESSION_TOKEN = os.environ.get('AWS_SESSION_TOKEN')  
REGION_NAME = os.environ.get('REGION_NAME')

ec2_client = boto3.client('ec2', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, aws_session_token=AWS_SESSION_TOKEN, region_name=REGION_NAME)

def is_ipv4(ip):
    """Check if the given IP is IPv4."""
    try:
        ipaddress.ip_address(ip.split('/')[0])
        return True
    except ValueError:
        return False

def load_ips_from_excel(sheet_name):
    """Load IPv4 addresses from the specified Excel sheet."""
    df = pd.read_excel('path_to_excel.xlsx', sheet_name=sheet_name)
    all_ips = df['IP Address Range'].tolist()
    ipv4_ips = [ip for ip in all_ips if is_ipv4(ip)]
    return ipv4_ips

def remove_existing_ips(sg_id):
    """Remove all existing IPs from the specified security group."""
    response = ec2_client.describe_security_groups(GroupIds=[sg_id])
    permissions = response.get('SecurityGroups', [{}])[0].get('IpPermissions', [])

    existing_ips = []
    for permission in permissions:
        if permission['FromPort'] == 443 and permission['ToPort'] == 443 and permission['IpProtocol'] == 'tcp':
            for range in permission['IpRanges']:
                existing_ips.append(range['CidrIp'])

    if existing_ips:
        ec2_client.revoke_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 443,
                    'ToPort': 443,
                    'IpRanges': [{'CidrIp': ip} for ip in existing_ips]
                }
            ]
        )

def get_next_available_sg_name(base_name):
    """Find the next available name for the security group."""
    count = 1
    while True:
        potential_name = f"{base_name}-{count}"
        sgs = ec2_client.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': [potential_name]}])
        if not sgs.get('SecurityGroups', []):
            return potential_name
        count += 1

def create_security_group(vpc_id, base_name, ips):
    """Create a new security group and add the specified IPs to it."""
    new_sg_name = get_next_available_sg_name(base_name)
    
    response = ec2_client.create_security_group(
        GroupName=new_sg_name,
        Description=f"Security group for Akamai IPs {new_sg_name.split('-')[-1]}",
        VpcId=vpc_id
    )
    new_sg_id = response.get('GroupId')

    if not new_sg_id:
        raise ValueError("Failed to create a new security group")

    ec2_client.authorize_security_group_ingress(
        GroupId=new_sg_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 443,
                'ToPort': 443,
                'IpRanges': [{'CidrIp': ip} for ip in ips]
            }
        ]
    )
    return new_sg_id

def create_combined_security_group(vpc_id, sg_ids):
    """Create a combined security group with inbound rules referencing other security groups."""
    combined_sg_name = "combined-akamai-sg"
    response = ec2_client.create_security_group(
        GroupName=combined_sg_name,
        Description="Combined security group for Akamai IPs",
        VpcId=vpc_id
    )
    combined_sg_id = response.get('GroupId')
    if not combined_sg_id:
        raise ValueError("Failed to create a combined security group")

    for sg_id in sg_ids:
        ec2_client.authorize_security_group_ingress(
            GroupId=combined_sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 443,
                    'ToPort': 443,
                    'UserIdGroupPairs': [{'GroupId': sg_id}]
                }
            ]
        )
    return combined_sg_id

def main():
    sheet_name = input('Enter the name of the sheet you want to use: ')
    new_ips = load_ips_from_excel(sheet_name)

    vpc_id = 'your_vpc_id'
    
    security_group_names = ['akamai-sg-1']  # Start with one SG for testing
    created_sg_ids = []

    for sg_name in security_group_names:
        sgs = ec2_client.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': [sg_name]}])
        sg_id = sgs.get('SecurityGroups', [{}])[0].get('GroupId')
        created_sg_ids.append(sg_id)

        if not sg_id:
            continue

        # Remove old IPs
        remove_existing_ips(sg_id)

        # Add the new IPs in chunks of 60
        while new_ips:
            ips_chunk = new_ips[:60]
            new_ips = new_ips[60:]

            # If it's the original SG we're updating, use its ID directly
            if sg_name == security_group_names[0] and not new_ips:
                ec2_client.authorize_security_group_ingress(
                    GroupId=sg_id,
                    IpPermissions=[
                        {
                            'IpProtocol': 'tcp',
                            'FromPort': 443,
                            'ToPort': 443,
                            'IpRanges': [{'CidrIp': ip} for ip in ips_chunk]
                        }
                    ]
                )
            else:
                # Otherwise, create a new SG and add IPs to it
                new_sg_id = create_security_group(vpc_id, "akamai-sg", ips_chunk)
                created_sg_ids.append(new_sg_id)
                print(f"Created new security group {new_sg_id} and added IPs")

    # Create the combined security group
    combined_sg_id = create_combined_security_group(vpc_id, created_sg_ids)
    print(f"Created combined security group {combined_sg_id}")

if __name__ == '__main__':
    main()




# BCS_PATCH_MGT_2-[ec2-user@ip-10-140-238-37 Akamai]$ python3 akamai.py
# Enter the name of the sheet you want to use: APAC_Staging_GTM
# Created new security group sg-05905c482d6793d05 and added IPs
# Created new security group sg-01df672ea89af5145 and added IPs
# Traceback (most recent call last):
#   File "akamai.py", line 165, in <module>
#     main()
#   File "akamai.py", line 156, in main
#     new_sg_id = create_security_group(vpc_id, "akamai-sg", ips_chunk)
#   File "akamai.py", line 84, in create_security_group
#     'IpRanges': [{'CidrIp': ip} for ip in ips]
#   File "/home/ec2-user/.local/lib/python3.7/site-packages/botocore/client.py", line 535, in _api_call
#     return self._make_api_call(operation_name, kwargs)
#   File "/home/ec2-user/.local/lib/python3.7/site-packages/botocore/client.py", line 980, in _make_api_call
#     raise error_class(parsed_response, operation_name)
# botocore.exceptions.ClientError: An error occurred (InvalidParameterValue) when calling the AuthorizeSecurityGroupIngress operation: CIDR block 2600:14a0::/40 is malformed

