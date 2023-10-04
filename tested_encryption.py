import boto3
import os
import time
import json
from datetime import datetime

def create_session():
    return boto3.Session(
        region_name=os.environ.get('AWS_DEFAULT_REGION'),
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.environ.get('AWS_SESSION_TOKEN'),
    )

def get_instance_name(session, instance_id):
    ec2_client = session.client("ec2")
    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        for tag in response['Reservations'][0]['Instances'][0].get('Tags', []):
            if tag['Key'] == 'Name':
                return tag['Value']
        return None
    except Exception as e:
        print(f"Error retrieving instance name: {e}")
        return None

def get_kms_key_arn(session, alias_name='alias/aws/ebs'):
    kms_client = session.client('kms')
    try:
        response = kms_client.describe_key(KeyId=alias_name)
        return response['KeyMetadata']['Arn']
    except Exception as e:
        print(f"Error retrieving KMS key with alias {alias_name}: {e}")
        return None

def get_volume_info(session):
    ec2_client = session.client("ec2")
    try:
        response = ec2_client.describe_volumes()
        return response['Volumes']
    except Exception as e:
        print(f"Error retrieving volume information: {e}")
        return []

def create_snapshot(session, volume_id):
    ec2_client = session.client("ec2")
    try:
        response = ec2_client.create_snapshot(VolumeId=volume_id)
        return response['SnapshotId']
    except Exception as e:
        print(f"Error creating snapshot for volume {volume_id}: {e}")
        return None

def create_encrypted_volume(session, snapshot_id, availability_zone, size, volume_type, kms_key):
    ec2_client = session.client("ec2")
    try:
        response = ec2_client.create_volume(
            SnapshotId=snapshot_id,
            AvailabilityZone=availability_zone,
            Size=size,
            VolumeType=volume_type,
            Encrypted=True,
            KmsKeyId=kms_key,
        )
        return response['VolumeId']
    except Exception as e:
        print(f"Error creating encrypted volume from snapshot {snapshot_id}: {e}")
        return None

def attach_encrypted_volume(session, encrypted_volume_id, instance_id, device_name):
    ec2_client = session.client("ec2")
    try:
        ec2_client.attach_volume(
            VolumeId=encrypted_volume_id,
            InstanceId=instance_id,
            Device=device_name
        )
    except Exception as e:
        print(f"Error attaching encrypted volume {encrypted_volume_id} to instance {instance_id}: {e}")

def detach_volume(session, volume_id):
    ec2_client = session.client("ec2")
    try:
        ec2_client.detach_volume(VolumeId=volume_id)
    except Exception as e:
        print(f"Error detaching volume {volume_id}: {e}")

def stop_instance(session, instance_id):
    ec2_client = session.client("ec2")
    try:
        ec2_client.stop_instances(InstanceIds=[instance_id])
        waiter = ec2_client.get_waiter('instance_stopped')
        waiter.wait(InstanceIds=[instance_id])
    except Exception as e:
        print(f"Error stopping instance {instance_id}: {e}")

def start_instance(session, instance_id):
    ec2_client = session.client("ec2")
    try:
        ec2_client.start_instances(InstanceIds=[instance_id])
        waiter = ec2_client.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
    except Exception as e:
        print(f"Error starting instance {instance_id}: {e}")

def log_volume_details(details):
    # Using a timestamp to make a unique log filename for each run
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    with open(f'volume_changes_{timestamp}.log', 'a') as file:
        file.write(json.dumps(details) + '\n')

def main():
    session = create_session()
    kms_key = get_kms_key_arn(session)
    if not kms_key:
        print("Error: Could not retrieve the KMS key ARN. Exiting.")
        return

    volume_info = get_volume_info(session)
    for volume in volume_info:
        volume_id = volume['VolumeId']

        if volume['State'] != 'in-use':
            print(f"Volume {volume_id} is not in use. Skipping...")
            continue

        if volume['Encrypted']:
            print(f"Volume {volume_id} is already encrypted. Skipping...")
            continue

        instance_id = volume['Attachments'][0]['InstanceId']
        stop_instance(session, instance_id)

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

        start_instance(session, instance_id)
        print(f"Volume {volume_id} processed and replaced with encrypted volume {encrypted_volume_id}")

if __name__ == '__main__':
    main()
