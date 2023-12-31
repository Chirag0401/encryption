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
        instance_data = {
            'Instance ID': instance.id,
            'Instance Type': instance.instance_type,
            'State': instance.state['Name'],
            'Tags': instance.tags,
            'Public IP Address': instance.public_ip_address,
            'Private IP Address': instance.private_ip_address,
            'Key Pair': instance.key_name,
            'Launch Time': instance.launch_time,
            'AMI ID': instance.image_id,
            'Lifecycle': instance.instance_lifecycle,
            'Availability Zone': instance.placement['AvailabilityZone'],
            'IAM Role': instance.iam_instance_profile['Arn'] if instance.iam_instance_profile else None,
            'Network Interfaces': [eni.id for eni in instance.network_interfaces],
            'Security Groups': [],
            'Volumes': [],
            'Target Groups': [],
            'Load Balancers': [],
        }

        for sg in instance.security_groups:
            sg_id = sg['GroupId']
            sg_details = ec2_client.describe_security_groups(GroupIds=[sg_id])['SecurityGroups'][0]
            inbound_rules = sg_details['IpPermissions']
            outbound_rules = sg_details['IpPermissionsEgress']
            instance_data['Security Groups'].append({
                'SG Name': sg_details['GroupName'],
                'SG ID': sg_id,
                'Inbound Rules': inbound_rules,
                'Outbound Rules': outbound_rules
            })

        for volume in instance.volumes.all():
            instance_data['Volumes'].append({
                'Volume ID': volume.id,
                'State': volume.state,
                'Type': volume.volume_type,
                'Size': volume.size
            })

        elbv2_client = session.client('elbv2')
        target_groups = elbv2_client.describe_target_groups()
        for tg in target_groups['TargetGroups']:
            health_descriptions = elbv2_client.describe_target_health(TargetGroupArn=tg['TargetGroupArn'])
            for desc in health_descriptions['TargetHealthDescriptions']:
                if desc['Target']['Id'] == instance.id:
                    instance_data['Target Groups'].append({
                        'Target Group Name': tg['TargetGroupName'],
                        'Target Group ARN': tg['TargetGroupArn']
                    })
                    lb_arns = tg['LoadBalancerArns']
                    for lb_arn in lb_arns:
                        lb = elbv2_client.describe_load_balancers(LoadBalancerArns=[lb_arn])['LoadBalancers'][0]
                        instance_data['Load Balancers'].append({
                            'LB Name': lb['LoadBalancerName'],
                            'LB ARN': lb_arn,
                            'Type': lb['Type']
                        })

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



# Traceback (most recent call last):
#   File "instance_report.py", line 104, in <module>
#     main()
#   File "instance_report.py", line 101, in main
#     generate_report_with_pandas(data, report_filename)
#   File "instance_report.py", line 93, in generate_report_with_pandas
#     df.to_excel(writer, sheet_name='Instances', index=False)
#   File "/home/ec2-user/.local/lib/python3.7/site-packages/pandas/core/generic.py", line 2291, in to_excel
#     storage_options=storage_options,
#   File "/home/ec2-user/.local/lib/python3.7/site-packages/pandas/io/formats/excel.py", line 845, in write
#     freeze_panes=freeze_panes,
#   File "/home/ec2-user/.local/lib/python3.7/site-packages/pandas/io/excel/_openpyxl.py", line 457, in write_cells
#     for cell in cells:
#   File "/home/ec2-user/.local/lib/python3.7/site-packages/pandas/io/formats/excel.py", line 778, in get_formatted_cells
#     cell.val = self._format_value(cell.val)
#   File "/home/ec2-user/.local/lib/python3.7/site-packages/pandas/io/formats/excel.py", line 527, in _format_value
#     "Excel does not support datetimes with "
# ValueError: Excel does not support datetimes with timezones. Please ensure that datetimes are timezone unaware before writing to Excel.
