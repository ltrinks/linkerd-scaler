from kubernetes import client, config, watch
import matplotlib.pyplot as plt

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

while True:
    try:
        res_metrics = metrics.getResourceMetrics("nodevoto")
        f.write(str(res_metrics))
        f.write("\n\n")
        f.flush()
        time.sleep(5)
    except Exception as e:
        print("error " + str(e))

