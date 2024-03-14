from kubernetes import client, config, watch
import requests
from prometheus_client import parser
import quantity
import pprint

# load the config for the cluster to connect to the API
config.load_incluster_config()

# clients for namespaces and apps
coreApiClient = client.CoreV1Api()
appsApiClient = client.AppsV1Api()
topApiClient = client.CustomObjectsApi()

# converts watcher-5769cd9645-nsh6d to watcher
def getPodName(pod):
    return "".join(pod.split("-")[:-2])

# get the cpu and memory for each deployment in a namespace, also break it down by pod
# {test: {cpu: 0, memory: 0, count: 1, pods: {test-1234: {cpu: 0, memory: 0}}}}
def getResourceMetrics(namespace):
    info = {}
    for pod in topApiClient.list_namespaced_custom_object("metrics.k8s.io", "v1beta1", namespace, "pods")["items"]:
        pod_name = getPodName(pod["metadata"]["name"])

        if pod_name not in info:
            info[pod_name] = {"cpu": 0, "memory": 0, "count": 0, "pods": {}}

        info[pod_name]["count"] += 1
        info[pod_name]["pods"][pod["metadata"]["name"]] = {"cpu": 0, "memory": 0}
        for container in pod["containers"]:
            info[pod_name]["cpu"] += float(quantity.parse_quantity(container["usage"]["cpu"]))
            info[pod_name]["pods"][pod["metadata"]["name"]]["cpu"] += float(quantity.parse_quantity(container["usage"]["cpu"]))
            info[pod_name]["memory"] += float(quantity.parse_quantity(container["usage"]["memory"]))
            info[pod_name]["pods"][pod["metadata"]["name"]]["memory"] += float(quantity.parse_quantity(container["usage"]["memory"]))

        info[pod_name]["latency"] =  getNamespaceDeploymentResponseLatency(namespace, pod_name, 0.95, "30s")

    return info

def getResourceMetricsNoLinkerd(namespace):
    info = {}
    for pod in topApiClient.list_namespaced_custom_object("metrics.k8s.io", "v1beta1", namespace, "pods")["items"]:
        pod_name = getPodName(pod["metadata"]["name"])

        if pod_name not in info:
            info[pod_name] = {"cpu": 0, "memory": 0, "count": 0, "pods": {}}

        info[pod_name]["count"] += 1
        info[pod_name]["pods"][pod["metadata"]["name"]] = {"cpu": 0, "memory": 0}
        for container in pod["containers"]:
            info[pod_name]["cpu"] += float(quantity.parse_quantity(container["usage"]["cpu"]))
            info[pod_name]["pods"][pod["metadata"]["name"]]["cpu"] += float(quantity.parse_quantity(container["usage"]["cpu"]))
            info[pod_name]["memory"] += float(quantity.parse_quantity(container["usage"]["memory"]))
            info[pod_name]["pods"][pod["metadata"]["name"]]["memory"] += float(quantity.parse_quantity(container["usage"]["memory"]))

    return info


def getNamespaceDeploymentResponseLatency(namespace, deployment, percentile, period):
    metrics = requests.get(f"http://prometheus.linkerd-viz.svc.cluster.local:9090/api/v1/query?query=histogram_quantile({percentile}, sum(rate(response_latency_ms_bucket{{namespace=\"{namespace}\", deployment=\"{deployment}\", direction=\"inbound\"}}[{period}])) by (le))").json()
    return metrics["data"]["result"][0]["value"][1]

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

