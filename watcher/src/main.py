from kubernetes import client, config, watch
import requests
import glob
import os
import time
from prometheus_client import CollectorRegistry, Gauge, write_to_textfile

# remove previous run
files = glob.glob('/metrics/*')
for f in files:
    os.remove(f)

# load the config for the cluster to connect to the API
config.load_incluster_config()

# clients for namespaces and apps
coreApiClient = client.CoreV1Api()
appsApiClient = client.AppsV1Api()
topApiClient = client.CustomObjectsApi()

f = open("/metrics/pods.txt", "w")

# scale the nodevoto web pod to 2 replicas
f.write(str(appsApiClient.patch_namespaced_deployment_scale(
   "web", "nodevoto",
   {'spec': {'replicas': 2}})) + "\n\n")

# for forever, get CPU and memory of the pods, get the IP addresses of the pods, get prometheus reports
while True:
    print("Checking pods " + str(time.time()))
    f.write(str(topApiClient.list_namespaced_custom_object("metrics.k8s.io", "v1beta1", "nodevoto", "pods")) + "\n")
    for i in coreApiClient.list_namespaced_pod("nodevoto").items:
        f.write("%s\t%s\t%s\n" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
        pod_file = open("/metrics/%s.txt" % i.metadata.name, "w")
        pod_file.write(requests.get("http://%s:4191/metrics" % i.status.pod_ip).content.decode())
        pod_file.close()
    f.write("\n\n")
    f.flush()
    time.sleep(15)
