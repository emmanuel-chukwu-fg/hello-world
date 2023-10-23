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
    cmd = ['kubectl', 'get', 'ing', '-o', 'json']
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if proc.returncode != 0:
        print(f"Error getting ingresses: {err.decode('utf-8')}")
        return []

    ingresses = json.loads(out.decode('utf-8'))
    return ingresses['items']

def check_endpoint_health(endpoint):
    cmd = ['curl', '-o', '/dev/null', '-s', '-w', '%{http_code}', '--insecure', endpoint]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = proc.communicate()

    if proc.returncode != 0:
        return f"Error: {err.strip()}"

    return out.strip()

def main():
    for cluster in CLUSTERS:
        if not switch_context(cluster):
            continue  # if switching context fails, continue to next cluster

        ingresses = get_ingresses()
        for ing in ingresses:
            annotations = ing['metadata'].get('annotations', {})
            if 'nginx.ingress.kubernetes.io/rewrite-target' in annotations:
                continue  # skip ingresses that have a rewrite-target

            for rule in ing['spec']['rules']:
                host = rule['host']
                for path in rule.get('http', {}).get('paths', []):
                    path_val = path['path']
                    path_val = path_val if path_val.endswith('/') else path_val + '/'
                    url = f"https://{host}{path_val}health"  # construct the URL

                    if url.startswith('https://'):
                        status = check_endpoint_health(url)
                        print(f'"{url}": "{status}"')

if __name__ == "__main__":
    main()

PS C:\Users\echukwu\OneDrive - Frasers Group\Desktop\ProjectFiles> & C:/Users/echukwu/AppData/Local/Programs/Python/Python311/python.exe "c:/Users/echukwu/OneDrive - Frasers Group/Desktop/ProjectFiles/scripts/python/exception.py"
Switched to context connectgateway_corp-test-mgmt-anthos-3578_global_non-prod-warehouse
"https://apache-test-f5.anthos.sportski.com/health": "Error: "
