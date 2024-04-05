import matplotlib.pyplot as plt
import quantity


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