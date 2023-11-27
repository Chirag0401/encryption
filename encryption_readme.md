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



My Performance
Proactive Infrastructure Development: Successfully engineered robust infrastructure solutions, enhancing system reliability and performance.
Scripting Expertise: Demonstrated proficiency in Python and boto3, notably in automating EBS volume encryption and EC2 inventory generation, significantly reducing manual workload.
Innovative Security Measures: Pioneered the creation of dynamic security groups using Excel-sourced IP rules, bolstering our network's security posture.
Terraform Mastery: Skillfully crafted Terraform code, contributing to efficient and scalable infrastructure management.
Compliance Vigilance: Diligently mitigated compliance issues in dom9 reports, ensuring our operations align with industry standards.
My Development
Technical Skill Enhancement: Continuously expanded my expertise in infrastructure creation and script automation, aligning with the latest industry trends.
Automation Champion: Innovated in script writing, notably in automating Zabbix dashboard creation, streamlining operational processes.
Server Setup Proficiency: Excelled in server setup tasks, ensuring high availability and optimal performance.
Shell Scripting Acumen: Demonstrated advanced skills in shell scripting, further automating and improving operational workflows.
Continuous Learning: Regularly updated my technical knowledge, staying ahead in a rapidly evolving tech landscape.
My Client (Combination of Performance and Development)
End-to-End Infrastructure Solutions: Provided comprehensive infrastructure solutions from creation to automation, significantly enhancing client experience.
Efficiency in Scripting: Automated crucial processes using Python, boto3, and shell scripts, resulting in faster and more reliable service delivery.
Security and Compliance Focus: Implemented stringent security measures and compliance practices, earning client trust and satisfaction.
Innovative Development Practices: Constantly developed innovative solutions like dynamic security groups, showcasing my commitment to technical excellence.
Client-Centric Development: Tailored my skill development to address client-specific needs, ensuring high-quality and relevant service delivery.
My Behaviour
Team Collaboration: Fostered a collaborative environment, contributing to team efforts and sharing knowledge.
Problem-Solving Attitude: Consistently approached challenges with a solution-oriented mindset, effectively addressing complex issues.
Professional Development: Actively sought feedback and learning opportunities, demonstrating a commitment to personal and professional growth.
Positive Work Ethic: Maintained a high level of dedication and reliability, contributing to a productive work atmosphere.
Adaptive and Resilient: Adapted swiftly to changing demands and maintained performance under pressure.
Goal: Risk and Compliance
100% Training Coverage: Achieved complete compliance training, demonstrating my commitment to understanding and mitigating risks.
Full Compliance with RegU and ARC: Diligently completed all regulatory and audit compliance requirements, ensuring 100% compliance.
Proactive Risk Management: Actively identified and mitigated potential risks, contributing to a secure and compliant operational environment.
Continuous Compliance Monitoring: Regularly monitored and adhered to compliance standards, ensuring ongoing alignment with industry regulations.
Educating Team on Compliance: Played a key role in educating the team about compliance practices, fostering a culture of awareness and adherence.
Efficiency: Operational Excellence
Streamlining Processes: Implemented efficient scripting solutions, significantly enhancing operational workflows.
Maximizing Resource Utilization: Optimized infrastructure and server setups for peak performance, ensuring optimal use of resources.
Automating for Efficiency: Leveraged automation in tasks like dashboard creation, reducing manual effort and increasing productivity.
Quality and Timeliness: Consistently delivered high-quality work within set timelines, contributing to overall operational excellence.
Innovative Solutions for Efficiency: Introduced innovative practices like dynamic security group creation, driving operational efficiency.
Summary for Year-End Connect
In my role as a Software Engineer 1 since July 10th, I have significantly contributed to our team’s success through innovative infrastructure solutions, expertise in scripting and automation, and a strong focus on security and compliance. My proactive approach to problem-solving and continuous skill development has not only enhanced our operational efficiency but also ensured client satisfaction and trust. I have consistently demonstrated a high level of professionalism and adaptability, positively impacting our team dynamics. Going forward, my goal is to continue excelling in risk management and operational excellence, maintaining 100% compliance and training coverage. My commitment to continuous learning and efficiency will drive further improvements in our processes and service delivery.







