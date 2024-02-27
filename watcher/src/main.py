from kubernetes import client, config, watch
import requests
import glob
import os
import time

# remove previous run
files = glob.glob('/metrics/*')
for f in files:
    os.remove(f)

# load the config for the cluster to connect to the API
config.load_incluster_config()

# clients for namespaces and apps
v1 = client.CoreV1Api()
apiClient = client.AppsV1Api()

f = open("/metrics/pods.txt", "w")

# scale the nodevoto web pod to 2 replicas
f.write(str(apiClient.patch_namespaced_deployment_scale(
   "web", "nodevoto",
   {'spec': {'replicas': 2}})) + "\n\n")

# for forever, identify running pods in the nodevoto namespace and get prometheus reports
while True:
    print("Checking pods " + str(time.time()))
    for i in v1.list_namespaced_pod("nodevoto").items:
        f.write("%s\t%s\t%s\n\n" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
        pod_file = open("/metrics/%s.txt" % i.metadata.name, "w")
        pod_file.write(requests.get("http://%s:4191/metrics" % i.status.pod_ip).content.decode())
        pod_file.close()
        f.flush()
    time.sleep(15)
