from kubernetes import client, config, watch
import requests
from prometheus_client import parser
import quantity
import pprint
import datetime
from tzlocal import get_localzone

# load the config for the cluster to connect to the API
config.load_incluster_config()

# clients for namespaces and apps
coreApiClient = client.CoreV1Api()
appsApiClient = client.AppsV1Api()
topApiClient = client.CustomObjectsApi()

# converts watcher-5769cd9645-nsh6d to watcher
def getPodName(pod):
    return "-".join(pod.split("-")[:-2])

# get the cpu, latency, and memory for each deployment in a namespace, also break it down by pod
# {test: {cpu: 0, memory: 0, count: 1, pods: {test-1234: {cpu: 0, memory: 0}}}}
passed_pods = set()
def getResourceMetrics(namespace):
    info = {}
    for pod in topApiClient.list_namespaced_custom_object("metrics.k8s.io", "v1beta1", namespace, "pods")["items"]:
        pod_name = getPodName(pod["metadata"]["name"])
        
        # don't count pods that have recently become ready or are not running
        global passed_pods
        if (not pod["metadata"]["name"] in passed_pods):
            status = coreApiClient.read_namespaced_pod_status(pod["metadata"]["name"], namespace).status
            phase = status.phase

            if phase != "Running":
                print("ignoring not running")
                continue

            running_condition = [i for i in status.conditions if i.type == "Ready"][0]
            ready_time = datetime.datetime.now() - running_condition.last_transition_time.replace(tzinfo=None)
            if (ready_time < datetime.timedelta(seconds=30)):
                print("ignoring too young")
                continue
            
            passed_pods.add(pod["metadata"]["name"])

        if pod_name not in info:
            info[pod_name] = {"cpu": 0, "memory": 0, "count": 0, "pods": {}}
            #info[pod_name]["latency"] =  getNamespaceDeploymentResponseLatency(namespace, pod_name, 0.95, "30s")

        info[pod_name]["count"] += 1
        #info[pod_name]["pods"][pod["metadata"]["name"]] = {"cpu": 0, "memory": 0}
        for container in pod["containers"]:
            info[pod_name]["cpu"] += float(quantity.parse_quantity(container["usage"]["cpu"]))
            #info[pod_name]["pods"][pod["metadata"]["name"]]["cpu"] += float(quantity.parse_quantity(container["usage"]["cpu"]))
            info[pod_name]["memory"] += float(quantity.parse_quantity(container["usage"]["memory"]))
            #info[pod_name]["pods"][pod["metadata"]["name"]]["memory"] += float(quantity.parse_quantity(container["usage"]["memory"]))

    for deployment in info:
        info[deployment]["utilization"] = round(100 * float(info[deployment]["cpu"] /  float(quantity.parse_quantity("50m"))) / info[deployment]["count"])

    return info

# get metric data for deployments in a namespace without latency from linkerd, count all
def getResourceMetricsNoLinkerd(namespace):
    info = {}
    for pod in topApiClient.list_namespaced_custom_object("metrics.k8s.io", "v1beta1", namespace, "pods")["items"]:
        pod_name = getPodName(pod["metadata"]["name"])

        if pod_name not in info:
            info[pod_name] = {"cpu": 0, "memory": 0, "count": 0, "pods": {}}

        info[pod_name]["count"] += 1
        #info[pod_name]["pods"][pod["metadata"]["name"]] = {"cpu": 0, "memory": 0}
        for container in pod["containers"]:
            info[pod_name]["cpu"] += float(quantity.parse_quantity(container["usage"]["cpu"]))
            #info[pod_name]["pods"][pod["metadata"]["name"]]["cpu"] += float(quantity.parse_quantity(container["usage"]["cpu"]))
            info[pod_name]["memory"] += float(quantity.parse_quantity(container["usage"]["memory"]))
            #info[pod_name]["pods"][pod["metadata"]["name"]]["memory"] += float(quantity.parse_quantity(container["usage"]["memory"]))

    return info


# fetch latency of a deployment from Linkerd
prometheus_pod_ip = ""
def getNamespaceDeploymentResponseLatency(namespace, deployment, percentile, period):
    try:
        # bypass coredns for getting pod ip
        global prometheus_pod_ip
        if prometheus_pod_ip == "":
            viz_pods = coreApiClient.list_namespaced_pod("linkerd-viz")
            for i in viz_pods.items:
                if "prometheus" in i.metadata.name:
                    prometheus_pod_ip = i.status.pod_ip

        metrics = requests.get(f"http://{prometheus_pod_ip}:9090/api/v1/query?query=histogram_quantile({percentile}, sum(rate(response_latency_ms_bucket{{namespace=\"{namespace}\", deployment=\"{deployment}\", direction=\"inbound\"}}[{period}])) by (le))").json()
        latency = metrics["data"]["result"][0]["value"][1]
        return latency
    except Exception as err:
        print("Error fetching latency " + str(err))
        prometheus_pod_ip = ""

        return 0.0

# get resources collected by linkerd injected prometheus
def getPrometheusMetrics(ip):
    metrics = list(parser.text_string_to_metric_families(requests.get("http://%s:4191/metrics/api/v1/query?query=histogram_quantile(0.95, sum(rate(response_latency_ms_bucket[30s])) by (le))" % ip).content.decode()))
    metrics_dict = {}
    for metric in metrics:
        metrics_dict[metric.name] = {
            "type": metric.type, 
            "unit": metric.unit, 
            "samples": [
                {
                    "labels": sample.labels, 
                    "value": sample.value, 
                    "timestamp": sample.timestamp
                } for sample in metric.samples
            ]
        }
    return metrics_dict

# get resource metrics and add prometheus info for each pod
def getNamespaceMetrics(namespace):
    resources = getResourceMetrics(namespace)
    for i in coreApiClient.list_namespaced_pod(namespace).items:
        if (i.metadata.name in resources[getPodName(i.metadata.name)]["pods"]):
            resources[getPodName(i.metadata.name)]["pods"][i.metadata.name]["prometheus"] = getPrometheusMetrics(i.status.pod_ip)
    return resources

