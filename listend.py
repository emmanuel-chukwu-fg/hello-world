import subprocess
import json

CLUSTERS = [
    {"name": "non-prod-buying", "project": "xxxxxx", "context": ""},
    # Add other clusters here...
]

def switch_context(cluster_info):
    context = cluster_info['context']
    cmd = ['kubectl', 'config', 'use-context', context]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if proc.returncode != 0:
        print(f"Error switching to context {context}: {err.decode('utf-8')}")
        return False

    print(f"Switched to context {context}")
    return True

def get_ingress_endpoints():
    cmd = ['kubectl', 'get', 'ing', '-o', 'json']
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if proc.returncode != 0:
        print(f"Error getting ingresses: {err.decode('utf-8')}")
        return None

    ingresses = json.loads(out.decode('utf-8'))
    endpoints = []

    for item in ingresses['items']:
        # Assuming the first rule hosts the service endpoint
        try:
            rules = item['spec']['rules']
            for rule in rules:
                host = rule['host']
                if host.startswith('http://'):
                    continue  # Ignore non-HTTPS URLs
                https_url = f"https://{host}/health"
                endpoints.append(https_url)
        except KeyError:
            continue  # Ingress might not have a 'rules' field

    return endpoints

def check_endpoint_health(endpoint):
    cmd = ['curl', '-o', '/dev/null', '-s', '-w', '%{http_code}', '--insecure', endpoint]  # '--insecure' for SSL issues
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = proc.communicate()

    if proc.returncode != 0:
        print(f"Error curling {endpoint}: {err.strip()}")  # Print the error message from curl
        return "Error"  # You can return a more descriptive error message if needed

    return out.strip()

def main():
    for cluster in CLUSTERS:
        success = switch_context(cluster)
        if not success:
            continue

        print(f"Checking endpoints for cluster {cluster['name']}...")
        endpoints = get_ingress_endpoints()
        if endpoints is None:
            continue

        for endpoint in endpoints:
            status = check_endpoint_health(endpoint)
            print(f'"{endpoint}": "{status}"')

if __name__ == "__main__":
    main()
