#! /usr/bin/env python3

import sys
import json
import quantity

TARGET = "15m" # CPU target metric

# load the run
run_file_name = sys.argv[1]
run_file = open(run_file_name)
run = json.load(run_file)

# isolate the counts and desired for each
counts = [{dep: slice["metrics"][dep]["count"] for dep in slice["metrics"]} for slice in run]
desired_counts = [slice["desired"] for slice in run]

# determine the stability of each state
def counts_equal(i):
    for dep in desired_counts[i]:
        if counts[i][dep] != desired_counts[i][dep]:
            return False
    return True

stability = [counts_equal(i) for i in range(len(counts))]

# -1 scale down, 0 stable, 1 scale up
def desired_direction(i):
    real_count = sum([counts[i][dep] for dep in counts[i]])
    desired_count = sum([desired_counts[i][dep] for dep in desired_counts[i]])

    if real_count == desired_count:
        return 0;
    elif real_count < desired_count:
        return 1
    else:
        return -1

stability_direction = [desired_direction(i) for i in range(len(counts))]

# find the lengths of all unstable events
instability_event_lengths = []
down = []
up = []
i = 0
while i < len(stability):
    if stability[i] == False:
        direction = desired_direction(i)
        length = 1
        while i + length < len(stability) and desired_direction(i + length) == direction:
            length += 1
        instability_event_lengths.append(length)
        if (direction == 1):
            up.append(length)
        else:
            down.append(length)
        i = i + length - 1
    i += 1

print(f"instability events: {len(instability_event_lengths)}")
print(f"instability average length: {sum(instability_event_lengths)/len(instability_event_lengths)}")
print(f"Percent stable: {len([i for i in range(len(stability)) if stability[i] == True]) / len(stability) * 100}%")

print(f"instability events (down): {len(down)}")
print(f"instability average length (down): {sum(down)/len(down)}")

print(f"instability events (up): {len(up)}")
print(f"instability average length (up): {sum(up)/len(up)}")
# get cpu usage of each state
cpu = [{dep: slice["metrics"][dep]["cpu"] for dep in slice["metrics"]} for slice in run]

def cpu_limit_exceeded(i):
    for dep in cpu[i]:
        if cpu[i][dep] > quantity.parse_quantity(TARGET) * run[i]["metrics"][dep]["count"]:
            return True
    return False

cpu_stability = [cpu_limit_exceeded(i) for i in range(len(cpu))]

# find the lengths of all unstable events
instability_event_lengths = []
i = 0
while i < len(cpu):
    if cpu_stability[i] == False:
        length = 1
        while i + length < len(cpu_stability) and cpu_stability[i + length] == False:
            length += 1
        instability_event_lengths.append(length)
        i = i + length - 1
    i += 1

print(f"cpu exceeded events: {len(instability_event_lengths)}")
print(f"cpu exceeded average length: {sum(instability_event_lengths) / len(instability_event_lengths)}")
print(f"Percent cpu okay: {len([i for i in range(len(run)) if cpu_limit_exceeded(i) == False]) / len(run) * 100}%")

cpu_updates = 0
curr_cpu = cpu[1]
for this_cpu in cpu:
    if curr_cpu != this_cpu:
        cpu_updates += 1
        curr_cpu = this_cpu

print(f"Percent new cpu value: {cpu_updates / len(run) * 100}%")

# get web latency
latencies = [float(slice["metrics"]["web"]["latency"]) for slice in run]
print(f"web average latency: {sum(latencies) / len(latencies)}")

latency_updates = 0
curr_lat = latencies[0]
for latency in latencies:
    if curr_lat != latency:
        latency_updates += 1
        curr_lat = latency

print(f"web latency percent new value: {latency_updates / len(run) * 100}%")
