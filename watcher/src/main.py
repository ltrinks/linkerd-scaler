from kubernetes import client, config, watch

import glob
import os
import time
import pprint
import metrics
import quantity
import math


# remove previous run
files = glob.glob('/metrics/*')
for f in files:
    os.remove(f)

f = open("/metrics/pods.txt", "w")

# load the config for the cluster to connect to the API
config.load_incluster_config()
appsApiClient = client.AppsV1Api()

i = 1

# for forever, get metrics, and adjust scale if needed
while True:
    if (i % 30 == 0):
        appsApiClient.patch_namespaced_deployment_scale("vote-bot", "nodevoto-bot",{'spec': {'replicas': 1}})
        f.write("Scaling bot to 1\n")

    elif (i % 10 == 0):
        appsApiClient.patch_namespaced_deployment_scale("vote-bot", "nodevoto-bot",{'spec': {'replicas': 10}})
        f.write("Scaling bot to 10\n")

    f.write("Checking pods " + str(time.time()) + "\n")
    namespace_metrics = metrics.getResourceMetrics("nodevoto")
    f.write("deployment | cpu | target cpu | count | desired count\n")

    target_cpu = float(quantity.parse_quantity("15m"))
    for deployment, value in namespace_metrics.items():
        desired = math.ceil(value["cpu"] / target_cpu)
        f.write(deployment + " | " + str(value["cpu"]) + " | " + str(target_cpu) + " | " + str(value["count"]) + " | " + str(desired) + " ")
        if (value["count"] != desired):
            appsApiClient.patch_namespaced_deployment_scale(deployment, "nodevoto",{'spec': {'replicas': desired}})
            f.write("SCALING")
        f.write("\n")
    f.write("\n")
    f.flush()
    i += 1
    time.sleep(3)
