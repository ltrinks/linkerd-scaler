#!/usr/bin/env bash

watch "kubectl get deployments -n nodevoto-bot; kubectl get deployments -n nodevoto; kubectl get deployments -n linkerd-scaler"

