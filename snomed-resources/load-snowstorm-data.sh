#!/bin/sh

echo "Installing curl..."
apk add --no-cache curl 

# Check if snomed-data.zip file exists
if [ ! -f /snowstorm-data/snomed-data.zip ]; then
  echo "ERROR: snomed-data.zip file not found in /snowstorm-data directory"
  echo "Please check if you have setup the volumes and .env for SNOMED_RF2_FILES_PATH correctly"
  exit 1
fi

snowstorm_lite_url="http://snowstorm-lite:8080/fhir"

# Wait for the Snowstorm Lite Server to start
while true; do
  http_status_code=$(curl -s -o /dev/null -w "%{http_code}" $snowstorm_lite_url)

  if [ "$http_status_code" -eq 200 ]; then
    echo "Snowstorm Lite Server is up and running!"
    break
  else
    echo "HTTP status code $http_status_code - Not OK, retrying in 5 seconds...";
    sleep 5
  fi
done

# Make a POST API call to load data
curl -v -u admin:${SNOWSTORM_LITE_ADMIN_PASSWORD} --form file='@/snowstorm-data/snomed-data.zip' --form version-uri="http://snomed.info/sct/900000000000207008/version/20230731" http://snowstorm-lite:8080/fhir-admin/load-package
echo "Request for Data Load Sent Successfully"
