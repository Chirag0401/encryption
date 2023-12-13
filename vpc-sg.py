import boto3
import os
import json
from prettytable import PrettyTable
import pandas as pd

def create_session():
    return boto3.Session(
        region_name=os.environ.get('AWS_DEFAULT_REGION'),
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.environ.get('AWS_SESSION_TOKEN'),
    )

def get_vpc_info(session):
    ec2_client = session.client("ec2")
    vpc_response = ec2_client.describe_vpcs()
    vpcs = vpc_response["Vpcs"]
    print(vpcs)
    vpc_info = []

    subnet_info = []
    route_info = []
    igw_info = []
    nat_info = []

    for vpc in vpcs:
        vpc_id = vpc["VpcId"]
        vpc_name = ""
        owner_id = vpc["OwnerId"]
        vpc_state = vpc["State"]

        for tag in vpc["Tags"]:
            if tag["Key"] == "Name":
                vpc_name = tag["Value"]

        cidr_block_association_set = vpc.get("CidrBlockAssociationSet", [])

        for cidr_block_association in cidr_block_association_set:
            cidr_block = cidr_block_association["CidrBlock"]
            cidr_block_state = cidr_block_association["CidrBlockState"]["State"]

            vpc_info.append({
                "VPC ID": vpc_id,
                "VPC Name": vpc_name,
                "Owner ID": owner_id,
                "Cidr_Block": cidr_block,
                "Cidr_Block_State": cidr_block_state,
                "State": vpc_state,
            })

        subnet_response = ec2_client.describe_subnets(
            Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
        )
        subnets = subnet_response["Subnets"]

        for subnet in subnets:
            subnet_id = subnet["SubnetId"]
            subnet_name = subnet["Tags"][0]["Value"]
            subnet_state = subnet["State"]
            ipv4_cidr = subnet["CidrBlock"]
            available_ip = subnet["AvailableIpAddressCount"]
            availability_zone = subnet["AvailabilityZone"]

            subnet_info.append({
                "SubnetName": subnet_name,
                "SubnetId": subnet_id,
                "State": subnet_state,
                "VPCID": vpc_id,
                "Ipv4_cidr": ipv4_cidr,
                "AvailableIpAddressCount": available_ip,
                "AvailabilityZone": availability_zone,
            })

        route_response = ec2_client.describe_route_tables(
            Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
        )
        route_tables = route_response["RouteTables"]

        for route_table in route_tables:
            route_table_name = ""
            route_table_id = route_table["RouteTableId"]

            if "Tags" in route_table:
                for tag in route_table["Tags"]:
                    if tag["Key"] == "Name":
                        route_table_name = tag["Value"]
                        break

            for association in route_table["Associations"]:
                subnet_id = association.get("SubnetId")
                main = association.get("Main")

                if subnet_id:
                    routes = []
                    for route in route_table["Routes"]:
                        destination_cidr = route.get("DestinationCidrBlock")
                        target = route.get("GatewayId") or route.get("NatGatewayId") or route.get(
                            "VpcPeeringConnectionId") or route.get("NetworkInterfaceId")
                        state = route.get("State")
                        routes.append({
                            "DestinationCidr": destination_cidr,
                            "Target": target,
                            "State": state
                        })

                    route_info.append({
                        "RouteTableName": route_table_name,
                        "RouteTableId": route_table_id,
                        "SubnetId": subnet_id,
                        "VpcId": vpc_id,
                        "Main": main,
                        "Routes": routes
                    })

        igw_response = ec2_client.describe_internet_gateways(
            Filters=[{"Name": "attachment.vpc-id", "Values": [vpc_id]}]
        )
        internet_gateways = igw_response["InternetGateways"]

        for igw in internet_gateways:
            igw_id = igw["InternetGatewayId"]
            state = igw["Attachments"][0]["State"]

            if "Tags" in igw:
                igw_name = igw["Tags"][0]["Value"]
            else:
                igw_name = ""

            igw_info.append({
                "InternetGatewayID": igw_id,
                "InternetGatewayName": igw_name,
                "State": state,
                "VPCID": vpc_id,
            })

        nat_response = ec2_client.describe_nat_gateways(
            Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
        )
        nat_gateways = nat_response["NatGateways"]

        for nat in nat_gateways:
            nat_gateway_id = nat["NatGatewayId"]

            if "Tags" in nat:
                nat_gateway_name = nat["Tags"][0]["Value"]
            else:
                nat_gateway_name = ""

            state = nat["State"]
            subnet_id = nat["SubnetId"]
            private_ip = nat["NatGatewayAddresses"][0]["PrivateIp"]
            public_ip = nat["NatGatewayAddresses"][0]["PublicIp"]

            nat_info.append({
                "NATGatewayID": nat_gateway_id,
                "NATGatewayName": nat_gateway_name,
                "State": state,
                "SubnetID": subnet_id,
                "VPCID": vpc_id,
                "PrivateIP": private_ip,
                "PublicIP": public_ip,
            })

    subnet_table = pd.DataFrame(subnet_info)
    route_table = pd.DataFrame(route_info)
    igw_table = pd.DataFrame(igw_info)
    nat_table = pd.DataFrame(nat_info)

    account_id = session.client("sts").get_caller_identity()["Account"]
    filename = f"vpc_info_{account_id}.xlsx"

    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        vpc_df = pd.DataFrame(vpc_info)
        vpc_df.to_excel(writer, sheet_name="VPC", index=False)
        subnet_table.to_excel(writer, sheet_name="Subnets", index=False)
        igw_table.to_excel(writer, sheet_name="IGWs", index=False)
        nat_table.to_excel(writer, sheet_name="NATs", index=False)

        # Create a new sheet for routes
        route_sheet = writer.book.create_sheet("Routes")
        route_sheet.append(["Route Table Name", "Route Table ID", "Subnet ID", "VPC ID", "Main", "Destination CIDR", "Target", "State"])

        row = 1
        for route in route_info:
            route_table_name = route["RouteTableName"]
            route_table_id = route["RouteTableId"]
            subnet_id = route["SubnetId"]
            vpc_id = route["VpcId"]
            main = route["Main"]
            routes = route["Routes"]

            for r in routes:
                destination_cidr = r["DestinationCidr"]
                target = r["Target"]
                state = r["State"]

                route_sheet.append([route_table_name, route_table_id, subnet_id, vpc_id, main, destination_cidr, target, state])

                row += 1

    return filename

