import subprocess
import json
from urllib.parse import urlparse
from termcolor import colored

# Define your clusters here
CLUSTERS = [
    {"name": "non-prod-warehouse", "project": "corp-test-mgmt-anthos-3578", "context": "connectgateway_corp-test-mgmt-anthos-3578_global_non-prod-warehouse"},
    # Add other clusters here
]

def switch_context(cluster_info):
    print(f"Switching context to: {cluster_info}")  # Debugging print
    context = cluster_info['context']
    cmd = ['kubectl', 'config', 'use-context', context]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if proc.returncode != 0:
        print(f"Error switching to context {context}: {err.decode()}")  # Decode error message
        return False

    print(f"Switched to context {context}")  # Debugging print
    return True

def fetch_ingresses():
    print("Fetching ingresses...")  # Debugging print
    cmd = ['kubectl', 'get', 'ingresses', '--all-namespaces', '-o', 'json']
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if proc.returncode != 0:
        print(f"Error fetching ingresses: {err.decode()}")  # Decode error message
        return None

    ingresses = json.loads(out)
    print(f"Fetched ingresses: {ingresses}")  # Debugging print

    # Print all the ingresses in the cluster, each on a new line
    for ingress in ingresses['items']:
        print(json.dumps(ingress, indent=4))  # Print each ingress with nice formatting

    return ingresses

def check_endpoint(url, ingresses):
    print(f"Checking URL: {url}")  # Debugging print
    host = urlparse(url).netloc
    ingress_found = any(ingress for ingress in ingresses['items'] if any(rule['host'] == host for rule in ingress['spec']['rules']))

    cmd = ['curl', '-ks', '-o', '/dev/null', '-w', '%{http_code}', url]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if proc.returncode != 0:
        print(f"Error checking {url}: {err.decode()}")  # Decode error message
        return None

    status_code = out.decode().strip()
    print(f"Status code for {url}: {status_code}")  # Debugging print

    if status_code == '200':
        return colored(f"{url}: '{status_code}' - SSL Working Fine", "green")
    elif status_code == '404' and not ingress_found:
        return colored(f"{url}: '404' - No ingress found", "yellow")
    elif status_code == '404':
        return colored(f"{url}: '404' - Error 404 returned, please investigate", "red")
    else:
        return colored(f"Unexpected output for {url}: '{status_code}'", "red")

def main():
    print("Script started...")  # Debugging print

    for cluster in CLUSTERS:
        if not switch_context(cluster):
            continue  # if context switch fails, continue to the next cluster

        ingresses = fetch_ingresses()
        if not ingresses:
            continue  # if fetching ingresses fails, continue to the next cluster

        for ingress in ingresses['items']:
            for rule in ingress['spec']['rules']:
                host = rule['host']
                url = f"https://{host}/health"
                result = check_endpoint(url, ingresses)
                if result:
                    print(result)

    print("Script execution finished.")  # Debugging print

if __name__ == "__main__":
    main()
