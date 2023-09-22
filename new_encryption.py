import boto3
import time
import datetime
import json

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
        volume_id = volume['VolumeId']
        volume_name = None
        instance_id = None
        instance_name = None
        encrypted = volume['Encrypted']
        is_root = False
        device_name = None
        volume_size = volume['Size']
        availability_zone = volume['AvailabilityZone']
        
        if 'Attachments' in volume and len(volume['Attachments']) > 0:
            attachments = volume['Attachments']
            for attachment in attachments:
                instance_id = attachment['InstanceId']
                instance_name = get_instance_name(ec2_client, instance_id)
                if 'Device' in attachment and attachment['Device'] == '/dev/xvda':
                    volume_name = "Root Volume"
                    is_root = True
                    device_name = attachment['Device']
                else:
                    device_name = attachment['Device']
        volume_info.append({
            'Volume ID': volume_id,
            'Volume Name': volume_name,
            'Instance ID': instance_id,
            'Instance Name': instance_name,
            'Encrypted': encrypted,
            'Is Root': is_root,
            'Device Name': device_name,
            'Volume Size': volume_size,
            'Availability Zone': availability_zone
        })
        if 'Tags' in volume:
            for tag in volume['Tags']:
                if tag['Key'] == 'Name':
                    volume_name = tag['Value']
                    break

        if not is_root:
            volume_info.append({
                'Volume ID': volume_id,
                'Volume Name': volume_name,
                'Instance ID': instance_id,
                'Instance Name': instance_name,
                'Encrypted': encrypted,
                'Is Root': is_root,
                'Device Name': device_name,
                'Volume Size': volume_size,
                'Availability Zone': availability_zone
            })
    print(volume_info)
    return volume_info

def get_instance_name(ec2_client, instance_id):
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    instances = response['Reservations'][0]['Instances']

    for instance in instances:
        if 'Tags' in instance:
            for tag in instance['Tags']:
                if tag['Key'] == 'Name':
                    return tag['Value']

    return None

def create_snapshots(volume_info, session):
    ec2_client = session.client("ec2")

    snapshot_details = []
    retention_days = 90

    for volume in volume_info:
        if not volume['Encrypted']:
            volume_id = volume['Volume ID']
            instance_id = volume['Instance ID']
            instance_name = volume['Instance Name']
            root_volume = volume['Device Name']
            disk_size = volume['Volume Size']
            availability_zone = volume['Availability Zone']
            response = ec2_client.create_snapshot(VolumeId=volume_id, Description='Testing snapshot using python script')
            snapshot_id = response['SnapshotId']
            snapshot_name = f"{instance_name}-snapshot" if instance_name else "Unnamed-snapshot"

            # Set retention period
            retention_date = datetime.datetime.now() + datetime.timedelta(days=retention_days)
            ec2_client.create_tags(
                Resources=[snapshot_id],
                Tags=[
                    {'Key': 'RetentionDate', 'Value': retention_date.strftime('%Y-%m-%d')},
                    {'Key': 'Name', 'Value': snapshot_name}
                ]
            )

            snapshot_details.append({
                'Snapshot ID': snapshot_id,
                'Volume ID': volume_id,
                'Instance ID': instance_id,
                'Instance Name': instance_name,
                'Snapshot Name': snapshot_name,
                'Root Volume': root_volume,
                'Disk Size': disk_size,
                'Availability Zone': availability_zone,
                'Description': 'Testing snapshot using python script'
            })

            time.sleep(10)

    with open('snapshot_details.json', 'w') as file:
        json.dump(snapshot_details, file, indent=4)

def create_volumes_from_snapshots(kms_key_arn, session):
    ec2_client = session.client('ec2')
    with open('snapshot_details.json', 'r') as file:
        snapshot_details = json.load(file)

    snapshot_ids = []
    volume_details = []
    for detail in snapshot_details:
        snapshot_id = detail['Snapshot ID']
        snapshot_name = detail['Snapshot Name']
        volume_id = detail['Volume ID']
        instance_id = detail['Instance ID']
        instance_name = detail['Instance Name']
        root_volume = detail['Root Volume']
        disk_size = detail['Disk Size']
        snapshot_ids.append(snapshot_id)
        volume_details.append({
            'snapshot_id': snapshot_id,
            'snapshot_name': snapshot_name,
            'volume_id': volume_id,
            'instance_id': instance_id,
            'instance_name': instance_name,
            'root_volume': root_volume,
            'disk_size': disk_size
        })
        print(volume_details)

    for volume_detail in volume_details:
        snapshot_id = volume_detail['snapshot_id']
        root_volume = volume_detail['root_volume']
        disk_size = volume_detail['disk_size']
        instance_name = volume_detail['instance_name']
        instance_id = volume_detail['instance_id']
        snapshot_state = ec2_client.describe_snapshots(SnapshotIds=[snapshot_id])['Snapshots'][0]['State']
        if snapshot_state != 'completed':
            print(f"Waiting for snapshot {snapshot_id} to become ready")
            while snapshot_state != 'completed':
                time.sleep(10)
                snapshot_state = ec2_client.describe_snapshots(SnapshotIds=[snapshot_id])['Snapshots'][0]['State']
        old_volume_az = ec2_client.describe_volumes(VolumeIds=[volume_detail['volume_id']])['Volumes'][0]['AvailabilityZone']
        response = ec2_client.create_volume(
            SnapshotId=snapshot_id,
            AvailabilityZone=old_volume_az,
            Encrypted=True,
            KmsKeyId=kms_key_arn
        )
        volume_id = response['VolumeId']
        print(f"Created encrypted volume with ID: {volume_id}")
        volume_detail['new_volume_id'] = volume_id
        volume_detail['availability_zone'] = old_volume_az
    output_file = 'volume_details.txt'
    with open(output_file, 'w') as file:
        for volume_detail in volume_details:
            file.write("Snapshot ID: " + volume_detail['snapshot_id'] + ", ")
            file.write("Snapshot Name: " + volume_detail['snapshot_name'] + ", ")
            file.write("Old Volume ID: " + volume_detail['volume_id'] + ", ")
            file.write("New Volume ID: " + volume_detail['new_volume_id'] + ", ")
            file.write("Instance ID: " + volume_detail['instance_id'] + ", ")
            file.write("Instance Name: " + volume_detail['instance_name'] + ", ")
            file.write("Root Volume: " + volume_detail['root_volume'] + ", ")
            file.write("Disk Size: " + str(volume_detail['disk_size']) + ", ")
            file.write("Availability Zone: " + volume_detail['availability_zone'] + "\n")

    print("Output stored in", output_file)