def get_security_group_details(session):
    ec2 = session.client("ec2")
    response = ec2.describe_security_groups()
    security_groups = response["SecurityGroups"]

    security_group_info = []

    for security_group in security_groups:
        group_name = security_group["GroupName"]
        group_id = security_group["GroupId"]

        rules = []
        for rule in security_group["IpPermissions"]:
            rule_id = ""
            if "UserIdGroupPairs" in rule and rule["UserIdGroupPairs"]:
                rule_id = rule["UserIdGroupPairs"][0]["GroupId"]

            rule_type = rule["IpProtocol"]
            port_range = ""

            if "FromPort" in rule and "ToPort" in rule:
                port_range = f"{rule['FromPort']}-{rule['ToPort']}"

            for source in rule["IpRanges"]:
                source_cidr = source["CidrIp"]
                description = source.get("Description", "")

                rules.append({
                    "SecurityGroupRuleId": rule_id,
                    "Type": rule_type,
                    "PortRange": port_range,
                    "Source": source_cidr,
                    "Description": description
                })

        security_group_info.append({
            "Name": group_name,
            "SecurityGroupId": group_id,
            "Rules": rules
        })

    account_id = session.client("sts").get_caller_identity()["Account"]
    filename = f"security_group_info_{account_id}.xlsx"

    table = pd.DataFrame(columns=["Security Group Name", "Security Group ID", "Rule ID", "Type", "Port Range", "Source", "Description"])

    for group_info in security_group_info:
        for rule in group_info["Rules"]:
            table = table.append({
                "Security Group Name": group_info["Name"],
                "Security Group ID": group_info["SecurityGroupId"],
                "Rule ID": rule["SecurityGroupRuleId"],
                "Type": rule["Type"],
                "Port Range": rule["PortRange"],
                "Source": rule["Source"],
                "Description": rule["Description"]
            }, ignore_index=True)

    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        table.to_excel(writer, sheet_name="Security Group Info", index=False)

    return filename


def get_account_id(session):
    sts_client = session.client("sts")
    response = sts_client.get_caller_identity()
    account_id = response["Account"]
    return account_id

def main():
    session = create_session()
    get_vpc_info(session)
    get_security_group_details(session)

if __name__ == "__main__":
    main()
