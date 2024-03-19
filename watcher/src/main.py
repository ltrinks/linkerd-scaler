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

ACTIVE = False # scale if true, watch only if false
POLL = 15 # seconds
RUNFOR = 60 # minutes

SCALE_FACTOR = 1 # how many bots to add each increase
MAX_PODS = 20 # max pods allowed for a deployment (bots and nodevoto)
INCREASES = 20 # number of times to increase before resetting
POLLS_PER_INCREASE = 10 # number of polls between each increase

# remove previous run
files = glob.glob('/metrics/*')
for f in files:
    os.remove(f)

f = open("/metrics/pods.txt", "w")

# load the config for the cluster to connect to the API
config.load_incluster_config()
appsApiClient = client.AppsV1Api()

i = 1
metrics_over_time = []
bots_over_time = []
combined_over_time = []

def generate_graph():
    x_axis = [i * POLL for i in range(len(metrics_over_time))]

    y_axis = []
    web_latency = []
    web_cpu_utilization = []
    for slice in metrics_over_time:
        counts = 0
        for deployment in slice:
            counts += slice[deployment]["count"]
        y_axis.append(counts)
        web_latency.append(round(float(slice["web"]["latency"])))
        web_cpu_utilization.append(round(100 * float(slice["web"]["cpu"] /  float(quantity.parse_quantity("100m"))) / slice["web"]["count"]))
    
    desired_pods = []
    for slice in combined_over_time:
        desired = slice["desired"]
        count = 0
        for deployment in desired:
            count += desired[deployment]
        desired_pods.append(count)
       


    fig, ax1 = plt.subplots()

    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Pod Count")
    ax1.plot(x_axis, y_axis, label="Pods", color="blue")
    ax1.plot(x_axis, bots_over_time, label="Bots", color="grey")
    ax1.plot(x_axis, desired_pods, label="Desired", color="purple")

    fig.legend(loc='upper left') 
    plt.title("Nodevoto Pods vs Bots (desired) " + (" (HPA)" if not ACTIVE else ""))
    fig.tight_layout()
    plt.savefig("/metrics/desired_pods_over_time.png")
    plt.close()

    fig, ax1 = plt.subplots()

    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Pod Count")
    ax1.plot(x_axis, y_axis, label="Pods", color="blue")
    ax1.plot(x_axis, bots_over_time, label="Bots", color="grey")

    ax2 = ax1.twinx()
    ax2.set_ylabel("Web P95 Latency (ms)")
    ax2.plot(x_axis, web_latency, color="red", label="Latency")
    fig.legend(loc='upper left') 
    plt.title("Nodevoto Pods vs Bots over Time (Latency) " + (" (HPA)" if not ACTIVE else ""))
    fig.tight_layout()
    plt.savefig("/metrics/latency_pods_over_time.png")
    plt.close()


    fig, ax1 = plt.subplots()

    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Pod Count")
    ax1.plot(x_axis, y_axis, label="Pods", color="blue")
    ax1.plot(x_axis, bots_over_time, label="Bots", color="grey")

    ax2 = ax1.twinx()
    ax2.set_ylabel("Web CPU Utilization (%)")
    ax2.plot(x_axis, web_cpu_utilization, color="red", label="CPU")
    fig.legend(loc='upper left') 
    plt.title("Nodevoto Pods vs Bots over Time (CPU) " + (" (HPA)" if not ACTIVE else ""))
    fig.tight_layout()
    plt.savefig("/metrics/cpu_pods_over_time.png")
    plt.close()

# for specified time, get metrics, and adjust scale if needed
while i * POLL <= RUNFOR * 60:
    try:
        raw = open("/metrics/raw.txt", "w")
        if (i % POLLS_PER_INCREASE == 0):
            print(f"{((i * POLL) / (RUNFOR * 60)) * 100}%")
            appsApiClient.patch_namespaced_deployment_scale("vote-bot", "nodevoto-bot",{'spec': {'replicas': (SCALE_FACTOR * (i % (POLLS_PER_INCREASE * (INCREASES + 1))) // POLLS_PER_INCREASE)}, "maxReplicas": MAX_PODS})
            f.write(f"Scaling bot to {(SCALE_FACTOR * (i % (POLLS_PER_INCREASE * (INCREASES + 1))) // POLLS_PER_INCREASE)}\n")

        f.write("Checking pods " + str(time.ctime()) + "\n")
        namespace_metrics = metrics.getResourceMetrics("nodevoto")

        raw.write(str(namespace_metrics))
        raw.close()

        bot_count = 0
        bots = metrics.getResourceMetricsNoLinkerd("nodevoto-bot")
        if ("votebot" in bots):
            bot_count = bots["votebot"]["count"]
        bots_over_time.append(bot_count)

        f.write("deployment | cpu | target cpu | count | desired count\n")
        desired_state = {}
        target_cpu = float(quantity.parse_quantity("30m"))
        for deployment, value in namespace_metrics.items():
            desired = math.ceil(value["cpu"] / target_cpu)
            desired_state[deployment] = desired
            f.write(deployment + " | " + str(value["cpu"]) + " | " + str(target_cpu) + " | " + str(value["count"]) + " | " + str(desired) + " ")
            if (ACTIVE and value["count"] != desired):
                appsApiClient.patch_namespaced_deployment_scale(deployment, "nodevoto",{'spec': {'replicas': desired, "maxReplicas": MAX_PODS}})
                f.write("SCALING")
            elif (not ACTIVE):
               desired_state[deployment] = appsApiClient.read_namespaced_deployment_status(deployment, "nodevoto").spec.replicas
            f.write("\n")

        metrics_over_time.append(namespace_metrics)
        combined = {"bots": bots, "metrics": namespace_metrics, "desired": desired_state}
        combined_over_time.append(combined)
        f.write("\n")
        f.flush()
    except Exception as err:
        print(f"ERROR during {i}: " + str(err))

    i += 1
    time.sleep(POLL)

generate_graph()
print("Run finished")
run_file = open("/metrics/run.json", "w")
json.dump(combined_over_time, run_file, indent="\t")
run_file.close()

while True:
    time.sleep(POLL)

