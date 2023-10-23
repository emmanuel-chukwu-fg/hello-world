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

def get_all_ingresses():
    try:
        ingresses_raw = subprocess.check_output(["kubectl", "get", "ingresses", "--all-namespaces", "-o=json"], text=True)
        ingresses_json = json.loads(ingresses_raw)
        return ingresses_json['items']
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while retrieving ingresses: {str(e)}")
        return []
    except json.JSONDecodeError as e:
        print(f"An error occurred while parsing JSON: {str(e)}")
        return []

def curl_endpoint(endpoint):
    try:
        response = subprocess.check_output(["curl", "-Is", endpoint], text=True)
        print(f"Response from {endpoint}:")
        print(response)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while curling {endpoint}: {str(e)}")

def main():
    for cluster in CLUSTERS:
        if not cluster['context']:
            print(f"Context for cluster {cluster['name']} is not defined. Skipping...")
            continue
        if switch_context(cluster):
            print(f"Fetching ingresses for cluster: {cluster['name']}")

            ingresses = get_all_ingresses()
            for ingress in ingresses:
                for rule in ingress.get('spec', {}).get('rules', []):
                    host = rule.get('host', '')
                    if host:
                        print(f"Curling: {host}")
                        curl_endpoint(f"http://{host}")  # Assumes HTTP. Change to 'https://' if endpoints are HTTPS.

if __name__ == '__main__':
    main()
