import boto3
import time
import json
from datetime import datetime

def create_session(region, access_key, secret_access_key, session_token):
    session = boto3.Session(
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_access_key,
        aws_session_token=session_token,
    )
    return session

def get_volume_info(session):
    ec2_client = session.client("ec2")
    response = ec2_client.describe_volumes()
    volumes = response['Volumes']
    volume_info = []
    
    for volume in volumes:
        volume_info.append(volume)
    
    print(json.dumps(volume_info, indent=4, default=str))  # Use str() to serialize datetime objects
    return volume_info

def create_snapshot(session, volume_id):
    ec2_client = session.client("ec2")
    try:
        response = ec2_client.create_snapshot(VolumeId=volume_id)
        snapshot_id = response['SnapshotId']
        waiter = ec2_client.get_waiter('snapshot_completed')
        waiter.wait(SnapshotIds=[snapshot_id])
        return snapshot_id
    except Exception as e:
        print(f"Error creating snapshot for volume {volume_id}: {e}")
        return None

def create_encrypted_volume(session, snapshot_id, availability_zone, size, kms_key):
    ec2_client = session.client("ec2")
    try:
        response = ec2_client.create_volume(
            SnapshotId=snapshot_id,
            AvailabilityZone=availability_zone,
            Size=size,
            Encrypted=True,
            KmsKeyId=kms_key,
        )
        volume_id = response['VolumeId']
        waiter = ec2_client.get_waiter('volume_available')
        waiter.wait(VolumeIds=[volume_id])
        return volume_id
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
        waiter = ec2_client.get_waiter('volume_in_use')
        waiter.wait(VolumeIds=[encrypted_volume_id])
    except Exception as e:
        print(f"Error attaching encrypted volume {encrypted_volume_id} to instance {instance_id}: {e}")

def detach_volume(session, volume_id):
    ec2_client = session.client("ec2")
    try:
        ec2_client.detach_volume(VolumeId=volume_id)
        waiter = ec2_client.get_waiter('volume_available')
        waiter.wait(VolumeIds=[volume_id])
    except Exception as e:
        print(f"Error detaching volume {volume_id}: {e}")

def delete_volume(session, volume_id):
    ec2_client = session.client("ec2")
    try:
        ec2_client.delete_volume(VolumeId=volume_id)
    except Exception as e:
        print(f"Error deleting volume {volume_id}: {e}")

def main():
    region = "eu-west-1"
    access_key = ""
    secret_access_key = ""
    session_token = ""
    kms_key = "arn:aws:kms:eu-west-1:198370751513:key/d1d3158d-940a-4e76-b21b-ec5d595723e9"  # Replace with your KMS key ID
    
    session = create_session(region, access_key, secret_access_key, session_token)
    volume_info = get_volume_info(session)
    
    for volume in volume_info:
        volume_id = volume['VolumeId']
        if volume['State'] != 'in-use':
            print(f"Volume {volume_id} is not in use. Skipping...")
            continue
        
        if volume['Encrypted']:
            print(f"Volume {volume_id} is already encrypted. Skipping...")
            continue
        
        print(f"Processing volume {volume_id}")
        snapshot_id = create_snapshot(session, volume_id)
        if not snapshot_id:
            continue
        
        encrypted_volume_id = create_encrypted_volume(session, snapshot_id, volume['AvailabilityZone'], volume['Size'], kms_key)
        if not encrypted_volume_id:
            continue
        
        instance_id = volume['Attachments'][0]['InstanceId']
        device_name = volume['Attachments'][0]['Device']
        
        detach_volume(session, volume_id)
        attach_encrypted_volume(session, encrypted_volume_id, instance_id, device_name)
        
        confirm_delete = input(f"Do you really want to delete the original volume {volume_id}? (yes/no): ")
        if confirm_delete.lower() == 'yes':
            delete_volume(session, volume_id)
        else:
            print("Skipping deletion of original volume.")

if __name__ == '__main__':
    main()
