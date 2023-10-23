import subprocess
import json

# Define your clusters with relevant details.
CLUSTERS = [
    {"name": "non-prod-buying", "project": "project1", "context": "context1"},
    # ... other clusters ...
]

# ANSI escape codes for coloring text.
class ANSIColors:
    RED = '\033[91m'
    ENDC = '\033[0m'
    # Add more colors if needed

def switch_context(cluster_info):
    # Switches the kubectl context to the specified cluster.
    context = cluster_info['context']
    cmd = ['kubectl', 'config', 'use-context', context]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if proc.returncode != 0:
        print(f"Error switching to context {context}: {err.decode()}")
        return False

    print(f"Switched to context {context}")
    return True

def get_ingresses():
    # Fetches all ingresses in the current kubectl context.
    cmd = ['kubectl', 'get', 'ing', '-o', 'json', '--all-namespaces']
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if proc.returncode != 0:
        print(f"Error fetching ingresses: {err.decode()}")
        return [], []

    ingresses = json.loads(out.decode())['items']
    urls_with_ingress = []

    for ing in ingresses:
        for rule in ing['spec']['rules']:
            host = rule['host']
            if 'http' not in host:
                host = 'https://' + host
            urls_with_ingress.append(host + '/health')

    return urls_with_ingress

def check_endpoints(urls_with_ingress):
    # Check each endpoint that has an ingress and print the status.
    status_codes = {"200": [], "404": [], "other": []}

    for url in urls_with_ingress:
        # The -k flag is used with curl to proceed without certificate validation, replace it if needed.
        response = subprocess.Popen(['curl', '-k', '-s', '-o', '/dev/null', '-w', '%{http_code}', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        status_code, error = response.communicate()

        if error:
            print(f"Error fetching {url}: {error.decode()}")
            continue

        status_code = status_code.decode().strip()

        if status_code == "200":
            status_codes["200"].append(f"{url}: '{status_code}' - SSL Working Fine")
        elif status_code == "404":
            status_codes["404"].append(f"{ANSIColors.RED}{url}: '{status_code}' - Error 404 returned, please investigate{ANSIColors.ENDC}")
        else:
            status_codes["other"].append(f"{ANSIColors.RED}{url}: '{status_code}' - Unexpected status code returned{ANSIColors.ENDC}")

    for status, messages in status_codes.items():
        for message in messages:
            print(message)

def main():
    for cluster_info in CLUSTERS:
        if switch_context(cluster_info):
            urls_with_ingress = get_ingresses()
            if urls_with_ingress:
                check_endpoints(urls_with_ingress)
            else:
                print(f"No ingresses found in cluster: {cluster_info['name']}")
        else:
            print(f"Skipping checks for cluster: {cluster_info['name']}")

if __name__ == "__main__":
    main()
