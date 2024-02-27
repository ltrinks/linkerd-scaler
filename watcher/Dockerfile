# base image
FROM python:3.11.8-alpine
ENV PYTHONUNBUFFERED=1

# install dependencies
RUN pip install kubernetes

# copy the source code
WORKDIR /usr/watcher

COPY src .

# execute when started
CMD python main.py
