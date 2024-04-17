docker build -t watcher watcher
docker tag watcher ltrinks/watcher:latest
docker push ltrinks/watcher:latest