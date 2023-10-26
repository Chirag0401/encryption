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

def get_instance_details(session):
    ec2 = session.resource('ec2')
    ec2_client = session.client('ec2')
    cloudwatch = session.client('cloudwatch')

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
            'EFS Mounts': []
        }

        # Security Groups and their rules
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

        # Volumes
        for volume in instance.volumes.all():
            instance_data['Volumes'].append({
                'Volume ID': volume.id,
                'State': volume.state,
                'Type': volume.volume_type,
                'Size': volume.size
            })

        # Target Groups and Load Balancers
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
                    # Get associated load balancers
                    lb_arns = tg['LoadBalancerArns']
                    for lb_arn in lb_arns:
                        lb = elbv2_client.describe_load_balancers(LoadBalancerArns=[lb_arn])['LoadBalancers'][0]
                        instance_data['Load Balancers'].append({
                            'LB Name': lb['LoadBalancerName'],
                            'LB ARN': lb_arn,
                            'Type': lb['Type']
                        })

        # EFS Mounts
        efs_client = session.client('efs')
        file_systems = efs_client.describe_file_systems()['FileSystems']
        for fs in file_systems:
            mount_targets = efs_client.describe_mount_targets(FileSystemId=fs['FileSystemId'])['MountTargets']
            for mt in mount_targets:
                if any(sg['GroupId'] for sg in instance.security_groups if sg['GroupId'] == mt['SecurityGroups'][0]):
                    instance_data['EFS Mounts'].append({
                        'EFS ID': fs['FileSystemId'],
                        'EFS Name': fs['Name'],
                        'Mount Target ID': mt['MountTargetId']
                    })

        # CPU Utilization from CloudWatch
        cpu_stats = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance.id}],
            StartTime=instance.launch_time,
            EndTime=pd.Timestamp.now(tz="UTC"),
            Period=3600,
            Statistics=['Average']
        )
        if cpu_stats['Datapoints']:
            instance_data['Average CPU Utilization'] = cpu_stats['Datapoints'][0]['Average']

        # Memory Utilization (This requires a custom CloudWatch metric, so it might not always be available)
        try:
            memory_stats = cloudwatch.get_metric_statistics(
                Namespace='CustomNamespace',  # Adjust this based on your setup
                MetricName='MemoryUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance.id}],
                StartTime=instance.launch_time,
                EndTime=pd.Timestamp.now(tz="UTC"),
                Period=3600,
                Statistics=['Average']
            )
            if memory_stats['Datapoints']:
                instance_data['Average Memory Utilization'] = memory_stats['Datapoints'][0]['Average']
        except:
            instance_data['Average Memory Utilization'] = "N/A"

        # Placeholder for Cost/Price
        instance_data['Cost/Price'] = "Check AWS Pricing API or Cost Explorer"

        instances_data.append(instance_data)

    return instances_data

def generate_report_with_pandas(data):
    df = pd.DataFrame(data)
    with pd.ExcelWriter('report.xlsx') as writer:
        df.to_excel(writer, sheet_name='Instances', index=False)
    print("Report generated as report.xlsx")

def main():
    session = create_session()
    data = get_instance_details(session)
    generate_report_with_pandas(data)

if __name__ == "__main__":
    main()
