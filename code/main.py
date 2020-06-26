# -*- coding: utf-8 -*-

import boto3
import logging
import xlsxwriter
from pprint import pprint
from config import Config
from typing import Text, Dict, List

# ==============================================================================
# GLOBAL
# ==============================================================================

config = Config()

logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s  %(levelname)-10s %(processName)s  %(name)s %(message)s",
  datefmt="%Y-%m-%d-%H-%M-%S"
)

ec2_client = boto3.client(
  "ec2",
  aws_access_key_id=config.get_env("AWS_ACCESS_KEY_ID"),
  aws_secret_access_key=config.get_env("AWS_SECRET_ACCESS_KEY"),
  region_name=config.get_env("AWS_REGION")
)

s3_client = boto3.client(
  "s3",
  aws_access_key_id=config.get_env("AWS_ACCESS_KEY_ID"),
  aws_secret_access_key=config.get_env("AWS_SECRET_ACCESS_KEY"),
  region_name=config.get_env("AWS_REGION")
)

route_client = boto3.client(
  "route53",
  aws_access_key_id=config.get_env("AWS_ACCESS_KEY_ID"),
  aws_secret_access_key=config.get_env("AWS_SECRET_ACCESS_KEY"),
  region_name=config.get_env("AWS_REGION")
)

ecs_client = boto3.client(
  "ecs",
  aws_access_key_id=config.get_env("AWS_ACCESS_KEY_ID"),
  aws_secret_access_key=config.get_env("AWS_SECRET_ACCESS_KEY"),
  region_name=config.get_env("AWS_REGION")
)

# ==============================================================================
# FUNCTIONS
# ==============================================================================

def get_name(instance: Dict) -> Text:
  if "Tags" in instance.keys():
    for tag in instance["Tags"]:
        if tag["Key"] == "Name":
            return tag["Value"]
  else:
    return "-"

def get_ec2_information() -> List:
  logging.info("Get EC2 info...")
  ec2, ec2_list = ec2_client.describe_instances(), list()
  for reservations in ec2["Reservations"]:
    for instance in reservations["Instances"]:
      hostname = get_name(instance)
      instance_type = instance["InstanceType"] if "InstanceType" in instance.keys() else "-"
      plataform = instance["Platform"] if "Platform" in instance.keys() else "linux"
      ec2_list.append([hostname, instance_type, plataform])
  return ec2_list

def get_s3_information() -> List:
  logging.info("Get S3 info...")
  s3, s3_list = s3_client.list_buckets(), list()
  for bucket in s3["Buckets"]:
    name = bucket["Name"]
    creation = bucket["CreationDate"].strftime("%Y-%m-%d %H:%M:%S")
    s3_list.append([name, creation])
  return s3_list

def get_vpns_information() -> List:
  logging.info("Get VPN info...")
  vpns, vpns_list = ec2_client.describe_vpn_connections(), list()
  for vpn in vpns["VpnConnections"]:
    vpn_id = vpn["VpnConnectionId"]
    vpn_name = get_name(vpn)
    vpns_list.append([vpn_id, vpn_name])
  return vpns_list

def get_route_information() -> List:
  logging.info("Get DNS info...")
  routes, routes_list = route_client.list_hosted_zones(), list()
  for route in routes["HostedZones"]:
    route_id = route["Id"]
    route_name = route["Name"]
    route_resource_record_set_count = route["ResourceRecordSetCount"]
    routes_list.append([route_id, route_name, route_resource_record_set_count])
  return routes_list

def get_ecs_information() -> List:
  logging.info("Get ECS info...")
  ecs, ecs_list = ecs_client.list_clusters(), list()
  for cluster in ecs["clusterArns"]:
    services = ecs_client.list_services(cluster=cluster)
    for service in services["serviceArns"]:
      tasks = ecs_client.list_tasks(cluster=cluster, serviceName=service)
      describe_services = ecs_client.describe_services(cluster=cluster,services=[service])["services"]
      runningCount = [elemento["runningCount"] for elemento in describe_services][0]
      desiredCount = [elemento["desiredCount"] for elemento in describe_services][0]
      for task in tasks["taskArns"]:
        information = ecs_client.describe_tasks(cluster=cluster,tasks=[task])["tasks"]
        for info in information:
          cpu, memory = info["cpu"], info["memory"]
          ecs_list.append([cpu, memory, runningCount, desiredCount, service.split("/")[-1], cluster.split("/")[-1]])
  return ecs_list

# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":

  logging.info("Starting script. Get information...")

  ec2_list = get_ec2_information()
  s3_list = get_s3_information()
  vpns_list = get_vpns_information()
  routes_list = get_route_information()
  ecs_list = get_ecs_information()

  information = [
    {"name": "ec2", "data": ec2_list, "columns": ["A1", "B1", "C1"], "names": ["HOSTNAME", "TYPE", "PLATAFORM"]},
    {"name": "s3", "data":s3_list, "columns": ["A1", "B1"], "names": ["NAME", "CREATION"]},
    {"name": "vpn", "data":vpns_list, "columns": ["A1", "B1"], "names": ["ID", "NAME"]},
    {"name": "dns", "data":routes_list, "columns": ["A1", "B1", "C1"], "names": ["ID", "NAME", "RESOURCE RECORD SET"]},
    {"name": "ecs", "data":ecs_list, "columns": ["A1", "B1", "C1", "D1", "E1", "F1"], "names": ["CPU", "MEMORY", "RUNNING", "DESIRED", "SERVICE", "CLUSTER"]}
  ]

  logging.info("Creation Excel file...")

  with xlsxwriter.Workbook("files/report.xlsx") as workbook:

    for value in information:
      worksheet, bold = workbook.add_worksheet(value["name"].upper()), workbook.add_format({"bold": True})
      for column, name in zip(value["columns"], value["names"]):
        worksheet.write(column, name, bold)
      for row_num, data in enumerate(value["data"], start=1):
        worksheet.write_row(row_num, 0, data)

  logging.info("Finish Execution :)")
