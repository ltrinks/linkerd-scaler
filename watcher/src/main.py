from kubernetes import client, config, watch
import matplotlib.pyplot as plt

import glob
import os
import time
import pprint
import metrics
import quantity
import math
import json
import pandas as pd
import graph
import requests

ACTIVE = False # scale if true, watch only if false
POLL = 15 # seconds
RUNFOR = 44 # minutes

SCALE_FACTOR = 3 # how many bots to add each increase
MAX_PODS = 10 # max pods allowed for a deployment (bots and nodevoto)
INCREASES = 10 # number of times to increase before resetting
POLLS_PER_INCREASE = 15 # number of polls between each increase
TARGET = "300m" # CPU target metric, to update for HPA see nodevoto-hpa.yaml
LIMIT = "500m"

# remove previous run
files = glob.glob('/metrics/*')
for f in files:
    os.remove(f)

# load the config for the cluster to connect to the API
config.load_incluster_config()
appsApiClient = client.AppsV1Api()

# TODO collapse all into just combined over time
i = 1
metrics_over_time = []
bots_over_time = []
combined_over_time = []
gradual_change_over_time = {}

# for specified time, get metrics, and adjust scale if needed
for port in range(3001, 3002):
    requests.post(f"http://172.16.118.182:{port}", data = {"rps": 1})
    time.sleep(0.05)
rps = 1
while i * POLL <= RUNFOR * 60:
    try:
        # if an increase poll scale bots
        if (i % POLLS_PER_INCREASE == 0):
            print(f"{((i * POLL) / (RUNFOR * 60)) * 100}%")
            rps = SCALE_FACTOR * (i % (POLLS_PER_INCREASE * (INCREASES + 1))) // POLLS_PER_INCREASE
            for port in range(3001, 3002):
                requests.post(f"http://172.16.118.182:{port}", data = {"rps": ((SCALE_FACTOR * (i % (POLLS_PER_INCREASE * (INCREASES + 1))) // POLLS_PER_INCREASE)) // 2})

        # get CPU, latency, counts, for targeted namespace
        start_timestamp = time.time()
        start_ns = time.monotonic_ns()
        namespace_metrics = metrics.getResourceMetrics("default")
        end_ns = time.monotonic_ns()
        poll_time = end_ns - start_ns

        # save the set requests per second on gNBSim
        bots_over_time.append(rps)

        # for each deployment, determine desired vaue and scale if needed
        desired_state = {}
        target_cpu = float(quantity.parse_quantity(TARGET))
        for deployment, value in namespace_metrics.items():
            if not deployment in gradual_change_over_time:
                gradual_change_over_time[deployment] = []

            # smooth out the change using the last data point, only allow a 5% change of the target metric
            current_cpu = value["cpu"]

            previous_data = gradual_change_over_time[deployment][-2:]
            previous_data.append(current_cpu)
            gradual_change = []
            for idx, usage in enumerate(previous_data):
                if idx == 0:
                    gradual_change.append(usage)
                    continue
                
                prev = gradual_change[-1]
                change = usage - prev
                percent_change = abs(change) / (prev + 0.0000001)
                if abs(change) > 0.05 * target_cpu:
                    direction = 1
                    if change < 0:
                        direction = -1
                    gradual_change.append(prev + (direction * 0.05 * target_cpu))
                    continue
                gradual_change.append(usage)

            gradual_change_over_time[deployment].append(gradual_change[-1])

            value["gradual_cpu"] = gradual_change[-1]

            # based on https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/#algorithm-details
            desired = max(math.ceil(gradual_change[-1] / target_cpu), 1)
            desired_state[deployment] = desired

            # if active and a change desired, request the change
            if (ACTIVE and value["count"] != desired):
                print(f"scaling {deployment}")
                appsApiClient.patch_namespaced_deployment_scale(deployment, "default",{'spec': {'replicas': desired, "maxReplicas": MAX_PODS}})

            # if not active, we are not controlling desired, fetch it from the deployment spec
            elif (not ACTIVE):
               desired_state[deployment] = appsApiClient.read_namespaced_deployment_status(deployment, "default").spec.replicas

        metrics_over_time.append(namespace_metrics)
        combined = {"metrics": namespace_metrics, "desired": desired_state, "start_s": start_timestamp, "took_ns": poll_time}
        combined_over_time.append(combined)
    except Exception as err:
        print(f"ERROR during {i}: " + str(err))

    i += 1
    time.sleep(POLL)

# lessen the traffic
requests.post("http://172.16.118.182:3001", data = {"rps": 1})

# save the run file
run_file = open("/metrics/run.json", "w")
json.dump(combined_over_time, run_file, indent="\t")
run_file.close()

params_file = open("/metrics/parameters.json", "w")
json.dump({"active": ACTIVE, 
           "poll": POLL, 
           "run_for": RUNFOR, 
           "scale_factor": SCALE_FACTOR, 
           "max_pods": MAX_PODS, 
           "increases": INCREASES, 
           "polls_per_increase": POLLS_PER_INCREASE,
            "target": TARGET,
            "limit": LIMIT}, params_file, indent="\t")
params_file.close()

# generate graphs
graph.generate_graph(POLL, ACTIVE, metrics_over_time, combined_over_time, bots_over_time)
print("Run finished")

# wait forever to avoid restart of the watcher pod
while True:
    time.sleep(POLL)
