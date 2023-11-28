import boto3
import pandas as pd

# AWS Configuration
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')
AWS_SESSION_TOKEN = os.environ.get('AWS_SESSION_TOKEN')  
REGION_NAME = os.environ.get('REGION_NAME')

ec2_client = boto3.client('ec2', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, aws_session_token=AWS_SESSION_TOKEN, region_name=REGION_NAME)

def fetch_sg_rules(sg_ids):
    ip_port_pairs = set()
    for sg_id in sg_ids:
        sg_info = ec2_client.describe_security_groups(GroupIds=[sg_id])
        for permission in sg_info['SecurityGroups'][0]['IpPermissions']:
            ip_protocol = permission.get('IpProtocol')
            if ip_protocol == 'tcp' or ip_protocol == 'udp':
                from_port = permission.get('FromPort')
                to_port = permission.get('ToPort')
                for ip_range in permission['IpRanges']:
                    ip_port_pairs.add((ip_range['CidrIp'], from_port, to_port))
    return ip_port_pairs

def write_to_excel(ip_port_pairs, file_name='sg_rules.xlsx'):
    df = pd.DataFrame(list(ip_port_pairs), columns=['IP Address Range', 'From Port', 'To Port'])
    df.to_excel(file_name, index=False)
    print(f"Excel file '{file_name}' has been created.")

def main():
    sg_ids_input = input("Enter the security group IDs, separated by commas: ")
    sg_ids = [sg_id.strip() for sg_id in sg_ids_input.split(',')]

    ip_port_pairs = fetch_sg_rules(sg_ids)
    write_to_excel(ip_port_pairs)

if __name__ == '__main__':
    main()
