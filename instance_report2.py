import boto3
import os
import pandas as pd

def create_session():
    """Create a boto3 session using environment variables."""
    return boto3.Session(
        region_name=os.environ.get('AWS_DEFAULT_REGION'),
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.environ.get('AWS_SESSION_TOKEN'),
    )

def get_account_number(session):
    """Get the AWS account number using STS client."""
    sts_client = session.client('sts')
    account_id = sts_client.get_caller_identity()["Account"]
    return account_id

def get_instance_details(session):
    ec2 = session.resource('ec2')
    ec2_client = session.client('ec2')

    instances_data = []

    for instance in ec2.instances.all():
        # Extract instance name from tags
        instance_name = None
        if instance.tags:
            for tag in instance.tags:
                if tag['Key'] == 'Name':
                    instance_name = tag['Value']
                    break

        # Format tags for readability
        formatted_tags = '; '.join([f"{tag['Key']}={tag['Value']}" for tag in instance.tags]) if instance.tags else None

        # Formatting for Network Interfaces, Security Groups, Volumes, etc.
        formatted_network_interfaces = '; '.join([eni.id for eni in instance.network_interfaces])
        formatted_security_groups = '; '.join([f"{sg['GroupName']} (ID: {sg['GroupId']})" for sg in instance.security_groups])
        formatted_volumes = '; '.join([f"ID: {vol.id}, State: {vol.state}, Type: {vol.volume_type}, Size: {vol.size}GB" for vol in instance.volumes.all()])

        # Placeholder for formatted Target Groups and Load Balancers
        formatted_target_groups = []
        formatted_load_balancers = []

        elbv2_client = session.client('elbv2')
        target_groups = elbv2_client.describe_target_groups()
        for tg in target_groups['TargetGroups']:
            health_descriptions = elbv2_client.describe_target_health(TargetGroupArn=tg['TargetGroupArn'])
            for desc in health_descriptions['TargetHealthDescriptions']:
                if desc['Target']['Id'] == instance.id:
                    formatted_target_groups.append(f"Name: {tg['TargetGroupName']}, ARN: {tg['TargetGroupArn']}")
                    lb_arns = tg['LoadBalancerArns']
                    for lb_arn in lb_arns:
                        lb = elbv2_client.describe_load_balancers(LoadBalancerArns=[lb_arn])['LoadBalancers'][0]
                        formatted_load_balancers.append(f"Name: {lb['LoadBalancerName']}, ARN: {lb_arn}, Type: {lb['Type']}")

        formatted_target_groups = '; '.join(formatted_target_groups)
        formatted_load_balancers = '; '.join(formatted_load_balancers)

        instance_data = {
            'Instance Name': instance_name,
            'Instance ID': instance.id,
            'Instance Type': instance.instance_type,
            'State': instance.state['Name'],
            'Tags': formatted_tags,
            'Public IP Address': instance.public_ip_address,
            'Private IP Address': instance.private_ip_address,
            'Key Pair': instance.key_name,
            'Launch Time': instance.launch_time,
            'AMI ID': instance.image_id,
            'Lifecycle': instance.instance_lifecycle,
            'Availability Zone': instance.placement['AvailabilityZone'],
            'IAM Role': instance.iam_instance_profile['Arn'] if instance.iam_instance_profile else None,
            'Network Interfaces': formatted_network_interfaces,
            'Security Groups': formatted_security_groups,
            'Volumes': formatted_volumes,
            'Target Groups': formatted_target_groups,
            'Load Balancers': formatted_load_balancers,
        }

        instances_data.append(instance_data)

    return instances_data

def generate_report_with_pandas(data, filename):
    df = pd.DataFrame(data)
    with pd.ExcelWriter(filename) as writer:
        df.to_excel(writer, sheet_name='Instances', index=False)
    print(f"Report generated as {filename}")

def main():
    session = create_session()
    account_number = get_account_number(session)
    data = get_instance_details(session)
    report_filename = f'report_{account_number}.xlsx'
    generate_report_with_pandas(data, report_filename)

if __name__ == "__main__":
    main()
