#!/usr/bin/env bash

export pod=$(kubectl get pods -n linkerd-scaler | grep watcher | awk '{print $1}')
echo following $pod
kubectl -n linkerd-scaler logs --follow $pod
