import boto3
import os
import time
import json
from datetime import datetime
from collections import defaultdict

def create_session():
    return boto3.Session(
        region_name=os.environ.get('AWS_DEFAULT_REGION'),
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.environ.get('AWS_SESSION_TOKEN'),
    )

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
        print(f"KMS key with alias {alias_name} not found.")
        return None

def get_volume_info(session):
    ec2_client = session.client("ec2")
    response = ec2_client.describe_volumes()
    return response['Volumes']

def create_snapshot(session, volume_id):
    ec2_client = session.client("ec2")
    response = ec2_client.create_snapshot(VolumeId=volume_id)
    return response['SnapshotId']

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
    return response['VolumeId']

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

def stop_instance(session, instance_id):
    ec2_client = session.client("ec2")
    print(f"Stopping instance {instance_id}...")
    ec2_client.stop_instances(InstanceIds=[instance_id])
    waiter = ec2_client.get_waiter('instance_stopped')
    waiter.wait(InstanceIds=[instance_id])
    print(f"Instance {instance_id} stopped.")

def start_instance(session, instance_id):
    ec2_client = session.client("ec2")
    print(f"Starting instance {instance_id}...")
    ec2_client.start_instances(InstanceIds=[instance_id])
    waiter = ec2_client.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])
    print(f"Instance {instance_id} started.")

def log_volume_details(details):
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    with open(f'volume_changes_{current_time}.log', 'a') as file:
        file.write(json.dumps(details) + '\n')

def process_volumes_for_instance(session, volumes, kms_key):
    instance_id = volumes[0]['Attachments'][0]['InstanceId']
    print(f"Processing volumes for instance {instance_id}")
    stop_instance(session, instance_id)

    for volume in volumes:
        volume_id = volume['VolumeId']
        print(f"Processing volume {volume_id}")
        snapshot_id = create_snapshot(session, volume_id)
        time.sleep(10)
        
        encrypted_volume_id = create_encrypted_volume(session, snapshot_id, volume['AvailabilityZone'], volume['Size'], volume['VolumeType'], kms_key)
        detach_volume(session, volume_id)
        time.sleep(10)

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
        print(f"Volume {volume_id} processed and replaced with encrypted volume {encrypted_volume_id}")

    start_instance(session, instance_id)

def main():
    session = create_session()
    kms_key = get_kms_key_arn(session)
    if not kms_key:
        print("Error: Could not retrieve the KMS key ARN. Exiting.")
        return

    volume_info = get_volume_info(session)
    instance_to_volumes_map = defaultdict(list)
    for volume in volume_info:
        if volume['State'] == 'in-use' and not volume['Encrypted']:
            instance_id = volume['Attachments'][0]['InstanceId']
            instance_to_volumes_map[instance_id].append(volume)

    for instance_id, volumes in instance_to_volumes_map.items():
        process_volumes_for_instance(session, volumes, kms_key)

if __name__ == '__main__':
    main()
