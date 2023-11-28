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
    try:
        return ipaddress.ip_address(ip.split('/')[0]).version == 4
    except ValueError:
        return False

def load_ips_and_ports_from_excel(sheet_name):
    df = pd.read_excel('path_to_excel.xlsx', sheet_name=sheet_name)
    ip_port_pairs = [(row['IP Address Range'], row['Port']) for index, row in df.iterrows() if is_ipv4(row['IP Address Range'])]
    return ip_port_pairs

def create_security_group(vpc_id, sg_name):
    response = ec2_client.create_security_group(
        GroupName=sg_name,
        Description=f"Security group for {sg_name}",
        VpcId=vpc_id
    )
    new_sg_id = response.get('GroupId')

    if not new_sg_id:
        raise ValueError("Failed to create a new security group")

    print(f"Created new security group {new_sg_id} with name {sg_name}.")
    return new_sg_id

def rule_exists(sg_rules, ip, port, ip_protocol='tcp'):
    for rule in sg_rules:
        if (rule.get('FromPort') <= port <= rule.get('ToPort') and
            rule.get('IpProtocol') == ip_protocol):
            for ip_range in rule.get('IpRanges', []):
                if ip_range.get('CidrIp') == ip:
                    return True
    return False

def add_ips_to_sg(sg_id, ip_port_pairs):
    sg_info = ec2_client.describe_security_groups(GroupIds=[sg_id])
    existing_rules = sg_info['SecurityGroups'][0]['IpPermissions']

    for ip, port in ip_port_pairs:
        if not rule_exists(existing_rules, ip, port):
            try:
                ec2_client.authorize_security_group_ingress(
                    GroupId=sg_id,
                    IpPermissions=[
                        {
                            'IpProtocol': 'tcp',
                            'FromPort': port,
                            'ToPort': port,
                            'IpRanges': [{'CidrIp': ip}]
                        }
                    ]
                )
                print(f"Added IP {ip} with port {port} to the security group {sg_id}.")
            except Exception as e:
                print(f"An error occurred while adding IP {ip} with port {port}: {e}")

def main():
    sheet_name = input('Enter the name of the sheet you want to use: ')
    ip_port_pairs = load_ips_and_ports_from_excel(sheet_name)

    sg_ids_input = input('Enter the security group IDs, separated by commas (leave blank to create a new one): ')
    if sg_ids_input.strip():
        sg_ids = [sg_id.strip() for sg_id in sg_ids_input.split(',')]
        for sg_id in sg_ids:
            add_ips_to_sg(sg_id, ip_port_pairs)
    else:
        vpc_id = input('Enter your VPC ID for the new security group: ')
        new_sg_name = input('Enter the name of the new security group: ')
        new_sg_id = create_security_group(vpc_id, new_sg_name)
        add_ips_to_sg(new_sg_id, ip_port_pairs)

if __name__ == '__main__':
    main()
