#!/bin/bash

minikube -p linkerd-scaler addons enable metrics-server
kubectl delete -f watcher/watcher.yaml
eval $(minikube -p linkerd-scaler docker-env)
docker build -t watcher watcher
kubectl apply -f watcher/watcher.yaml