def detach_volumes(session):
    ec2_client = session.client('ec2')
    with open('volume_details.txt', 'r') as volume_file:
        volume_details = volume_file.readlines()
    volume_ids = []
    for detail in volume_details:
        volume_id = detail.split(',')[2].strip().split(': ')[1]
        volume_ids.append(volume_id)
    for volume_id in volume_ids:
        volume_details = ec2_client.describe_volumes(VolumeIds=[volume_id])['Volumes'][0]
        device_name = volume_details['Attachments'][0]['Device']
        instance_id = volume_details['Attachments'][0]['InstanceId']
        
        if device_name == volume_details['Attachments'][0]['Device']:
            # Stop instance if the volume is the root volume
            ec2_client.stop_instances(InstanceIds=[instance_id])
            while True:
                time.sleep(10)
                instance_state = ec2_client.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]['State']['Name']
                if instance_state == 'stopped':
                    break
        
        ec2_client.detach_volume(VolumeId=volume_id)
        while True:
            time.sleep(10)
            volume_state = ec2_client.describe_volumes(VolumeIds=[volume_id])['Volumes'][0]['State']
            if volume_state == 'available':
                break

        print(f"Detached volume {volume_id} from instance {instance_id} with device {device_name}")

def attach_encrypted_volume(session):
    ec2_client = session.client('ec2')
    with open('volume_details.txt', 'r') as volume_file:
        volume_details = volume_file.readlines()
    with open('snapshot_details.txt', 'r') as snapshot_file:
        snapshot_details = snapshot_file.readlines()
    for volume_detail in volume_details:
        volume_detail = volume_detail.strip().split(',')
        
        old_volume_id = volume_detail[2].strip().split(': ')[1]
        new_volume_id = volume_detail[3].strip().split(': ')[1]
        instance_id = volume_detail[4].strip().split(': ')[1]
        old_device_name = volume_detail[6].strip().split(': ')[1]
        root_volume = volume_detail[8].strip().split(': ')[1]  # Access 'Root Volume' value
        
        while True:
            volume_state = ec2_client.describe_volumes(VolumeIds=[new_volume_id])['Volumes'][0]['State']
            if volume_state == 'available':
                break
            else:
                print(f"Waiting for volume {new_volume_id} to become available...")
                time.sleep(30)

        ec2_client.attach_volume(VolumeId=new_volume_id, InstanceId=instance_id, Device=old_device_name)

        if old_device_name == root_volume:  # Compare with the 'root_volume' variable
            # Start instance if the volume is the root volume
            ec2_client.start_instances(InstanceIds=[instance_id])
            while True:
                time.sleep(10)
                instance_state = ec2_client.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]['State']['Name']
                if instance_state == 'running':
                    break

        print(f"Attached encrypted volume {new_volume_id} to instance {instance_id} with device {old_device_name}")

# def get_kms_key_arn():
#     kms_client = boto3.client('kms')
    
#     response = kms_client.list_aliases()
    
#     for alias in response['Aliases']:
#         if alias['AliasName'] == 'alias/aws/ebs':
#             key_id = alias['TargetKeyId']
#             key_response = kms_client.describe_key(KeyId=key_id)
#             key_arn = key_response['KeyMetadata']['Arn']
#             return key_arn
    
#     return None  # Return None if the alias is not found

# # Example usage
# kms_key_arn = get_kms_key_arn()
# if kms_key_arn:
#     print("KMS Key ARN:", kms_key_arn)
# else:
#     print("KMS key alias 'aws/ebs' not found.")

def main():
    region = 'eu-west-1'
    access_key = ''
    secret_access_key = ''
    session_token = ''
    kms_key_arn = 'arn:aws:kms:eu-west-1:198370751513:key/d1d3158d-940a-4e76-b21b-ec5d595723e9'
    session = create_session(region, access_key, secret_access_key, session_token)
    volume_info = get_volume_info(session)
    create_snapshots(volume_info, session)
    create_volumes_from_snapshots(kms_key_arn, session)
    detach_volumes(session)
    attach_encrypted_volume(session)

if __name__ == '__main__':
    main()
