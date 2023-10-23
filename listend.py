import subprocess
import json

CLUSTERS = [
    {"name": "non-prod-buying", "project": "xxxxxx", "context": ""},
    # Add other clusters here with their respective context
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

def get_ingresses():
    try:
        ingress_raw = subprocess.check_output(["kubectl", "get", "ingresses", "--all-namespaces", "-o=json"], text=True)
        ingress_json = json.loads(ingress_raw)
        return ingress_json['items']
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while retrieving ingresses: {str(e)}")
        return []
    except json.JSONDecodeError as e:
        print(f"An error occurred while parsing JSON: {str(e)}")
        return []

def main():
    if not CLUSTERS:
        print("No clusters defined.")
        return

    for cluster in CLUSTERS:
        if not cluster['context']:
            print(f"Context for cluster {cluster['name']} is not defined. Skipping...")
            continue
        if switch_context(cluster):
            print(f"Fetching ingresses for cluster: {cluster['name']}")
            ingresses = get_ingresses()
            for ingress in ingresses:
                namespace = ingress['metadata']['namespace']
                name = ingress['metadata']['name']
                for rule in ingress['spec']['rules']:
                    host = rule['host']
                    print(f"- namespace: {namespace}, name: {name}, host: {host}")

if __name__ == '__main__':
    main()
