EBS Encryption Automation Script
This script provides an automated way to encrypt unencrypted Amazon Elastic Block Store (EBS) volumes attached to Amazon EC2 instances.

Overview
EBS volumes that are in use and not encrypted are identified, snapshots are taken of these volumes, encrypted volumes are created from the snapshots, and then these encrypted volumes are reattached to the original instances in place of the unencrypted volumes.

Initialization:

Set up logging.
Define the maximum number of retries (MAX_RETRIES).
Read the excluded instance IDs from a CSV file into the EXCLUDED_INSTANCES list.
Function Definitions:

create_session():
Creates and returns a new boto3 session using AWS credentials from the environment variables.
read_excluded_instances_from_csv(file_path):
Reads instance IDs from a given CSV file and returns them as a list.
robust_waiter(waiter, **kwargs):
A wrapper around boto3's waiter to add retry logic and error handling.
get_instance_name(session, instance_id):
Returns the name of an EC2 instance given its ID.
get_kms_key_arn(session, alias_name='alias/aws/ebs'):
Retrieves the ARN of a KMS key based on its alias.
get_volume_info(session):
Returns information about all the EBS volumes.
create_snapshot(session, volume_id):
Creates a snapshot of a given volume and waits for its completion.
create_encrypted_volume(session, snapshot_id, availability_zone, size, volume_type, kms_key):
Creates an encrypted EBS volume from a given snapshot.
attach_encrypted_volume(session, encrypted_volume_id, instance_id, device_name):
Attaches an encrypted volume to an EC2 instance.
detach_volume(session, volume_id):
Detaches an EBS volume from its attached instance.
stop_instance(session, instance_id):
Stops an EC2 instance.
start_instance(session, instance_id):
Starts an EC2 instance.
log_volume_details(details):
Logs details about volume changes to a CSV file.
process_volumes_for_instance(session, volumes, kms_key):
For a given EC2 instance, this function stops the instance, creates encrypted volumes from its attached volumes, and then starts the instance.
process_pending_snapshots(session):
Processes any snapshots that are still pending.
Main Execution (main() function):

Log headers to a CSV file.
Create a boto3 session.
Get the KMS key ARN.
Retrieve information about all EBS volumes.
Organize volumes by their availability zones and attached instances.
For each availability zone and each instance in that zone, if the instance is not in the EXCLUDED_INSTANCES list, process its volumes.
If there are any pending snapshots, process them.
Log the total execution time.
Script Execution:

If the script is run as the main module, the main() function is called.
The flow of the script is essentially about identifying unencrypted EBS volumes attached to EC2 instances, creating encrypted snapshots of those volumes, and then creating encrypted volumes from those snapshots. The original volumes are then replaced with the new encrypted volumes. The script also handles instances that are specified to be excluded from this process.

Working
A session with AWS is created.
Retrieve the ARN of the KMS key that will be used for encryption.
Describe all EBS volumes and filter those that are in use and not encrypted.
Organize the volumes by availability zone and instance.
For each instance in each availability zone, stop the instance, create snapshots of its unencrypted volumes, create encrypted volumes from those snapshots, detach the original volumes, attach the encrypted volumes, and then start the instance.
If any snapshots take longer than expected to complete, their processing is retried a few times. If they still don't complete, they are logged as failures.
All volume change details are written to a CSV file for reference.


Output

2023-10-10 11:00:00,000 - INFO - Processing volumes in availability zone: eu-west-1a
2023-10-10 11:15:00,000 - INFO - Instance i-0abcd1234efgh5678 stopped in 0:10:00
...
2023-10-10 12:00:00,000 - ERROR - Snapshot creation for volume vol-0abcd1234efgh5678 took too long. Adding to pending snapshots list.
...
2023-10-10 12:15:00,000 - INFO - Instance i-0abcd1234efgh5678 started in 0:10:00
...
2023-10-10 12:30:00,000 - INFO - Processing pending snapshots...
2023-10-10 12:45:00,000 - ERROR - Failed to process some snapshots even after 5 retries.
2023-10-10 12:45:01,000 - ERROR - Failed snapshot details: {'volume_id': 'vol-0abcd1234efgh5678', ...}
...
2023-10-10 13:00:00,000 - INFO - Script completed in 2:00:00
