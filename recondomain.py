#!/usr/bin/env python3

import argparse
import requests
import json
import urllib3
import os
import shutil
import subprocess

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

acunetix_host = ""
acunetix_port = ""
acunetix_api = ""
postgres_host = ""
postgres_port = ""
postgres_user = ""
postgres_pass = ""

def runSubfinderCommand(domain, output_path):
    command = f'subfinder -d {domain} -o {output_path}/subfinder.txt'
    subprocess.run(command, shell=True)

def runHttpxCommand(output_path):
    command = f'cat {output_path}/subfinder.txt | httpx --no-color -title -status-code | tee /tmp/{output_path}/httpx.txt'
    subprocess.run(command, shell=True)

def runNucleiCommand(output_path):
    command = f'nuclei -t ~/.local/nuclei-templates -o {output_path}/nuclei.txt'
    subprocess.run(command, shell=True)

def checkAcunetixConnection():
    with open("acunetix.conf", "r") as file:
        config_data = json.load(file)
    return True

def process_httpx_file(filename):
    result = []
    with open(filename, "r", encoding="utf-8") as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if line:
                parts = line.split()
                url = parts[0]
                status_code = parts[1].strip("[]")
                title = ' '.join(parts[2:]).strip("[]")
                result.append({
                    "url": url,
                    "status_code": status_code,
                    "title": title
                })
    return result

def createTargetsGroup(domain):
    url = "https://" + acunetix_host + ":" + acunetix_port + "/api/v1/target_groups"
    headers = {
        "X-Auth": acunetix_api
    }
    data = {
        "name": domain
    }

    response = requests.post(url, headers=headers, json=data, verify=False)
    
    if response.status_code == 201:
        print("Create Targets Group successful!")
        response_data = response.json()
        return response_data
    else:
        print("API request failed with status code:", response.status_code)
        return None

def createTargets(targets_list, targets_group):
    targets = []
    for target in targets_list:
        targets.append({
            "address": target["url"],
            "description": target["status_code"] + " | " + target["title"],
            "criticality": 30
        })


    url = "https://" + acunetix_host + ":" + acunetix_port + "/api/v1/targets/add"
    headers = {
        "X-Auth": acunetix_api
    }
    data = {
        "targets": targets,
        "groups": [targets_group.get("group_id")]
    }

    response = requests.post(url, headers=headers, json=data, verify=False)
    
    if response.status_code == 200:
        print("Create Targets successful!")
        response_data = response.json()
        return response_data
    else:
        print("API request failed with status code:", response.status_code)
        return None
    
def configurationTargets(targets):
    for target in targets["targets"]:
        url = "https://" + acunetix_host + ":" + acunetix_port + "/api/v1/targets/" + target["target_id"] + "/configuration"
        headers = {
            "X-Auth": acunetix_api
        }
        data = {
            "scan_speed": "sequential",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        response = requests.patch(url, headers=headers, json=data, verify=False)
    
        if response.status_code == 204:
            print("Configuration Targets successful.", target["address"]) 
        else:
            print("Configuration Targets false.", target["address"])

        url = "https://" + acunetix_host + ":" + acunetix_port + "/api/v1/targets/" + target["target_id"] + "/allowed_hosts"
        for target_temp in targets["targets"]:
            data = {
                "target_id": target_temp["target_id"]
            }
            response = requests.post(url, headers=headers, json=data, verify=False)

def createScan(targets):
    url = "https://" + acunetix_host + ":" + acunetix_port + "/api/v1/scans"
    headers = {
        "X-Auth": acunetix_api
    }
    for target in targets["targets"]:
        data = {
                "target_id": target["target_id"],
                "profile_id": "11111111-1111-1111-1111-111111111111",
                "report_template_id": "11111111-1111-1111-1111-111111111111",
                "schedule": {
                    "disable": True,
                    "time_sensitive": False,
                    "history_limit": 10,
                    "start_date": None,
                    "triggerable": False
                },
                "max_scan_time": 0,
                "incremental": False
        }
        response = requests.post(url, headers=headers, json=data, verify=False)
    
        if response.status_code == 201:
            print("Start scan Targets successful.", target["address"]) 
        else:
            print("Start scan Targets false.", target["address"])


def main(args):
    domain = args.domain
    output_path = args.output or "/tmp"
    acunetix = args.acunetix
    postgres = args.postgres

    output_path = f"{output_path}/{domain}"
    # Check if the output path exists
    if os.path.exists(output_path):
        # Ask the user whether to continue or not
        choice = input(f"The output path '{output_path}' already exists. This action will delete the existing directory and its contents. Do you want to continue? (y/n): ")
        if choice.lower() != "y":
            print("Aborted by user.")
            return

        # Remove the existing directory
        shutil.rmtree(output_path)
        print(f"Deleted existing directory: {output_path}")

    # Create a new directory
    os.makedirs(output_path)
    print(f"Created new directory: {output_path}")

    # Run
    runSubfinderCommand(domain, output_path)
    runHttpxCommand(output_path)
    runNucleiCommand(output_path)

    if acunetix:
        if checkAcunetixConnection():
            targets = process_httpx_file(f'{output_path}/httpx.txt')
            targets_group = createTargetsGroup(domain)
            targets = createTargets(targets, targets_group)
            configurationTargets(targets)
            createScan(targets)
        else:
            print("Connect to Acunetix server has error. Check configuration file.")

    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Recon Domain")
    parser.add_argument("-d", "--domain", required=True, help="Specify the domain")
    parser.add_argument("-o", "--output", help="Specify the path of the result folder")
    parser.add_argument("--acunetix", action="store_true", help="Scan with Acunetix config file (optional)")
    parser.add_argument("--postgres", action="store_true", help="Save Gowitness result to PostgreSQL config file (optional)")
    args = parser.parse_args()
    main(args)