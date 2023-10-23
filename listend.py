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

def get_deployments():
    try:
        deployments_raw = subprocess.check_output(["kubectl", "get", "deployments", "--all-namespaces", "-o=json"], text=True)
        deployments_json = json.loads(deployments_raw)
        return deployments_json['items']
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while retrieving deployments: {str(e)}")
        return []
    except json.JSONDecodeError as e:
        print(f"An error occurred while parsing JSON: {str(e)}")
        return []

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
            print(f"Fetching applications and ingresses for cluster: {cluster['name']}")
            ingresses = get_ingresses()
            apps_with_ingress = set()
            for ingress in ingresses:
                app_name = ingress['metadata']['name']
                apps_with_ingress.add(app_name)
                for rule in ingress['spec']['rules']:
                    host = rule['host']
                    print(f"App with Ingress: {app_name}, Endpoint: {host}")

            deployments = get_deployments()
            all_apps = set(deployment['metadata']['name'] for deployment in deployments)
            apps_without_ingress = all_apps - apps_with_ingress

            print("\nApps without Ingress:")
            for app in apps_without_ingress:
                print(app)

if __name__ == '__main__':
    main()
