# Bahmni Docker

Refer this [Wiki Page](https://bahmni.atlassian.net/wiki/spaces/BAH/pages/299630726/Running+Bahmni+on+Docker) for Running Bahmni on Docker for detailed instructions.

# To start Bahmni using docker compose: 
Since logging with Loki is enabled, install the loki logging driver first
```
docker plugin install grafana/loki-docker-driver:latest --alias loki --grant-all-permissions
```

1. Go to bahmni subfolder. For example: `cd bahmni`.
2. Execute script: `./run-bahmni.sh`. This will give you options for start/stop/view-logs/pull/reset/etc. 
3. Ensure your `.env` file in the sub-folder has correct PROFILE configured, before executing the above commands.  

Note: Some of the images are not compatible with Apple Silicon Mac M1 machines and will give error while running docker commands. To fix that, add `platform: linux/x86_64` in the service definition. 