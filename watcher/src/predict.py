import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

from tensorflow.keras.models import load_model
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import *
from tensorflow.keras.callbacks import ModelCheckpoint
from tensorflow.keras.losses import MeanSquaredError
from tensorflow.keras.metrics import RootMeanSquaredError
from tensorflow.keras.optimizers import Adam
import pandas
import matplotlib.pyplot as plt
import json
import datetime
import math
import numpy as np
from sklearn.metrics import mean_squared_error
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.arima.model import ARIMA
import tensorflow as tf

# convert into data frame
def run_to_df(run, deployment):
    time_series_worker = [{"start": datetime.datetime.fromtimestamp(i["start_s"]), "cpu": i["metrics"][deployment]["cpu"]} for i in run]
    data_frame = pandas.DataFrame({"time": [i["start"] for i in time_series_worker], "cpu": [i["cpu"] for i in time_series_worker]})
    data_frame.index = [i["start"] for i in time_series_worker]
    data_frame.index = pandas.DatetimeIndex(data_frame.index)
    del data_frame["time"]
    return data_frame

# make input matrix
def df_to_x_y(df, window_size):
    df_as_np = df.to_numpy()
    x = []
    y = []
    for i in range(len(df_as_np) - (window_size)):
        row = [[a] for a in df_as_np[i: i + window_size]]
        x.append(row)
        label = df_as_np[i + window_size]
        y.append(label)
    return np.array(x), np.array(y)


# run_file = run_file = open("../../runs/corekube2/run.json")
# run = json.load(run_file)
# data_frame = run_to_df(run, "corekube-worker")

# x, y = df_to_x_y(data_frame, 5)

# train_predictions = best.predict(x).flatten()
# train_results = pandas.DataFrame(data ={"Train Predictions": train_predictions, "Actuals": [i[0] for i in y]})

# plt.plot(train_results["Train Predictions"], label = 'Predicted', color = "orange")
# plt.plot(data_frame.to_numpy(), label = "Actual", color = "blue")
# plt.legend()
# plt.ylabel("CPU usage (cores)")
# plt.xlabel("Time")
# plt.title("LSTM Model Prediction")
# plt.savefig("./predict.png")
# plt.close()

models = {"corekube-worker": load_model("./corekube-worker.keras"),
            "corekube-frontend": load_model("./corekube-frontend.keras"),
            "corekube-db": load_model("./corekube-db.keras")}

def predict_ahead(data, start, ahead, deployment):
    last = np.asarray(data).tolist()[ : start ]
    prediction = 0
    for i in range(ahead):
        prediction = models[deployment].predict(np.array(last)).flatten()[-1]
        last.append(last[-1][1 : ] + [[[prediction]]])

    return prediction

# data = x[:1000].tolist()
# print(x[0])
# predictions = []
# for i in range(30):
#     prediction = models["corekube-worker"].predict(np.asarray(data)).flatten()[-1]
#     predictions.append(prediction)
#     data.append(data[-1][1:] + [[[prediction]]])

# plt.plot(predictions)
# plt.savefig("./predictions.png")



# look_ahead = [predict_ahead(x, i, 45) for i in range(1, len(x))]

# plt.plot(look_ahead, label = 'Predicted', color = "orange")
# plt.plot(data_frame.to_numpy(), label = "Actual", color = "blue")
# plt.legend()
# plt.ylabel("CPU usage (cores)")
# plt.xlabel("Time")
# plt.title("LSTM Model Prediction (Look Ahead)")
# plt.savefig("./predict_ahead.png")

def get_prediction(combined_over_time, deployment):
    data_frame = run_to_df(combined_over_time, deployment)
    x, y = df_to_x_y(data_frame, 5)
    return predict_ahead(x, -1, 1, deployment)
