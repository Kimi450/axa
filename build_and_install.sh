#!/bin/bash

docker build -t kimi450/axa .
docker push kimi450/axa:latest
(cd charts && helm uninstall axa || true && helm upgrade --install axa .)