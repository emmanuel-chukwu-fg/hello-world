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
    GREEN = '\033[92m'

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
    urls = []

    for ing in ingresses:
        rules = ing.get('spec', {}).get('rules', [])
        for rule in rules:
            host = rule.get('host', '')
            if host:
                url = f"https://{host}/health"
                urls.append(url)
    
    return urls

def check_endpoints(urls):
    # Initialize the results dictionary.
    results = {
        "200": [],
        "404": [],
        "no_ingress": [],
        "other": []
    }

    for url in urls:
        response = subprocess.Popen(['curl', '-k', '-s', '-o', '/dev/null', '-w', '%{http_code}', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        status_code, error = response.communicate()

        if error:
            print(f"Error fetching {url}: {error.decode()}")
            continue

        status_code = status_code.decode().strip()

        # Classify the result based on the status_code.
        if status_code == "200":
            results["200"].append(f"{url}: '200' - SSL Working Fine")
        elif status_code == "404":
            # We'll check if this 404 is due to no ingress or an actual 404 from the server.
            if "no ingress" in url:  # Placeholder condition, replace with actual check for ingress presence.
                results["no_ingress"].append(f"{ANSIColors.RED}{url}: '404' - No ingress found{ANSIColors.ENDC}")
            else:
                results["404"].append(f"{ANSIColors.RED}{url}: '404' - Error 404 returned, please investigate{ANSIColors.ENDC}")
        else:
            results["other"].append(f"{ANSIColors.RED}{url}: '{status_code}' - Unexpected status code returned{ANSIColors.ENDC}")

    return results

def main():
    for cluster_info in CLUSTERS:
        if switch_context(cluster_info):
            urls = get_ingresses()
            if urls:
                results = check_endpoints(urls)
                print_results(results)
            else:
                print(f"{ANSIColors.RED}No ingress found in cluster: {cluster_info['name']}{ANSIColors.ENDC}")
        else:
            print(f"Skipping checks for cluster: {cluster_info['name']}")

def print_results(results):
    # Print the results grouped by status code.
    for status_code, messages in results.items():
        if messages:  # Only print if there are messages for this status code.
            print(f"\nResults for status code: {status_code}")
            for message in messages:
                print(message)

if __name__ == "__main__":
    main()
