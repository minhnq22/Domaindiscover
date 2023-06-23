#!/usr/bin/env python3
import requests
import json
import argparse

acunetix_host = ""
acunetix_port = ""
acunetix_apikey = ""

def checkAcunetixConnection():
    with open("config.conf", "r") as file:
        acunetix_config = json.load(file)
        global acunetix_host
        global acunetix_port
        global acunetix_apikey
        if acunetix_config["acunetix_host"]:
            acunetix_host = acunetix_config["acunetix_host"]
        else:
            print("acunetix_host is not set.")
            return False
        if acunetix_config["acunetix_port"]:
            acunetix_port = acunetix_config["acunetix_port"]
        else:
            print("acunetix_port is not set.")
            return False
        if acunetix_config["acunetix_apikey"]:
            acunetix_apikey = acunetix_config["acunetix_apikey"]
        else:
            print("acunetix_apikey is not set.")
            return False
    
    url = "https://" + acunetix_host + ":" + acunetix_port + "/api/v1/target_groups"
    headers = {
        "X-Auth": acunetix_apikey
    }
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 200:
        print("Connect to Acunetix ok!")
        return True
    else:
        print("Connetion fail.", response.status_code)
        return False

def createTargetsGroup(domain, output_path):
    url = "https://" + acunetix_host + ":" + acunetix_port + "/api/v1/target_groups"
    headers = {
        "X-Auth": acunetix_apikey
    }
    data = {
        "name": domain
    }
    response = requests.post(url, headers=headers, json=data, verify=False)
    if response.status_code == 201:
        print("Create Targets Group successful!")
        response_data = response.json()
        with open(f"{output_path}/acunetix_targets_group.txt", "w") as file:
            file.write(str(response_data))
        return response_data
    else:
        print("API request failed with status code:", response.status_code)
        return None

def createTargets(targets_list, targets_group, output_path):
    targets = []
    for target in targets_list:
        targets.append({
            "address": target["url"],
            "description": target["status_code"] + " | " + target["title"],
            "criticality": 30
        })
    url = "https://" + acunetix_host + ":" + acunetix_port + "/api/v1/targets/add"
    headers = {
        "X-Auth": acunetix_apikey
    }
    data = {
        "targets": targets,
        "groups": [targets_group.get("group_id")]
    }
    response = requests.post(url, headers=headers, json=data, verify=False)
    if response.status_code == 200:
        print("Create Targets successful!")
        response_data = response.json()
        with open(f"{output_path}/acunetix_targets.txt", "w") as file:
            file.write(str(response_data))
        return response_data
    else:
        print("API request failed with status code:", response.status_code)
        return None
    
def configurationTargets(targets):
    for target in targets["targets"]:
        url = "https://" + acunetix_host + ":" + acunetix_port + "/api/v1/targets/" + target["target_id"] + "/configuration"
        headers = {
            "X-Auth": acunetix_apikey
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

def createScans(targets):
    url = "https://" + acunetix_host + ":" + acunetix_port + "/api/v1/scans"
    headers = {
        "X-Auth": acunetix_apikey
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

def createScan(domain, targets, output_path):
    print("""
                                     _    _       
     /\                             | |  (_)      
    /  \    ___  _   _  _ __    ___ | |_  _ __  __
   / /\ \  / __|| | | || '_ \  / _ \| __|| |\ \/ /
  / ____ \| (__ | |_| || | | ||  __/| |_ | | >  < 
 /_/    \_\\\___| \__,_||_| |_| \___| \__||_|/_/\_\\
    """)
    if checkAcunetixConnection():
        targets_group = createTargetsGroup(domain, output_path)
        targets = createTargets(targets, targets_group, output_path)
        configurationTargets(targets)
        createScans(targets)
    else:
        print("Connect to Acunetix server has error. Check configuration file.")

def main(args):
    print("""
                                     _    _       
     /\                             | |  (_)      
    /  \    ___  _   _  _ __    ___ | |_  _ __  __
   / /\ \  / __|| | | || '_ \  / _ \| __|| |\ \/ /
  / ____ \| (__ | |_| || | | ||  __/| |_ | | >  < 
 /_/    \_\\\___| \__,_||_| |_| \___| \__||_|/_/\_\\
 
 Using -h or --help.
    """)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Acunetix Control")
    parser.add_argument("--status", action="store_true", help="Check scans status")
    parser.add_argument("--stop-scan", help="Specify the path of the result folder")
    parser.add_argument("--delete-scan", help="Specify the path of the result folder")
    parser.add_argument("--stop-all", action="store_true", help="Scan with Acunetix config file (optional)")
    parser.add_argument("--delete-all", action="store_true", help="Save Gowitness result to PostgreSQL config file (optional)")
    args = parser.parse_args()
    main(args)