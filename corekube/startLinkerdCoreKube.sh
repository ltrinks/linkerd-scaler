linkerd inject k8s/corekube-db.yaml  | kubectl apply -f -
linkerd inject k8s/corekube-db-svc.yaml | kubectl apply -f -
linkerd inject k8s/corekube-frontend-svc.yaml | kubectl apply -f -
linkerd inject k8s/corekube-frontend.yaml | kubectl apply -f -
linkerd inject k8s/corekube-worker-svc.yaml | kubectl apply -f -
linkerd inject k8s/corekube-1worker-autoscaling.yaml | kubectl apply -f -