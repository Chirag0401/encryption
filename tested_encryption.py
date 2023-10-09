import boto3
import os
import json
from datetime import datetime
from collections import defaultdict
import botocore
import logging
from prettytable import PrettyTable

# Global list to store volume details for the current script run
VOLUME_DETAILS_LIST = []

# Setup logging
logging.basicConfig(filename='script_logs.log', level=logging.INFO)
logger = logging.getLogger()

def create_session():
    return boto3.Session(
        region_name=os.environ.get('AWS_DEFAULT_REGION'),
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.environ.get('AWS_SESSION_TOKEN'),
    )

def robust_waiter(waiter, **kwargs):
    try:
        waiter.wait(
            **kwargs,
            WaiterConfig={
                'Delay': 120,  # time in seconds between each check
                'MaxAttempts': 60  # maximum number of checks
            }
        )
    except botocore.exceptions.WaiterError:
        logger.error(f"Waiter {waiter.name} failed for parameters: {kwargs}.")

def get_instance_name(session, instance_id):
    ec2_client = session.client("ec2")
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    for tag in response['Reservations'][0]['Instances'][0].get('Tags', []):
        if tag['Key'] == 'Name':
            return tag['Value']
    return None

def get_kms_key_arn(session, alias_name='alias/aws/ebs'):
    kms_client = session.client('kms')
    try:
        response = kms_client.describe_key(KeyId=alias_name)
        return response['KeyMetadata']['Arn']
    except kms_client.exceptions.NotFoundException:
        logger.error(f"KMS key with alias {alias_name} not found.")
        return None

def get_volume_info(session):
    ec2_client = session.client("ec2")
    response = ec2_client.describe_volumes()
    return response['Volumes']

def create_snapshot(session, volume_id):
    ec2_client = session.client("ec2")
    response = ec2_client.create_snapshot(VolumeId=volume_id)
    snapshot_id = response['SnapshotId']

    waiter = ec2_client.get_waiter('snapshot_completed')
    robust_waiter(waiter, SnapshotIds=[snapshot_id])

    return snapshot_id

def create_encrypted_volume(session, snapshot_id, availability_zone, size, volume_type, kms_key):
    ec2_client = session.client("ec2")
    response = ec2_client.create_volume(
        SnapshotId=snapshot_id,
        AvailabilityZone=availability_zone,
        Size=size,
        VolumeType=volume_type,
        Encrypted=True,
        KmsKeyId=kms_key,
    )
    volume_id = response['VolumeId']

    waiter = ec2_client.get_waiter('volume_available')
    robust_waiter(waiter, VolumeIds=[volume_id])

    return volume_id

def attach_encrypted_volume(session, encrypted_volume_id, instance_id, device_name):
    ec2_client = session.client("ec2")
    ec2_client.attach_volume(
        VolumeId=encrypted_volume_id,
        InstanceId=instance_id,
        Device=device_name
    )

def detach_volume(session, volume_id):
    ec2_client = session.client("ec2")
    ec2_client.detach_volume(VolumeId=volume_id)

    waiter = ec2_client.get_waiter('volume_available')
    robust_waiter(waiter, VolumeIds=[volume_id])

def stop_instance(session, instance_id):
    ec2_client = session.client("ec2")
    ec2_client.stop_instances(InstanceIds=[instance_id])

    waiter = ec2_client.get_waiter('instance_stopped')
    robust_waiter(waiter, InstanceIds=[instance_id])

def start_instance(session, instance_id):
    ec2_client = session.client("ec2")
    ec2_client.start_instances(InstanceIds=[instance_id])

    waiter = ec2_client.get_waiter('instance_running')
    robust_waiter(waiter, InstanceIds=[instance_id])

def log_volume_details(details):
    VOLUME_DETAILS_LIST.append(details)

def write_volume_details_to_file():
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f'volume_changes_{current_time}.csv'
    headers = ["old_volume_id", "new_volume_id", "instance_id", "instance_name", "device_name", "disk_size", "snapshot_id", "availability_zone"]
    
    table = PrettyTable(field_names=headers)
    for detail in VOLUME_DETAILS_LIST:
        table.add_row([detail[h] for h in headers])

    with open(filename, 'w') as file:
        file.write(table.get_string())

def process_volumes_for_instance(session, volumes, kms_key):
    instance_id = volumes[0]['Attachments'][0]['InstanceId']
    stop_instance(session, instance_id)

    for volume in volumes:
        volume_id = volume['VolumeId']
        snapshot_id = create_snapshot(session, volume_id)
        
        encrypted_volume_id = create_encrypted_volume(session, snapshot_id, volume['AvailabilityZone'], volume['Size'], volume['VolumeType'], kms_key)
        detach_volume(session, volume_id)

        attach_encrypted_volume(session, encrypted_volume_id, instance_id, volume['Attachments'][0]['Device'])

        instance_name = get_instance_name(session, instance_id)
        details = {
            'old_volume_id': volume_id,
            'new_volume_id': encrypted_volume_id,
            'instance_id': instance_id,
            'instance_name': instance_name,
            'device_name': volume['Attachments'][0]['Device'],
            'disk_size': volume['Size'],
            'snapshot_id': snapshot_id,
            'availability_zone': volume['AvailabilityZone']
        }
        log_volume_details(details)

    start_instance(session, instance_id)

def main():
    start_time = datetime.now()

    session = create_session()
    kms_key = get_kms_key_arn(session)
    if not kms_key:
        logger.error("Error: Could not retrieve the KMS key ARN. Exiting.")
        return

    volume_info = get_volume_info(session)
    instance_to_volumes_map = defaultdict(list)
    for volume in volume_info:
        if volume['State'] == 'in-use' and not volume['Encrypted']:
            instance_id = volume['Attachments'][0]['InstanceId']
            instance_to_volumes_map[instance_id].append(volume)

    for instance_id, volumes in instance_to_volumes_map.items():
        process_volumes_for_instance(session, volumes, kms_key)

    write_volume_details_to_file()

    elapsed_time = datetime.now() - start_time
    logger.info(f"Script completed in {elapsed_time}")

if __name__ == '__main__':
    main()
