import boto3
import os

# AWS Configuration
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')
AWS_SESSION_TOKEN = os.environ.get('AWS_SESSION_TOKEN')  
REGION_NAME = os.environ.get('REGION_NAME')

ec2_client = boto3.client('ec2', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, aws_session_token=AWS_SESSION_TOKEN, region_name=REGION_NAME)

def get_security_group_rules(sg_ids):
    rules = []
    for sg_id in sg_ids:
        sg_info = ec2_client.describe_security_groups(GroupIds=[sg_id])
        for permission in sg_info['SecurityGroups'][0]['IpPermissions']:
            if not any(permission == existing_rule for existing_rule in rules):
                rules.append(permission)
    return rules

def create_security_group(vpc_id, sg_name):
    response = ec2_client.create_security_group(
        GroupName=sg_name,
        Description=f"Combined security group {sg_name}",
        VpcId=vpc_id
    )
    return response.get('GroupId')

def check_duplicate_rules(existing_rules, new_rule):
    return any(new_rule == rule for rule in existing_rules)

def add_rules_to_security_group(sg_id, rules):
    sg_info = ec2_client.describe_security_groups(GroupIds=[sg_id])
    existing_rules = sg_info['SecurityGroups'][0]['IpPermissions']

    rules_to_add = [rule for rule in rules if not check_duplicate_rules(existing_rules, rule)]

    for rule in rules_to_add:
        try:
            ec2_client.authorize_security_group_ingress(GroupId=sg_id, IpPermissions=[rule])
            print(f"Rule added to {sg_id}.")
        except ec2_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
                print(f"Duplicate rule, skipped: {rule}")
            else:
                print(f"Failed to add rule to {sg_id}: {e}")


def user_confirmation(prompt):
    return input(prompt).lower() in ['yes', 'y']

def main():
    sg_ids = input("Enter the security group IDs to combine, separated by commas: ").split(',')
    combined_rules = get_security_group_rules(sg_ids)

    if len(combined_rules) > 195 and user_confirmation("Rule count exceeds 195. Create a new security group? (yes/no): "):
        vpc_id = input("Enter your VPC ID: ")
        sg_name = input("Enter the name for the new security group: ")
        new_sg_id = create_security_group(vpc_id, sg_name)
        add_rules_to_security_group(new_sg_id, combined_rules[:195])
    else:
        existing_sg_id = input("Enter the existing security group ID to add the rules: ")
        add_rules_to_security_group(existing_sg_id, combined_rules[:195])

if __name__ == '__main__':
    main()


# [ec2-user@ip-10-140-241-119 sg-combine]$ python3 sg-combine.py
# Enter the security group IDs to combine, separated by commas: sg-00d655c03893e4563,sg-0cc133920bb6d45cb
# Enter the existing security group ID to add the rules: sg-0b70ab9c598da470c
# Rule added to sg-0b70ab9c598da470c.
# Failed to add rule to sg-0b70ab9c598da470c: An error occurred (InvalidPermission.Duplicate) when calling the AuthorizeSecurityGroupIngress operation: the specified rule "peer: 104.115.39.0/24, TCP, from port: 443, to port: 443, ALLOW" already exists

