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
docker pull sourishkrout/nodevoto:v5

# install linkerd CLI
curl --proto '=https' --tlsv1.2 -sSfL https://run.linkerd.io/install-edge | sh
export PATH=$HOME/.linkerd2/bin:$PATH

# install linkerd control plane
linkerd install --crds | kubectl apply -f -;
linkerd install --set proxyInit.runAsRoot=true | kubectl apply -f -;
linkerd --output short check --wait 30m;

# deploy nodevoto and inject linkerd proxies
linkerd inject nodevoto.yml --proxy-cpu-request 5m | kubectl apply -f -;
linkerd --output short -n nodevoto check --proxy --wait 30m;

# install linkerd viz tool
linkerd viz install | kubectl apply -f -;
linkerd --output short check --wait 30m;
minikube -p linkerd-scaler addons enable metrics-server
sleep 30

# add linkerd-scale into cluster
kubectl create namespace linkerd-scaler
docker build -t watcher watcher
#kubectl apply -f nodevoto-hpa.yaml
kubectl apply -f watcher/watcher.yaml
sleep 10

echo running

# follow watcher logs
#./follow-logs.sh

# open linkerd dashboard and nodevoto web site
# linkerd viz dashboard &
# minikube -p linkerd-scaler -n nodevoto service web-svc &

# wait for ^C
tail -f /dev/null
