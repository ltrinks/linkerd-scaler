#!/bin/bash

kubectl delete -f watcher/watcher.yaml
kubectl create namespace watcher
eval $(minikube -p nodevoto docker-env)
docker build -t watcher watcher
kubectl apply -f watcher/watcher.yaml
