import boto3
import os
import pandas as pd

AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')
AWS_SESSION_TOKEN = os.environ.get('AWS_SESSION_TOKEN')  
REGION_NAME = os.environ.get('REGION_NAME')

ec2_client = boto3.client('ec2', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, aws_session_token=AWS_SESSION_TOKEN, region_name=REGION_NAME)

def remove_existing_ips(sg_id):
    """Remove all existing IPs from the specified security group."""
    response = ec2_client.describe_security_groups(GroupIds=[sg_id])
    permissions = response['SecurityGroups'][0]['IpPermissions']

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
        if not sgs['SecurityGroups']:
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
    new_sg_id = response['GroupId']

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

def main():
    vpc_id = 'your_vpc_id'
    
    # Load new IPs from Excel
    df = pd.read_excel('path_to_excel.xlsx')
    new_ips = df['IP Address Range'].tolist() 

    security_group_names = ['akamai-sg-1']  # Start with one SG for testing

    for sg_name in security_group_names:
        sgs = ec2_client.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': [sg_name]}])
        sg_id = sgs['SecurityGroups'][0]['GroupId']

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
                print(f"Created new security group {new_sg_id} for Akamai IPs.")

if __name__ == "__main__":
    main()


# [nan, 'IP Address Range', '104.107.116.14/31', '104.107.61.132/31', '104.112.226.200/30', '104.115.39.0/24', '104.116.241.196/30', '104.116.243.214/31', '104.120.139.0/24', '104.125.80.12/32', '104.64.0.0/10', '104.90.204.144/29', '104.96.169.0/24', '104.96.91.132/31', '104.97.78.0/24', '104.98.3.0/24', '118.214.0.0/16', '124.40.41.200/29', '124.40.42.228/31', '125.252.224.36/31', '125.56.219.52/31', '165.254.1.100/31', '172.224.0.0/12', '173.205.7.116/31', '173.222.0.0/15', '173.222.148.0/24', '184.24.0.0/13', '184.25.56.10/31', '184.27.198.224/31', '184.50.0.0/15', '184.50.228.238/31', '184.50.84.196/32', '184.50.84.198/32', '184.50.85.0/24', '184.84.0.0/14', '184.84.242.21/32', '184.84.242.22/31', '184.84.242.32/30', '192.204.11.4/31', '193.108.155.118/32', '193.108.155.208/32', '2.16.0.0/13', '2.16.157.170/31', '2.18.25.47/32', '2.19.193.116/31', '2.22.10.12/31', '201.33.187.68/30', '201.6.6.214/31', '203.69.138.120/30', '203.69.138.121/32', '203.69.138.122/32', '203.96.118.0/26', '204.1.136.238/31', '204.2.159.68/31', '204.2.160.182/31', '204.2.166.173/32', '204.2.166.174/31', '204.2.166.176/30', '204.2.166.180/32', '204.201.160.246/31', '205.185.205.132/31', '207.126.104.118/31', '208.49.157.49/32', '208.49.157.50/31', '208.49.157.52/31', '208.49.157.54/32', '209.107.208.188/31', '209.170.113.100/31', '209.170.113.106/31', '209.170.113.108/32', '209.170.113.98/31', '209.249.98.36/31', '209.8.112.100/30', '209.8.112.104/31', '209.8.112.96/30', '209.8.118.39/32', '209.8.118.44/32', '220.90.198.178/31', '23.0.0.0/12', '23.192.0.0/11', '23.199.49.0/24', '23.200.75.14/31', '23.200.79.0/24', '23.200.84.166/31', '23.205.121.153/32', '23.210.209.63/32', '23.210.209.66/31', '23.210.209.74/31', '23.211.108.0/24', '23.216.54.0/24', '23.3.104.186/31', '23.3.11.140/32', '23.32.0.0/11', '23.32.5.0/24', '23.35.151.34/31', '23.35.219.28/31', '23.35.219.36/30', '23.40.241.0/24', '23.40.242.0/24', '23.44.172.230/31', '23.44.5.0/24', '23.45.50.0/24', '23.45.51.0/24', '23.48.168.0/22', '23.48.95.0/24', '23.50.48.0/20', '23.52.73.0/24', '23.57.69.52/30', '23.57.74.70/31', '23.58.82.133/32', '23.58.82.196/32', '23.58.82.204/32', '23.58.83.133/32', '23.58.83.196/32', '23.58.83.204/32', '23.61.1.150/31', '23.62.157.0/24', '23.62.2.210/31', '23.62.98.172/31', '23.63.110.0/24', '23.63.234.0/27', '23.63.234.13/32', '23.64.0.0/14', '23.65.182.244/31', '23.67.61.0/24', '23.72.0.0/13', '23.79.242.196/32', '23.79.242.198/32', '2600:14a0::/40', '58.97.45.0/24', '60.254.173.30/31', '61.111.58.82/31', '63.148.207.60/31', '63.151.118.0/24', '63.217.211.110/31', '63.217.211.116/31', '63.235.21.192/31', '63.235.29.198/32', '63.239.233.160/30', '63.239.233.161/32', '63.239.233.162/32', '64.145.89.236/31', '65.120.61.100/31', '65.124.174.194/31', '65.152.116.70/31', '65.158.180.206/31', '66.198.26.68/30', '66.198.26.69/32', '66.198.26.70/32', '66.198.8.141/32', '66.198.8.142/32', '66.198.8.143/32', '66.198.8.144/32', '66.198.8.167/32', '66.198.8.168/32', '67.220.142.19/32', '67.220.142.20/32', '67.220.142.21/32', '67.220.142.22/32', '67.220.143.216/31', '69.192.0.0/16', '69.192.3.135/32', '69.192.3.140/32', '69.31.121.20/31', '69.31.138.100/31', '69.31.59.188/31', '69.31.59.196/32', '69.31.59.202/32', '69.31.59.86/32', '72.246.0.0/15', '72.246.194.165/32', '72.246.52.144/28', '72.246.57.84/31', '72.247.124.172/31', '72.247.237.135/32', '72.247.39.94/32', '77.67.85.52/31', '8.18.43.199/32', '8.18.43.240/32', '80.239.206.148/30', '80.239.206.152/31', '81.20.66.77/32', '88.221.0.0/16', '88.221.213.4/32', '88.221.53.86/31', '90.84.52.180/31', '90.84.52.180/32', '92.122.0.0/15', '92.122.127.108/31', '92.122.191.60/32', '92.122.191.66/32', '92.123.244.140/30', '95.100.0.0/15', '95.100.153.0/24', '95.101.123.0/24', '96.16.0.0/15', '96.17.173.47/32', '96.17.173.71/32', '96.17.180.0/24', '96.6.0.0/15', 'Grand Total']
# Traceback (most recent call last):
#   File "akamai.py", line 111, in <module>
#     main()
#   File "akamai.py", line 107, in main
#     new_sg_id = create_security_group(vpc_id, "akamai-sg", ips_chunk)
#   File "akamai.py", line 64, in create_security_group
#     'IpRanges': [{'CidrIp': ip} for ip in ips]
#   File "/home/ec2-user/.local/lib/python3.7/site-packages/botocore/client.py", line 535, in _api_call
#     return self._make_api_call(operation_name, kwargs)
#   File "/home/ec2-user/.local/lib/python3.7/site-packages/botocore/client.py", line 941, in _make_api_call
#     headers=additional_headers,
#   File "/home/ec2-user/.local/lib/python3.7/site-packages/botocore/client.py", line 1008, in _convert_to_request_dict
#     api_params, operation_model
#   File "/home/ec2-user/.local/lib/python3.7/site-packages/botocore/validate.py", line 381, in serialize_to_request
#     raise ParamValidationError(report=report.generate_report())
# botocore.exceptions.ParamValidationError: Parameter validation failed:
# Invalid type for parameter IpPermissions[0].IpRanges[0].CidrIp, value: nan, type: <class 'float'>, valid types: <class 'str'>
# BCS_PATCH_MGT_2-[ec2-user@ip-10-140-238-37 Akamai]$






# So to summarise our call earlier, the Python looks fine with the following comments:

 

# The Security groups will need to be found via the VPC as Akamai rules are not normally applied to EC2s
# Mondays trial is about updating the existing security groups for Akamai in the SIT account
# From the script point of view for Monday, we should look to specify (as variables within your code), the names of the security groups we want to patch.  Don’t do the VPC lookup Monday unless you need to find the SG ID.
# The script should remove all existing Ips in the groups within the SG’s you code into the script.
# The script should then read the existing reference list (The EMEA and US tabs) and add all addresses to the security groups.
# Assume a maximum of 60 IP’s per SG. 
# You may find you do not have enough SG’s for the complete number of IPs in which case you will need to create new ones to handle the additional addresses.  If the last group is Akamai-5 then start the new group creation with Akamai-6 or similar
# For the first test Monday, lets just add the name of one of the SG’s into your script and then test with that to see how long it takes and that the results are as expected.  If they are Ok, then we will add the other SG names into the script and re-run it.  That will delete the IPs you just added to the first SG and re-do them but that’s Ok as we then need to see what the end to end run is like to add in all the IPs from the sheet.
