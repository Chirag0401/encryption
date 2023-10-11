EBS Encryption Automation Script
This script provides an automated way to encrypt unencrypted Amazon Elastic Block Store (EBS) volumes attached to Amazon EC2 instances.

Overview
EBS volumes that are in use and not encrypted are identified, snapshots are taken of these volumes, encrypted volumes are created from the snapshots, and then these encrypted volumes are reattached to the original instances in place of the unencrypted volumes.

Functions
1. create_session()
Establishes an AWS session using credentials from environment variables.

2. robust_waiter(waiter, **kwargs)
Waits for a particular AWS resource to reach a specific state. If the resource doesn't reach the desired state within the specified wait time, an error is logged.

3. get_instance_name(session, instance_id)
Retrieves the name of an EC2 instance using its instance ID.

4. get_kms_key_arn(session, alias_name='alias/aws/ebs')
Fetches the ARN of a KMS key using its alias.

5. get_volume_info(session)
Returns information about all EBS volumes in the region.

6. create_snapshot(session, volume_id)
Creates a snapshot for a given EBS volume and waits for the snapshot to be completed.

7. create_encrypted_volume(session, snapshot_id, availability_zone, size, volume_type, kms_key)
Creates an encrypted EBS volume from a given snapshot.

8. attach_encrypted_volume(session, encrypted_volume_id, instance_id, device_name)
Attaches an encrypted EBS volume to an EC2 instance.

9. detach_volume(session, volume_id)
Detaches an EBS volume from its associated EC2 instance.

10. stop_instance(session, instance_id)
Stops an EC2 instance.

11. start_instance(session, instance_id)
Starts an EC2 instance.

12. log_volume_details(details)
Logs the details of volume changes.

13. write_volume_details_to_file()
Writes the volume change details to a CSV file.

14. process_volumes_for_instance(session, volumes, kms_key)
Processes the EBS volumes attached to an EC2 instance, encrypting them as needed.

15. process_pending_snapshots(session)
Processes any snapshots that took longer than expected to complete.

16. main()
Main execution function that coordinates the entire process.

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
