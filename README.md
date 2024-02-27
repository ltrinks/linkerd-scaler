# Linkerd Scaler

## About
For now, Linkerd Scaler can scale deployments and access Prometheus metrics exposed by Linkerd proxies.

## Usage
Start by running:
```
./start.sh
```

Keep this script running for as long as you want the cluster alive, ^C to exit.

With the cluster running, in another terminal kubectl and other commands can be executed on the cluster.

To rebuild and rerun the watcher without restarting the cluster run:
```
./start-watcher.sh
```

Outputs of the watcher are found in metrics/, these persist but are deleted on each new watcher start.

## Nodevoto
Nodevoto can be found [here](https://github.com/sourishkrout/nodevoto).