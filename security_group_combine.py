import boto3
import os

# AWS Configuration
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')
AWS_SESSION_TOKEN = os.environ.get('AWS_SESSION_TOKEN')  
REGION_NAME = os.environ.get('REGION_NAME')

ec2_client = boto3.client('ec2', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, aws_session_token=AWS_SESSION_TOKEN, region_name=REGION_NAME)

def get_security_group_rules(sg_ids):
    """Retrieve unique rules from the provided security groups."""
    rules = []
    for sg_id in sg_ids:
        sg_info = ec2_client.describe_security_groups(GroupIds=[sg_id])
        for permission in sg_info['SecurityGroups'][0]['IpPermissions']:
            if permission not in rules:
                rules.append(permission)
    return rules

def create_security_group(vpc_id, sg_name):
    """Create a new security group."""
    response = ec2_client.create_security_group(
        GroupName=sg_name,
        Description=f"Combined security group {sg_name}",
        VpcId=vpc_id
    )
    return response.get('GroupId')

def check_duplicate_rules(existing_rules, new_rule):
    """Check if a rule already exists in the security group."""
    for rule in existing_rules:
        if rule['IpProtocol'] == new_rule['IpProtocol'] and \
           rule['FromPort'] == new_rule['FromPort'] and \
           rule['ToPort'] == new_rule['ToPort'] and \
           rule['IpRanges'] == new_rule['IpRanges']:
            return True
    return False

def add_rules_to_security_group(sg_id, rules):
    """Add rules to a security group, skipping duplicates."""
    sg_info = ec2_client.describe_security_groups(GroupIds=[sg_id])
    existing_rules = sg_info['SecurityGroups'][0]['IpPermissions']

    rules_to_add = [rule for rule in rules if not check_duplicate_rules(existing_rules, rule)]
    added_rule_count = 0

    for rule in rules_to_add:
        try:
            ec2_client.authorize_security_group_ingress(GroupId=sg_id, IpPermissions=[rule])
            added_rule_count += 1
        except ec2_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
                print(f"Duplicate rule skipped: {rule}")
            else:
                print(f"Failed to add rule to {sg_id}: {e}")

    print(f"Total number of rules added to {sg_id}: {added_rule_count}")

def handle_user_choice(combined_rules):
    """Handle user choice when rule count exceeds 195."""
    user_choice = input("Rule count exceeds 195. Would you like to create a new security group or use an existing one? (new/existing): ").lower()
    
    if user_choice == 'new':
        vpc_id = input("Enter your VPC ID: ")
        sg_name = input("Enter the name for the new security group: ")
        new_sg_id = create_security_group(vpc_id, sg_name)
        add_rules_to_security_group(new_sg_id, combined_rules[:195])
    elif user_choice == 'existing':
        existing_sg_id = input("Enter the existing security group ID: ")
        add_rules_to_security_group(existing_sg_id, combined_rules[:195])
    else:
        print("Invalid input. Exiting the script.")

def main():
    """Main function to execute the script."""
    sg_ids = input("Enter the security group IDs to combine, separated by commas: ").split(',')
    combined_rules = get_security_group_rules(sg_ids)

    if len(combined_rules) > 195:
        handle_user_choice(combined_rules)
    else:
        existing_sg_id = input("Enter the existing security group ID to add the rules: ")
        add_rules_to_security_group(existing_sg_id, combined_rules)

if __name__ == '__main__':
    main()
