import os
import subprocess
import requests
import json
import yaml

infracost_api_key = os.getenv("INFRACOST_API_KEY","")
dt_environment = os.getenv("DT_ENVIRONMENT","")
dt_api_token = os.getenv("DT_API_TOKEN","") # API Token Permissions required: "read settings", "write settings", "ingest metrics"
current_dir_path = os.path.dirname(os.path.realpath(__file__))

if infracost_api_key == "":
  print("Environment Variable INFRACOST_API_KEY is not set. This is mandatory. Exiting.")
  exit()
if dt_environment == "":
  print("Environment Variable DT_ENVIRONMENT is not set. Should be like: https://abc123.live.dynatrace.com OR https://ab-123.dt-managed.com/e/UUID (no trailing slash) This is mandatory. Exiting.")
  exit()
if dt_api_token == "":
  print("Environment Variable DT_API_TOKEN is not set. Should start with dtc01. and have permissions: read settings, write settings and ingest metrics. Exiting.")
  exit()

entity_name = "infracostreport"
dt_headers = {
        "accept": "application/json",
        "authorization": f"Api-Token {dt_api_token}"
    }

def create_entity_type():
    print(f"-- Create entity:{entity_name} Entity Type in Dynatrace --")

    dt_entity = {
        "schemaId": "builtin:monitoredentities.generic.type",
		"scope": "environment",
        "value": {
            "enabled": True,
            "name": f"entity:{entity_name}",
            "displayName": "Infracost Report",
            "createdBy": "Python Infracost Report Tool for Keptn"
        }
	}

    dt_entity_sources = []
    dt_entities_prefix_entity_source = {
        "sourceType": "Metrics",
        "condition": f"$prefix(entity.{entity_name})"
    }
    dt_entity_sources.append(dt_entities_prefix_entity_source)

    
    dt_entity_attributes = []

    dt_entity_attribute = {
        "key": "projectname",
        "displayName": "projectname",
        "pattern": "{projectname}"
    }
    dt_entity_attributes.append(dt_entity_attribute)

    # Build Rules
    dt_entity_rules = []
    dt_entity_rule = {
        "idPattern": "{projectname}",
        "instanceNamePattern": "{projectname}",
        "sources": dt_entity_sources,
        "attributes": dt_entity_attributes
    }
    dt_entity_rules.append(dt_entity_rule)
    
    # Attach rules to entity
    dt_entity['value']['rules'] = dt_entity_rules
    

    return dt_entity

def create_entity_in_dt(dt_entities, environment, token):
    print("-- Create Dynatrace Configurations --")

    endpoint = f"{environment}/api/v2/settings/objects"

    params = {
        "schemaIds": "builtin:monitoredentities.generic.type",
        "scopes": "environment",
        "fields": "objectId,value"
    }

    # First try to GET the object ID (in case it exists already)
    response = requests.get(url=endpoint,params=params,headers=dt_headers)

    response_json = response.json()

    item_exists = False

    for item in response_json['items']:
        if item['value']['name'] == f"entity:{entity_name}":
            item_exists = True
            return response

    # If settings object item does not exist, create it
    if not item_exists:
        response = requests.post(url=endpoint, json=dt_entities, headers=dt_headers)
        return response


def post_metrics_to_dt(metric_string, environment, token):
    print("-- Posting metrics to Dynatrace --")

    endpoint = f"{environment}/api/v2/metrics/ingest"

    response = requests.post(url=endpoint, headers=dt_headers, data=metric_string)

    return response

dt_entity = create_entity_type()
dt_entities = list()
dt_entities.append(dt_entity)

dt_response = create_entity_in_dt(dt_entities, dt_environment, dt_api_token)

if dt_response.status_code != 200:
    # something went wrong creating the object. Exit
    print(f"Could not create entity:{entity_name}. Response code is: {dt_response.status_code}. Text is: {dt_response.text}. Exiting")
    exit()

# Read infracost.yml
# Expected in same folder as app.py
infracost_config_file_path = os.path.join(current_dir_path, "infracost.yml")
f = ""
try:
    f = open(infracost_config_file_path, "r")
except OSError:
    print(f"1: Could not open/read file: {f}. This is mandatory. Please create in your repo. Exiting.")
    exit()

version = 0
projects = list()


with open(infracost_config_file_path,"r") as infracost_file:
    infracost_config_content = yaml.safe_load(infracost_file)
    
    # We should have two YAML collections: "version" and "projects"
    version = infracost_config_content['version']
    projects = infracost_config_content['projects']

    for project in projects:
      # Take each relative path eg. "terraform" and transform to a full path "/keptn/files/terraform"
      # These will be stored during the creation of a temporary file in the write phase next
      print(f"Setting existing project path: {project['path']} to {os.path.join(current_dir_path, project['path'])}")
      project['path'] = os.path.join(current_dir_path, project['path'])

# Transform the relative paths received from infracost.yml
# to "/keptn/files/relativePathHere"
# Write a temporary file into /tmp
temp_infracost_file_path = os.path.join("/tmp","infracost.modified.yml")
with open(temp_infracost_file_path,"w") as temp_infracost_file:
    yaml.safe_dump({"version": version}, temp_infracost_file)
    yaml.safe_dump({"projects": projects}, temp_infracost_file)

output_file_path = os.path.join("/tmp","output.json") # Holds infracost output JSON

process_output = subprocess.run(["infracost", "breakdown", "--config-file", temp_infracost_file_path, "--format", "json", "--out-file", output_file_path])

json_output = {}

f = ""
try:
  f = open(output_file_path, "r")
except OSError:
  print(f"2: Could not open/read output file: {f}. Infracost should have created this. This is mandatory. Exiting.")
  exit()

with open(output_file_path, "r") as output_file:
    json_output = json.load(output_file)

dt_metric_string = ""
for project in json_output['projects']:
    print(f"Project Name: {project['name']}. Project Monthly Cost: {project['breakdown']['totalMonthlyCost']}")

    line_sep = os.linesep

    dt_metric_string += f"entity.{entity_name}.totalHourlyCost,projectname={project['name']} {project['breakdown']['totalHourlyCost']}{line_sep}"
    dt_metric_string += f"entity.{entity_name}.totalMonthlyCost,projectname={project['name']} {project['breakdown']['totalMonthlyCost']}{line_sep}"

    print("Printing Metric String to send to DT:")
    print(dt_metric_string)

# Build all metrics. Send to DT
dt_response = post_metrics_to_dt(dt_metric_string, dt_environment, dt_api_token)

print(dt_response.status_code)
print(dt_response.text)
