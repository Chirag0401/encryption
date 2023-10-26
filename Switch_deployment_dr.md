# RDS Setup and Verification Script

This script provides functionalities to either set up a new RDS instance or verify an existing one. It supports both MSSQL and Aurora PostgreSQL engines. The script also integrates with Terraform to automate the provisioning and verification of RDS resources.

## Features

- Option to set up a new RDS instance using Terraform.
- Option to verify and use an existing RDS instance.
- Supports MSSQL and Aurora PostgreSQL database engines.
- Ability to create or verify a read replica for the RDS instance.

## Prerequisites

- AWS CLI installed and configured.
- Python 3.x
- Boto3 library installed (`pip install boto3`).
- Terraform installed and configured.
- Terraform scripts for RDS setup located in `/home/ec2-user/DR-RDS`.

## Usage

1. Set your AWS credentials (Access Key, Secret Access Key, Session Token) in the script.
2. Run the script:

\```bash
python3 your_script_name.py
\```

3. Follow the prompts to:
    - Decide between setting up a new RDS instance or verifying an existing one.
    - Choose the database engine.
    - Provide necessary identifiers for RDS instances and replicas.

4. The script will either set up the RDS resources using Terraform or verify the existing resources based on the provided inputs.

## Customization

- Update the `SECONDARY_REGION` and `terraform_directory` constants as per your requirements.
- Adjust the Terraform commands and paths based on your Terraform scripts' structure and requirements.

## Note

Ensure that you have the necessary AWS permissions to perform RDS operations and Terraform permissions for provisioning AWS resources. Always test the script in a non-production environment before using it in a production scenario.
