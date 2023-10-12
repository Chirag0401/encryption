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


# So to summarise our call earlier, the Python looks fine with the following comments:

 

# The Security groups will need to be found via the VPC as Akamai rules are not normally applied to EC2s
# Mondays trial is about updating the existing security groups for Akamai in the SIT account
# From the script point of view for Monday, we should look to specify (as variables within your code), the names of the security groups we want to patch.  Don’t do the VPC lookup Monday unless you need to find the SG ID.
# The script should remove all existing Ips in the groups within the SG’s you code into the script.
# The script should then read the existing reference list (The EMEA and US tabs) and add all addresses to the security groups.
# Assume a maximum of 60 IP’s per SG. 
# You may find you do not have enough SG’s for the complete number of IPs in which case you will need to create new ones to handle the additional addresses.  If the last group is Akamai-5 then start the new group creation with Akamai-6 or similar
# For the first test Monday, lets just add the name of one of the SG’s into your script and then test with that to see how long it takes and that the results are as expected.  If they are Ok, then we will add the other SG names into the script and re-run it.  That will delete the IPs you just added to the first SG and re-do them but that’s Ok as we then need to see what the end to end run is like to add in all the IPs from the sheet.
