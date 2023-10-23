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

def get_ingresses():
    cmd = ['kubectl', 'get', 'ing', '-o', 'json', '--all-namespaces']
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if proc.returncode != 0:
        print(f"Error fetching ingresses: {err.decode('utf-8')}")
        return []

    ingresses = json.loads(out.decode('utf-8'))
    return ingresses['items']

def check_url(url):
    cmd = f"curl -s -o /dev/null -w '%{{http_code}}' {url}"
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if proc.returncode != 0:
        print(f"Error checking {url}: {err.decode('utf-8')}")
        return None

    return out.decode('utf-8').strip()

def categorize_endpoints(endpoints):
    status_200, status_404, no_ingress, unexpected = [], [], [], []

    for endpoint in endpoints:
        status_code = check_url(endpoint + "/health")
        if status_code == '200':
            status_200.append(endpoint)
        elif status_code == '404':
            if 'no-ingress' in endpoint:
                no_ingress.append(endpoint)
            else:
                status_404.append(endpoint)
        else:
            unexpected.append((endpoint, status_code))

    return status_200, status_404, no_ingress, unexpected

def main():
    for cluster in CLUSTERS:
        print(f"Switching context to: {cluster}")
        if not switch_context(cluster):
            continue

        print("Fetching ingresses...")
        ingresses = get_ingresses()

        endpoints = []
        for ingress in ingresses:
            annotations = ingress['metadata'].get('annotations', {})
            if 'nginx.ingress.kubernetes.io/rewrite-target' in annotations:
                continue  # Skip ingresses with rewrite-target

            rules = ingress['spec'].get('rules', [])
            for rule in rules:
                host = rule.get('host', '')
                if host:
                    endpoints.append(f"http://{host}")

        status_200, status_404, no_ingress, unexpected = categorize_endpoints(endpoints)

        print("Results:")
        print("200 SSL working fine:")
        for endpoint in status_200:
            print(endpoint)

        print("404 Error, please investigate:")
        for endpoint in status_404:
            print(endpoint)

        print("Internal apps, no ingress found:")
        for endpoint in no_ingress:
            print(endpoint)

        print("Unexpected status code returned:")
        for endpoint, status_code in unexpected:
            print(f"{endpoint}: {status_code}")

if __name__ == "__main__":
    main()
