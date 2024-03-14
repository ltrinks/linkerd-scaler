from kubernetes import client, config, watch
import matplotlib.pyplot as plt

import glob
import os
import time
import pprint
import metrics
import quantity
import math

ACTIVE = True # scale if true, watch only if false
POLL = 3 # seconds
RUNFOR = 15 # minutes

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

def generate_graph():
    x_axis = [i * POLL for i in range(len(metrics_over_time))]

    y_axis = []
    web_latency = []
    for slice in metrics_over_time:
        counts = 0
        for deployment in slice:
            counts += slice[deployment]["count"]
        y_axis.append(counts)
        web_latency.append(round(float(slice["web"]["latency"])))

    plt.title("Nodevoto Pods vs Bots over Time" + (" (HPA)" if not ACTIVE else ""))
    plt.xlabel(f"Time (s)")
    plt.ylabel("Pod Count")
    plt.plot(x_axis, y_axis, label="Pods", color="blue")
    plt.plot(x_axis, bots_over_time, label="Bots", color="grey")
    plt.plot(x_axis, web_latency, color="red")
    plt.legend(loc='upper left')
    plt.savefig("/metrics/pods_over_time.png")
    plt.close()

# for specified time, get metrics, and adjust scale if needed
while i * POLL <= RUNFOR * 60:
    try:
        raw = open("/metrics/raw.txt", "w")
        if (i % 10 == 0):
            appsApiClient.patch_namespaced_deployment_scale("vote-bot", "nodevoto-bot",{'spec': {'replicas': (i % 100) // 10}, "maxReplicas": 10})
            f.write(f"Scaling bot to {(i % 100) // 10}\n")
            generate_graph()

        f.write("Checking pods " + str(time.ctime()) + "\n")
        namespace_metrics = metrics.getResourceMetrics("nodevoto")
        metrics_over_time.append(namespace_metrics)

        raw.write(str(namespace_metrics))
        raw.close()

        bot_count = 0
        bots = metrics.getResourceMetricsNoLinkerd("nodevoto-bot")
        if ("votebot" in bots):
            bot_count = bots["votebot"]["count"]
        bots_over_time.append(bot_count)

        f.write("deployment | cpu | target cpu | count | desired count\n")

        target_cpu = float(quantity.parse_quantity("30m"))
        for deployment, value in namespace_metrics.items():
            desired = math.ceil(value["cpu"] / target_cpu)
            f.write(deployment + " | " + str(value["cpu"]) + " | " + str(target_cpu) + " | " + str(value["count"]) + " | " + str(desired) + " ")
            if (ACTIVE and value["count"] != desired):
                appsApiClient.patch_namespaced_deployment_scale(deployment, "nodevoto",{'spec': {'replicas': desired, "maxReplicas": 10}})
                f.write("SCALING")
            f.write("\n")
        f.write("\n")
        f.flush()
    except Exception as err:
        print(f"ERROR during {i}: " + str(err))

    i += 1
    time.sleep(POLL)

print("Run finished")

while True:
    time.sleep(POLL)
