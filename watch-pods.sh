#!/usr/bin/env bash

watch "kubectl get deployments; kubectl get deployments -n linkerd-scaler"

