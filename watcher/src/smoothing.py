import pandas as pd
import matplotlib.pyplot as plt
import json
import sys
import math
import quantity

run_file_name = sys.argv[1]
run_file = open(run_file_name)
run = json.load(run_file)

web_cpu_utilization = [i["metrics"]["web"]["cpu"] for i in run]
web_cpu_utilization_avg = [i["metrics"]["web"]["cpu"] / i["metrics"]["web"]["count"] for i in run]

ema_cpu = pd.DataFrame({"previous": web_cpu_utilization}).ewm(com=0.9).mean()["previous"].tolist()

# if the change between two values is greater than 20%, trim it to 20%
gradual_change = []
for i, value in enumerate(web_cpu_utilization):
    if i == 0:
        gradual_change.append(value)
        continue
    
    prev = gradual_change[-1]
    change = value - prev
    percent_change = abs(change) / ((prev + value) / 2)
    if percent_change > 0.03:
        direction = 1
        if change < 0:
            direction = -1
        gradual_change.append(prev + (direction * ((prev + value) / 2) * 0.03))
        continue
    gradual_change.append(value)


target = float(quantity.parse_quantity("15m"))
gradual_change_target = []
for i, value in enumerate(web_cpu_utilization):
    if i == 0:
        gradual_change_target.append(value)
        continue
    
    prev = gradual_change_target[-1]
    change = value - prev
    if abs(change) > target * 0.05:
        direction = 1
        if change < 0:
            direction = -1
        gradual_change_target.append(prev + (direction * target * 0.05))
        continue

    # change is insignificant, keep previous
    gradual_change_target.append(prev)

gradual_change_total = [val * run[i]["metrics"]["web"]["count"] for i, val in enumerate(gradual_change)]
gradual_change_target_total = [val * run[i]["metrics"]["web"]["count"] for i, val in enumerate(gradual_change_target)]

ema_cpu = pd.DataFrame({"previous": gradual_change}).ewm(com=0.9).mean()["previous"].tolist()


x_axis = [i for i in range(len(web_cpu_utilization))]

plt.plot(x_axis, web_cpu_utilization, label="Raw", color="blue")
plt.plot(x_axis, gradual_change_target, label="Gradual", color="grey")
plt.legend()

plt.show()
