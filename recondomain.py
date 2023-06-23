#!/usr/bin/env python3

import argparse
import urllib3
import os
import shutil
import subprocess
import acunetix_control

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

domain = ""
output_path = ""
postgres_host = ""
postgres_port = ""
postgres_user = ""
postgres_pass = ""

def runSubfinderCommand():
    command = f"subfinder -d {domain} -o {output_path}/subfinder.txt"
    subprocess.run(command, shell=True)

def runHttpxCommand():
    command = f"cat {output_path}/subfinder.txt | httpx --no-color -title -status-code | tee {output_path}/httpx.txt"
    subprocess.run(command, shell=True)

def runNucleiCommand():
    command = f"cat {output_path}/httpx.txt | awk '{{print $1}}' | nuclei -t ~/.local/nuclei-templates -o {output_path}/nuclei.txt"
    subprocess.run(command, shell=True)

def runAcunetix():
    targets = process_httpx_file(f"{output_path}/httpx.txt")
    acunetix_control.createScan(domain, targets, output_path)

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

def main(args):
    global domain
    global output_path
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
    runSubfinderCommand()
    runHttpxCommand()
    runNucleiCommand()

    if acunetix:
        runAcunetix()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Recon Domain")
    parser.add_argument("-d", "--domain", required=True, help="Specify the domain")
    parser.add_argument("-o", "--output", help="Specify the path of the result folder")
    parser.add_argument("--acunetix", action="store_true", help="Scan with Acunetix config file (optional)")
    parser.add_argument("--postgres", action="store_true", help="Save Gowitness result to PostgreSQL config file (optional)")
    args = parser.parse_args()
    main(args)