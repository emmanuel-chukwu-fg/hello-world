import subprocess
import json
from urllib.parse import urlparse

# ANSI escape sequences for colored output
class ANSIColors:
    RED = '\033[31m'
    GREEN = '\033[32m'
    ENDC = '\033[0m'

# Define your clusters here
CLUSTERS = [
    {"name": "non-prod-buying", "project": "xxxxxx", "context": ""},
    # Add other clusters...
]

def switch_context(cluster_info):
    print(f"Switching context to: {cluster_info}")  # Debugging print
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
    print("Fetching ingresses...")  # Debugging print
    cmd = ['kubectl', 'get', 'ingresses', '-o', 'json']
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if proc.returncode != 0:
        print(f"Error fetching ingresses: {err.decode()}")
        return None

    ingresses = json.loads(out.decode())
    print(f"Fetched ingresses: {ingresses}")  # Debugging print
    return ingresses

def ingress_exists(host, ingresses):
    print(f"Checking if ingress exists for host: {host}")  # Debugging print
    for ingress in ingresses['items']:
        for rule in ingress.get('spec', {}).get('rules', []):
            if host == rule.get('host'):
                print(f"Found matching ingress for host: {host}")  # Debugging print
                return True
    print(f"No ingress found for host: {host}")  # Debugging print
    return False

def check_endpoint(url, ingresses):
    print(f"Checking URL: {url}")  # Debugging print
    host = urlparse(url).netloc
    cmd = ['curl', '-ks', '-o', '/dev/null', '-w', '%{http_code}', url]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if proc.returncode != 0:
        print(f"Error checking {url}: {err.decode()}")
        return None

    status_code = out.decode().strip()
    print(f"Status code for {url}: {status_code}")  # Debugging print

    # Handle response based on status code
    if status_code == "200":
        return f"{ANSIColors.GREEN}{url}: '200' - SSL Working Fine{ANSIColors.ENDC}"
    elif status_code == "404":
        if ingress_exists(host, ingresses):
            return f"{ANSIColors.RED}{url}: '404' - Error 404 returned, please investigate{ANSIColors.ENDC}"
        else:
            return f"{url}: '404' - Appname is an internal app, no ingress found"
    else:
        return f"{ANSIColors.RED}{url}: '{status_code}' - Unexpected status code returned{ANSIColors.ENDC}"

def main():
    print("Script started...")  # Debugging print
    for cluster_info in CLUSTERS:
        if switch_context(cluster_info):
            ingresses = get_ingresses()
            if ingresses:
                urls = []  # populate this with the URLs you want to check
                for ingress in ingresses['items']:
                    for rule in ingress.get('spec', {}).get('rules', []):
                        host = rule.get('host')
                        if host:  # assuming http for simplicity, adjust as needed
                            urls.append(f"http://{host}/health")

                for url in urls:
                    result = check_endpoint(url, ingresses)
                    if result:
                        print(result)
            else:
                print(f"{ANSIColors.RED}No ingresses found in the cluster: {cluster_info['name']}{ANSIColors.ENDC}")
        else:
            print(f"Skipping checks for cluster: {cluster_info['name']}")

    print("Script execution finished.")  # Debugging print

if __name__ == "__main__":
    main()
