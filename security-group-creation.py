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
    try:
        return ipaddress.ip_address(ip.split('/')[0]).version == 4
    except ValueError:
        return False

def load_ips_from_excel(sheet_name):
    df = pd.read_excel('path_to_excel.xlsx', sheet_name=sheet_name)
    all_ips = df['IP Address Range'].tolist()
    ipv4_ips = [ip for ip in all_ips if is_ipv4(ip)]
    return ipv4_ips

def remove_existing_ips(sg_id):
    response = ec2_client.describe_security_groups(GroupIds=[sg_id])
    permissions = response.get('SecurityGroups', [{}])[0].get('IpPermissions', [])
    if permissions:
        ec2_client.revoke_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=permissions
        )

def get_next_available_sg_name(base_name):
    count = 1
    while True:
        potential_name = f"{base_name}-{count}"
        sgs = ec2_client.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': [potential_name]}])
        if not sgs.get('SecurityGroups', []):
            return potential_name
        count += 1

def create_security_group(vpc_id, base_name, ips):
    new_sg_name = get_next_available_sg_name(base_name)
    response = ec2_client.create_security_group(
        GroupName=new_sg_name,
        Description=f"Security group {new_sg_name.split('-')[-1]}",
        VpcId=vpc_id
    )
    new_sg_id = response.get('GroupId')
    return new_sg_id

def main():
    vpc_id = input('Enter the VPC ID: ')
    ip_protocol = input('Enter the IP Protocol (e.g., tcp, udp): ')
    port_range = input('Enter the port or port range (e.g., 80 or 9000-9098): ')
    if '-' in port_range:
        from_port, to_port = map(int, port_range.split('-'))
    else:
        from_port = to_port = int(port_range)
    security_group_names_input = input('Enter the security group names separated by comma: ')
    security_group_names = [name.strip() for name in security_group_names_input.split(',')]
    base_sg_name = input('Enter the base name for new security groups: ')
    sheet_name = input('Enter the name of the sheet you want to use: ')
    new_ips = load_ips_from_excel(sheet_name)
    for sg_name in security_group_names:
        sgs = ec2_client.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': [sg_name]}])
        sg_id = sgs.get('SecurityGroups', [{}])[0].get('GroupId')
        if not sg_id:
            continue
        remove_existing_ips(sg_id)
        if new_ips:
            ips_chunk = new_ips[:195]
            new_ips = new_ips[195:]
            ec2_client.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=[
                    {
                        'IpProtocol': ip_protocol,
                        'FromPort': from_port,
                        'ToPort': to_port,
                        'IpRanges': [{'CidrIp': ip} for ip in ips_chunk]
                    }
                ]
            )
    while new_ips:
        ips_chunk = new_ips[:195]
        new_ips = new_ips[195:]
        new_sg_id = create_security_group(vpc_id, base_sg_name, ips_chunk)
        ec2_client.authorize_security_group_ingress(
            GroupId=new_sg_id,
            IpPermissions=[
                {
                    'IpProtocol': ip_protocol,
                    'FromPort': from_port,
                    'ToPort': to_port,
                    'IpRanges': [{'CidrIp': ip} for ip in ips_chunk]
                }
            ]
        )
        print(f"Created new security group {new_sg_id} and added IPs")

if __name__ == '__main__':
    main()
