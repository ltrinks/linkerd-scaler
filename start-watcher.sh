#!/bin/bash

kubectl delete -f watcher/watcher.yaml
eval $(minikube -p linkerd-scaler docker-env)
./push-watcher.sh
kubectl apply -f watcher/watcher.yaml
