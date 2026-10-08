#!/bin/bash
set -e

echo "Running script to generate architecture diagram from docker-compose..."

#For generating architecture diagram with networks, ports and volumes
docker run --rm --name bahpkg -v ${PWD}:/input pmsipilot/docker-compose-viz:latest render -m image --force bahmni-lite/docker-compose.yml --output-file=architecture-diagram/bahmni-lite-architecture-diagram.png $1 $2 $3 &&
docker run --rm --name bahpkg -v ${PWD}:/input pmsipilot/docker-compose-viz:latest render -m image --force bahmni-standard/docker-compose.yml --output-file=architecture-diagram/bahmni-standard-architecture-diagram.png $1 $2 $3 &&
echo "Successfully generated architecture diagram from docker-compose!"
