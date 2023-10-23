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

def get_services():
    services = []
    cmd = ['kubectl', 'get', 'svc', '--all-namespaces', '-o', 'json']
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if proc.returncode == 0:
        services_json = json.loads(out.decode('utf-8'))
        for service in services_json['items']:
            try:
                app_name = service['metadata']['labels']['app']
                ingress = service['spec']['ports'][0]['nodePort']
                services.append((app_name, ingress))
            except (KeyError, IndexError):
                # Ignoring services that do not match the expected structure
                pass
    else:
        print(f"Error retrieving services: {err.decode('utf-8')}")

    return services

def curl_endpoint(endpoint):
    try:
        response = subprocess.check_output(["curl", "-o", "/dev/null", "-Is", "-w", "%{http_code}", endpoint], text=True)
        print(f'"{endpoint}" : "{response.strip()}"')
    except subprocess.CalledProcessError as e:
        print(f'An error occurred while curling {endpoint}: {str(e)}')

def main():
    for cluster in CLUSTERS:
        if switch_context(cluster):
            services = get_services()
            for service in services:
                app_name, ingress = service
                url = f"https://{app_name}.your-cluster-domain.com:{ingress}/health"
                curl_endpoint(url)

if __name__ == "__main__":
    main()
