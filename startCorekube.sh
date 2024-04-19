#!/bin/bash

# install linkerd CLI
curl --proto '=https' --tlsv1.2 -sSfL https://run.linkerd.io/install-edge | sh
export PATH=$HOME/.linkerd2/bin:$PATH

# set up kubernetes cluster
cd ../systems-approach/aether-onramp
make aether-k8s-uninstall
make aether-k8s-install

cd -
cd corekube
./startcorekube.sh

sleep 240

cd ..
kubectl create namespace linkerd-scaler
./start-watcher.sh
