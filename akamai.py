import boto3
import os
import pandas as pd

# Retrieve AWS credentials and configuration from environment variables.
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')
SESSION_TOKEN = os.environ.get('AWS_SESSION_TOKEN')
REGION_NAME = os.environ.get('AWS_REGION')

# Establish a client connection to AWS EC2.
ec2_client = boto3.client('ec2', 
                          aws_access_key_id=AWS_ACCESS_KEY, 
                          aws_secret_access_key=AWS_SECRET_KEY, 
                          region_name=REGION_NAME,
                          aws_session_token=SESSION_TOKEN)

def get_existing_sg_ips(sg_id):
    """Retrieve the existing IPs from a given security group."""
    response = ec2_client.describe_security_groups(GroupIds=[sg_id])
    permissions = response['SecurityGroups'][0]['IpPermissions']
    
    existing_ips = []
    for permission in permissions:
        if permission['FromPort'] == 443 and permission['ToPort'] == 443 and permission['IpProtocol'] == 'tcp':
            for range in permission['IpRanges']:
                existing_ips.append(range['CidrIp'])
                
    return existing_ips

def update_security_group(sg_id, new_ips):
    """Update the security group with the new set of IPs."""
    existing_ips = get_existing_sg_ips(sg_id)
    
    # Determine which IPs to revoke and which to authorize.
    ips_to_revoke = list(set(existing_ips) - set(new_ips))
    ips_to_authorize = list(set(new_ips) - set(existing_ips))

    # Remove outdated IPs.
    if ips_to_revoke:
        ec2_client.revoke_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 443,
                    'ToPort': 443,
                    'IpRanges': [{'CidrIp': ip} for ip in ips_to_revoke]
                }
            ]
        )
    
    # Add the new set of IPs.
    if ips_to_authorize:
        ec2_client.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 443,
                    'ToPort': 443,
                    'IpRanges': [{'CidrIp': ip} for ip in ips_to_authorize[:60]]
                }
            ]
        )
        left_out_ips = ips_to_authorize[60:]
        return left_out_ips
    
    return []

def create_security_group(vpc_id, left_out_ips):
    """Create a new security group and assign it the remaining set of IPs."""
    response = ec2_client.create_security_group(
        GroupName='AkamaiExtraIPs',
        Description='Security group for leftover Akamai IPs',
        VpcId=vpc_id
    )
    new_sg_id = response['GroupId']
    
    ec2_client.authorize_security_group_ingress(
        GroupId=new_sg_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 443,
                'ToPort': 443,
                'IpRanges': [{'CidrIp': ip} for ip in left_out_ips]
            }
        ]
    )
    return new_sg_id

def main():
    """Main execution function."""
    akamai_sg_prefix = 'akamai'
    vpc_id = 'your_vpc_id'

    # Extract IP addresses from Excel.
    df = pd.read_excel('path_to_excel.xlsx')
    new_ips = df['IPs'].tolist()

    # Filter and update security groups named with prefix 'akamai'.
    sgs = ec2_client.describe_security_groups()
    for sg in sgs['SecurityGroups']:
        if sg['GroupName'].startswith(akamai_sg_prefix):
            left_out_ips = update_security_group(sg['GroupId'], new_ips)
            if left_out_ips:
                new_sg_id = create_security_group(vpc_id, left_out_ips)
                print(f"Created new security group {new_sg_id} for leftover IPs.")

if __name__ == "__main__":
    main()
