# Disaster Recovery (DR) Script for RDS

This script provides a mechanism to handle disaster recovery for RDS databases, specifically for MSSQL and Aurora PostgreSQL. In the event of a disaster in the primary region, it promotes the read replica or secondary cluster in the secondary region and makes necessary modifications. Additionally, it updates the Route 53 record to point to the newly promoted database.

## Features

- Promotes MSSQL read replicas.
- Promotes Aurora PostgreSQL secondary clusters.
- Modifies the promoted database instance/cluster with necessary configurations.
- Updates the Route 53 record to point to the promoted database.

## Prerequisites

- AWS CLI installed and configured.
- Python 3.x
- Boto3 library installed (`pip install boto3`).

## Usage

1. Set your AWS credentials (Access Key, Secret Access Key, Session Token) in the script.
2. Run the script:

\```bash
python3 your_script_name.py
\```

3. Follow the prompts to provide necessary inputs:
    - DB engine (either `mssql` or `aurora-postgres`).
    - Primary and secondary AWS regions.
    - Identifiers for the primary and secondary databases.
    - Whether the DR condition is activated.

4. If the DR condition is activated, the script will handle the disaster recovery process and provide feedback on the operations performed.

## Customization

- Update the `hosted_zone_id` and `record_name` in the `update_route53_record` function to match your Route 53 configuration.
- Adjust the sleep times (`time.sleep()`) as necessary based on your RDS configurations and the time it takes for certain operations to complete.

## Note

Ensure that you have the necessary AWS permissions to perform RDS and Route 53 operations. Always test the script in a non-production environment before using it in a production scenario.
