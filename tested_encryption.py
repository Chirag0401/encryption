import boto3
import json

def create_session():
    return boto3.Session(
        region_name="eu-west-1",
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.environ.get('AWS_SESSION_TOKEN'),
    )

def get_volume_info(session):
    ec2_client = session.client("ec2")
    response = ec2_client.describe_volumes()
    return response['Volumes']

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

def stop_instance(session, instance_id):
    ec2_client = session.client("ec2")
    ec2_client.stop_instances(InstanceIds=[instance_id])
    waiter = ec2_client.get_waiter('instance_stopped')
    waiter.wait(InstanceIds=[instance_id])

def start_instance(session, instance_id):
    ec2_client = session.client("ec2")
    ec2_client.start_instances(InstanceIds=[instance_id])
    waiter = ec2_client.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])

def main():
    kms_key = "arn:aws:kms:eu-west-1:198370751513:key/d1d3158d-940a-4e76-b21b-ec5d595723e9"

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

        encrypted_volume_id = create_encrypted_volume(session, snapshot_id, volume['AvailabilityZone'], volume['Size'], volume['VolumeType'], kms_key)
        if not encrypted_volume_id:
            continue

        instance_id = volume['Attachments'][0]['InstanceId']
        device_name = volume['Attachments'][0]['Device']

        if device_name == '/dev/xvda':  # Check if the volume is the root volume
            stop_instance(session, instance_id)

        detach_volume(session, volume_id)
        attach_encrypted_volume(session, encrypted_volume_id, instance_id, device_name)

        if device_name == '/dev/xvda':  # Check if the volume was the root volume
            start_instance(session, instance_id)

        confirm_delete = input(f"Do you really want to delete the original volume {volume_id}? (yes/no): ")
        if confirm_delete.lower() == 'yes':
            delete_volume(session, volume_id)
        else:
            print("Skipping deletion of original volume.")

if __name__ == '__main__':
    main()
