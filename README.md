# Domain discover
Using subfinder, httpx, nuclei and Acunetix for scan domain and sub-domains.

```
usage: recondomain.py [-h] -d DOMAIN [-o OUTPUT] [--acunetix] [--postgres]

Recon Domain

options:
  -h, --help            show this help message and exit
  -d DOMAIN, --domain DOMAIN
                        Specify the domain
  -o OUTPUT, --output OUTPUT
                        Specify the path of the result folder
  --acunetix            Scan with Acunetix config file (optional)
  --postgres            Save Gowitness result to PostgreSQL config file (optional)
```

```
usage: acunetix_control.py [-h] [--targets-path TARGETS_PATH] [--status] [--stop-scans] [--delete-scans]

Acunetix Control

options:
  -h, --help            show this help message and exit
  --targets-path TARGETS_PATH
                        Path to targets (domain), acunetix_targets_group.json and acunetix_targets.json
  --status              Check scans status
  --stop-scans          Stop scan(s)
  --delete-scans        Delete scan(s)
```