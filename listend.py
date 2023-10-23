import subprocess
import json

CLUSTERS = [
    {"name": "non-prod-buying", "project": "xxxxxx", "context": "your-context-name"},
    # Add other clusters here with their respective context names...
]

def switch_context(cluster_info):
    context = cluster_info['context']
    cmd = ['kubectl', 'config', 'use-context', context]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Switched to context {context}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error switching to context {context}: {e.stderr}")
        return False

def get_endpoints():
    cmd = ['kubectl', 'get', 'ing', '--all-namespaces', '-o', 'json']
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        ingress_data = json.loads(result.stdout)
        endpoints = []

        for item in ingress_data['items']:
            if 'tls' in item['spec']:  # Ensure that TLS is enabled, implying HTTPS is used
                try:
                    host = item['spec']['rules'][0]['host']
                    endpoints.append(f"https://{host}/health")  # Only gather https URLs
                except (KeyError, IndexError):
                    continue  # Skip ingresses without the necessary structure

        return endpoints
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving ingresses: {e.stderr}")
        return []

def check_endpoint_health(endpoint):
    cmd = ['curl', '-o', '/dev/null', '-s', '-w', '%{http_code}', '--insecure', endpoint]  # '--insecure' is used if you're okay with ignoring SSL certificate verification
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"  # Returning stderr to understand the error during the request

def main():
    for cluster in CLUSTERS:
        if switch_context(cluster):
            endpoints = get_endpoints()
            for endpoint in endpoints:
                status_code = check_endpoint_health(endpoint)
                print(f'"{endpoint}": "{status_code}"')

if __name__ == "__main__":
    main()
