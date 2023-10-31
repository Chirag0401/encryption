import boto3
import logging
import argparse
from getpass import getpass
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String

# Setup logging
logging.basicConfig(level=logging.INFO)

def create_rds_instance(client, db_engine):
    dbname = input("Enter the database name for the new RDS instance: ").strip()
    user = input("Enter the master username for the new RDS instance: ").strip()
    password = getpass("Enter the master password for the new RDS instance: ").strip()

    try:
        response = client.create_db_instance(
            DBName=dbname,
            DBInstanceIdentifier='mydbinstance',
            AllocatedStorage=20,
            DBInstanceClass='db.t2.small',
            Engine=db_engine,
            MasterUsername=user,
            MasterUserPassword=password,
            PubliclyAccessible=True
        )
        logging.info("RDS instance is being created...")
        waiter = client.get_waiter('db_instance_available')
        waiter.wait(DBInstanceIdentifier='mydbinstance')
        logging.info("RDS instance created and available.")
        return response['DBInstance']['Endpoint']['Address'], dbname, user, password
    except client.exceptions.ClientError as e:
        logging.error(f"Error creating RDS instance: {e}")
        return None, None, None, None

def check_instance_exists(client, db_instance_identifier):
    try:
        response = client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)
        if response.get('DBInstances'):
            logging.info(f"RDS instance {db_instance_identifier} exists.")
            return response['DBInstances'][0]['Endpoint']['Address']
        else:
            logging.warning(f"No RDS instance found with identifier {db_instance_identifier}.")
            return None
    except client.exceptions.DBInstanceNotFoundFault:
        logging.error(f"No RDS instance found with identifier {db_instance_identifier}.")
        return None

def create_and_read_table(host, dbname, user, password):
    # Using SQLAlchemy for database operations
    engine = create_engine(f'postgresql://{user}:{password}@{host}/{dbname}')
    metadata = MetaData()

    # Create table
    test_table = Table('test_table', metadata,
                       Column('id', Integer, primary_key=True),
                       Column('name', String(50))
                       )
    test_table.create(engine, checkfirst=True)
    logging.info("Table created.")

    # Insert data
    conn = engine.connect()
    ins = test_table.insert().values(name="test_name")
    conn.execute(ins)
    logging.info("Data inserted.")

    # Read data
    s = test_table.select()
    result = conn.execute(s)
    for row in result:
        print(row)

def main():
    parser = argparse.ArgumentParser(description="Manage RDS instances.")
    parser.add_argument("action", choices=["new", "existing"], help="Choose to create a new RDS instance or use an existing one.")
    args = parser.parse_args()

    client = boto3.client('rds')

    if args.action == 'new':
        db_engine = input("Enter the database engine (for this example, use 'postgres'): ").strip().lower()
        host, dbname, user, password = create_rds_instance(client, db_engine)
    elif args.action == 'existing':
        db_instance_identifier = input("Enter the DBInstanceIdentifier for the existing RDS instance: ").strip()
        host = check_instance_exists(client, db_instance_identifier)
        if not host:
            return
        dbname = input("Enter the database name for the existing RDS instance: ").strip()
        user = input("Enter the master username for the existing RDS instance: ").strip()
        password = getpass("Enter the master password for the existing RDS instance: ").strip()

    create_and_read_table(host, dbname, user, password)

if __name__ == "__main__":
    main()
