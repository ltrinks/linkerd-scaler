import pandas
import matplotlib.pyplot as plt
import json
import datetime
import math
import numpy as np
from sklearn.metrics import mean_squared_error
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.arima.model import ARIMA


# load the run
run_file = open("../../runs/long_corekube/run.json")
run = json.load(run_file)

# convert into data frame
time_series_worker = [{"start": datetime.datetime.fromtimestamp(i["start_s"]), "cpu": i["metrics"]["corekube-worker"]["cpu"]} for i in run]
data_frame = pandas.DataFrame({"time": [i["start"] for i in time_series_worker], "cpu": [i["cpu"] for i in time_series_worker]})
data_frame.index = [i["start"] for i in time_series_worker]
data_frame.index = pandas.DatetimeIndex(data_frame.index)
del data_frame["time"]



boundary = math.ceil((len(data_frame) * 0.75))
train = data_frame[: boundary]
test = data_frame[boundary: ]

plt.plot(train["cpu"], color="black", label="training")
plt.plot(test["cpu"], color="red", label="testing")
plt.savefig("./cpu.jpg")

print(train.head())
print(test.head())

y = train["cpu"]
y.index = y.index.to_period("min")

#SARIMAX
ARMAmodel = SARIMAX(y, order = (1, 0, 1))
ARMAmodel = ARMAmodel.fit()

y_pred = ARMAmodel.get_forecast(len(test.index))
y_pred_df = y_pred.conf_int(alpha = 0.05)

y_pred_df["Predictions"] = ARMAmodel.predict(start = y_pred_df.index[0], end = y_pred_df.index[-1])
y_pred_df.index = test.index
y_pred_out = y_pred_df["Predictions"] 

plt.plot(y_pred_out.index, y_pred_out, color='green', label = 'Predictions')
plt.legend()
plt.savefig("./predictions.jpg")

arma_rmse = np.sqrt(mean_squared_error(test["cpu"].values, y_pred_df["Predictions"]))
print("RMSE: ",arma_rmse)

#ARIMA
ARIMAmodel = ARIMA(y, order = (5, 1, 0))
ARIMAmodel = ARIMAmodel.fit()

y_pred = ARIMAmodel.get_forecast(len(test.index))
y_pred_df = y_pred.conf_int(alpha = 0.05) 
y_pred_df["Predictions"] = ARIMAmodel.predict(start = y_pred_df.index[0], end = y_pred_df.index[-1])
y_pred_df.index = test.index
y_pred_out = y_pred_df["Predictions"] 
plt.plot(y_pred_out, color='Yellow', label = 'ARIMA Predictions')
plt.legend()
plt.savefig("./arima_predictions.png")

arma_rmse = np.sqrt(mean_squared_error(test["cpu"].values, y_pred_df["Predictions"]))
print("RMSE: ",arma_rmse)


# frame a sequence as a supervised learning problem
def timeseries_to_supervised(data, lag=1):
	df = pandas.DataFrame(data)
	columns = [df.shift(i) for i in range(1, lag+1)]
	columns.append(df)
	df = pandas.concat(columns, axis=1)
	df.fillna(0, inplace=True)
	return df

supervised = timeseries_to_supervised(train, 1)
print(supervised.head())
