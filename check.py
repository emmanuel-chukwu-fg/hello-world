import subprocess
import json
import sys

# Define your clusters with relevant details.
CLUSTERS = [
    {"name": "non-prod-buying", "project": "project1", "context": "context1"},
    # ... other clusters ...
]

# ANSI escape codes for coloring text.
class ANSIColors:
    RED = '\033[91m'
    ENDC = '\033[0m'
    GREEN = '\033[92m'
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
        return []

    ingresses = json.loads(out.decode())['items']
    apps_with_ingress = []

    # Assuming 'app' label holds the application name
    for ing in ingresses:
        try:
            app_name = ing['metadata']['labels']['app']
            rules = ing['spec']['rules']
            if rules:
                for rule in rules:
                    host = rule['host']
                    if 'http' not in host:
                        host = 'https://' + host
                    apps_with_ingress.append({"app": app_name, "url": host + '/health', "has_ingress": True})
            else:
                apps_with_ingress.append({"app": app_name, "url": None, "has_ingress": False})
        except KeyError:
            continue  # Handle the case where expected fields are not found

    return apps_with_ingress

def check_endpoints(apps):
    # Check each endpoint and categorize the output based on status codes or ingress availability.
    status_codes = {"200": [], "404": [], "no_ingress": [], "other": []}

    for app in apps:
        url = app["url"]
        if app["has_ingress"]:
            response = subprocess.Popen(['curl', '-k', '-s', '-o', '/dev/null', '-w', '%{http_code}', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            status_code, error = response.communicate()

            if error:
                print(f"Error fetching {url}: {error.decode()}")
                continue

            status_code = status_code.decode().strip()

            if status_code == "200":
                status_codes["200"].append(f"{ANSIColors.GREEN}{url}: '{status_code}' - SSL Working Fine{ANSIColors.ENDC}")
            elif status_code == "404":
                status_codes["404"].append(f"{ANSIColors.RED}{url}: '{status_code}' - Error 404 returned, please investigate{ANSIColors.ENDC}")
            else:
                status_codes["other"].append(f"{ANSIColors.RED}{url}: '{status_code}' - Unexpected status code returned{ANSIColors.ENDC}")
        else:
            status_codes["no_ingress"].append(f"{ANSIColors.RED}No ingress found for app: {app['app']}{ANSIColors.ENDC}")

    return status_codes

def main():
    all_status_codes = {"200": [], "404": [], "no_ingress": [], "other": []}

    for cluster_info in CLUSTERS:
        if switch_context(cluster_info):
            apps = get_ingresses()
            status_codes = check_endpoints(apps)

            for status in all_status_codes.keys():
                all_status_codes[status].extend(status_codes[status])
        else:
            print(f"Skipping checks for cluster: {cluster_info['name']}")

    # Printing all results after checks have been completed for all clusters
    for status, messages in all_status_codes.items():
        if messages:
            print(f"\nResults for status code: {status}")
            for message in messages:
                print(message)

if __name__ == "__main__":
    main()
