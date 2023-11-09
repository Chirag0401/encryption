import boto3
import os
import pandas as pd
import ipaddress

# AWS Configuration
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')
AWS_SESSION_TOKEN = os.environ.get('AWS_SESSION_TOKEN')  
REGION_NAME = os.environ.get('REGION_NAME')

ec2_client = boto3.client('ec2', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, aws_session_token=AWS_SESSION_TOKEN, region_name=REGION_NAME)

def is_ipv4(ip):
    """Check if the given IP is IPv4."""
    try:
        return ipaddress.ip_address(ip.split('/')[0]).version == 4
    except ValueError:
        return False

def load_ips_from_excel(sheet_name):
    """Load IPv4 addresses from the specified Excel sheet."""
    df = pd.read_excel('path_to_excel.xlsx', sheet_name=sheet_name)
    all_ips = df['IP Address Range'].tolist()
    ipv4_ips = [ip for ip in all_ips if is_ipv4(ip)]
    return ipv4_ips

def create_security_group(vpc_id, sg_name, ips):
    """Create a new security group and add the specified IPs to it."""
    response = ec2_client.create_security_group(
        GroupName=sg_name,
        Description=f"Security group for additional IPs {sg_name}",
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

def add_ips_to_sg(sg_id, ips):
    """Attempt to add IPs to a security group and handle quota exceedance."""
    try:
        ec2_client.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 443,
                    'ToPort': 443,
                    'IpRanges': [{'CidrIp': ip} for ip in ips]
                }
            ]
        )
        print(f"Added {len(ips)} IPs to the security group {sg_id}.")
    except Exception as e:
        print(f"An error occurred: {e}")
        if "RulesPerSecurityGroupLimitExceeded" in str(e):
            return False
    return True

def main():
    sheet_name = input('Enter the name of the sheet you want to use: ')
    new_ips = load_ips_from_excel(sheet_name)

    vpc_id = input('Enter your VPC ID: ')
    security_group_name = input('Enter the name of the existing security group (leave blank to create a new one): ')

    if security_group_name:
        # Existing security group logic
        sg_info = ec2_client.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': [security_group_name]}])
        sg = sg_info.get('SecurityGroups', [{}])[0]
        sg_id = sg.get('GroupId')

        if not sg_id:
            print(f"No security group found with the name {security_group_name}")
            return

        # Add new IPs to the existing security group
        success = add_ips_to_sg(sg_id, new_ips)
        if not success:
            create_new_sg = input("The limit is exceeded. Do you want to create a new security group for the remaining IPs? (yes/no): ")
            if create_new_sg.lower() == 'yes':
                new_sg_name = input("Enter the name for the new security group: ")
                new_sg_id = create_security_group(vpc_id, new_sg_name, new_ips)
                print(f"Created new security group {new_sg_id} and added {len(new_ips)} IPs.")

    else:
        # Logic for creating a new security group
        print("No existing security group mentioned. We will be adding the IPs into a new security group.")
        new_sg_name = input("Enter the name for the new security group: ")
        new_sg_id = create_security_group(vpc_id, new_sg_name, new_ips)
        print(f"Created new security group {new_sg_id} and added {len(new_ips)} IPs.")

if __name__ == '__main__':
    main()
#An error occurred: An error occurred (InvalidPermission.Duplicate) when calling the AuthorizeSecurityGroupIngress operation: the specified rule "peer: 104.115.39.0/24, TCP, from port: 443, to port: 443, ALLOW" already exists
