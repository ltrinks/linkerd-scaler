#!/bin/bash

# if a command fails error
set -e

# kill all background tasks and the cluster on exit or error
trap 'kill $(jobs -p); minikube -p linkerd-scaler delete' EXIT
trap 'kill $(jobs -p); minikube -p linkerd-scaler delete; echo ERROR AT \"$BASH_COMMAND\", EXITING' ERR

# delete and start linkerd-scaler test cluster
export MINIKUBE_IN_STYLE=0
minikube -p linkerd-scaler delete;
minikube -p linkerd-scaler start --cpus 4 --memory 4096;
minikube -p linkerd-scaler mount ./metrics:/mnt/metrics &
eval $(minikube -p linkerd-scaler docker-env)

# install linkerd control plane
linkerd install --crds | kubectl apply -f -;
linkerd install --set proxyInit.runAsRoot=true | kubectl apply -f -;
linkerd --output short check;

# deploy nodevoto and inject linkerd proxies
linkerd inject nodevoto/nodevoto.yml | kubectl apply -f -;
linkerd --output short -n nodevoto check --proxy;

# install linkerd viz tool
linkerd viz install | kubectl apply -f -;
linkerd --output short check;

# add linkerd-scale into cluster
minikube -p linkerd-scaler addons enable metrics-server
kubectl create namespace linkerd-scaler
docker build -t watcher watcher
kubectl apply -f watcher/watcher.yaml

# open linkerd dashboard and nodevoto web site
linkerd viz dashboard &
minikube -p linkerd-scaler -n nodevoto service web-svc &

# wait for ^C
tail -f /dev/null
