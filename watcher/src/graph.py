import matplotlib.pyplot as plt
import quantity
import sys
import json


def generate_graph(POLL, ACTIVE, metrics_over_time, combined_over_time, bots_over_time):
    timestamps = [i["start_s"] for i in combined_over_time]
    start_ts = timestamps[0]
    x_axis = [i - start_ts for i in timestamps]

    y_axis = []
    web_latency = []
    web_cpu_utilization = []
    for slice in metrics_over_time:
        counts = 0
        for deployment in slice:
            counts += slice[deployment]["count"]
        y_axis.append(counts)
        web_latency.append(round(float(slice["web"]["latency"])))
        web_cpu_utilization.append(round(100 * float(slice["web"]["cpu"] /  float(quantity.parse_quantity("50m"))) / slice["web"]["count"]))
    
    desired_pods = []
    for slice in combined_over_time:
        desired = slice["desired"]
        count = 0
        for deployment in desired:
            count += desired[deployment]
        desired_pods.append(count)
       
    plt.title("Bot Counts (Load)")
    plt.plot(x_axis, bots_over_time, color="grey")
    plt.ylabel("Bot Count")
    plt.xlabel("Time (s)")
    plt.tight_layout()
    plt.savefig("/metrics/bot_counts.png")
    plt.close()


    fig, ax1 = plt.subplots()

    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Pod Count")
    ax1.plot(x_axis, y_axis, label="Pods", color="blue")
    ax1.plot(x_axis, desired_pods, label="Desired", color="purple")

    fig.legend(loc='upper left') 
    plt.title("Nodevoto Pods (desired) " + (" (HPA)" if not ACTIVE else ""))
    fig.tight_layout()
    plt.savefig("/metrics/desired_pods_over_time.png")
    plt.close()

    fig, ax1 = plt.subplots()

    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Pod Count")
    ax1.plot(x_axis, y_axis, label="Pods", color="blue")

    ax2 = ax1.twinx()
    ax2.set_ylabel("Web P95 Latency (ms)")
    ax2.plot(x_axis, web_latency, color="red", label="Latency")
    fig.legend(loc='upper left') 
    plt.title("Nodevoto Pods (Latency) " + (" (HPA)" if not ACTIVE else ""))
    fig.tight_layout()
    plt.savefig("/metrics/latency_pods_over_time.png")
    plt.close()


    fig, ax1 = plt.subplots()

    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Pod Count")
    ax1.plot(x_axis, y_axis, label="Pods", color="blue")

    ax2 = ax1.twinx()
    ax2.set_ylabel("Web CPU Utilization (%)")
    ax2.plot(x_axis, web_cpu_utilization, color="red", label="CPU")
    fig.legend(loc='upper left') 
    plt.title("Nodevoto Pods (CPU) " + (" (HPA)" if not ACTIVE else ""))
    fig.tight_layout()
    plt.savefig("/metrics/cpu_pods_over_time.png")
    plt.close()

if __name__ == "__main__":
    run_file_name = sys.argv[1]
    run_file = open(run_file_name)
    run = json.load(run_file)

    params_file_name = sys.argv[2]
    params_file = open(params_file_name)
    params = json.load(params_file)

    bots_over_time = [i["bots"]["votebot"]["count"] for i in run]
    metrics_over_time = [i["metrics"] for i in run]

    generate_graph(params["poll"], params["active"], metrics_over_time, run, bots_over_time)
