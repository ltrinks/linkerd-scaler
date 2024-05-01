# base image
FROM --platform=linux/x86_64 tensorflow/tensorflow

ENV PYTHONUNBUFFERED=1

# install dependencies
RUN pip install --upgrade pip
RUN pip install kubernetes
RUN pip install prometheus-client
RUN pip install matplotlib
RUN pip install tzlocal
RUN pip install pandas
RUN pip install numpy
RUN pip install scikit-learn
RUN pip install statsmodels

# copy the source code
WORKDIR /usr/watcher

COPY src .

# execute when started
CMD python3 act_before_main.py
