echo "Running script to generate architecture diagram from docker-compose..."

#For generating architecture diagram with networks, ports and volumes
if
  docker run --rm -it --name bahpkg -v ${PWD}:/input pmsipilot/docker-compose-viz:latest  render -m image --force bahmni/docker-compose.yml --output-file=architecture-diagram/bahmni-architecture-diagram.png $1 $2 $3
then
  echo "Successfully generated architecture diagram from docker-compose!"
else
  echo "Failed to generate architecture diagram from docker-compose!"
fi
