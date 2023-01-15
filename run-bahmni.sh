#!/bin/bash


function checkDockerAndDockerComposeVersion {
    
    # Check if docker is installed
    if ! [ -x "$(command -v docker)" ]; then
    echo 'Error: docker is not installed. Please install docker first!' >&2
    exit 1
    fi

    DOCKER_SERVER_VERSION=$(docker version -f "{{.Server.Version}}")
    DOCKER_SERVER_VERSION_MAJOR=$(echo "$DOCKER_SERVER_VERSION"| cut -d'.' -f 1)
    DOCKER_SERVER_VERSION_MINOR=$(echo "$DOCKER_SERVER_VERSION"| cut -d'.' -f 2)
    DOCKER_SERVER_VERSION_BUILD=$(echo "$DOCKER_SERVER_VERSION"| cut -d'.' -f 3)

    if [ "${DOCKER_SERVER_VERSION_MAJOR}" -ge 20 ] && \
    [ "${DOCKER_SERVER_VERSION_MINOR}" -ge 10 ]  && \
    [ "${DOCKER_SERVER_VERSION_BUILD}" -ge 13 ]; then
        echo 'Docker version >= 20.10.13, using Docker Compose V2'
    else
        echo 'Docker versions < 20.10.13 are not supported' >&2 
        exit 1
    fi

    # Check the version of Docker Compose
    if ! [ -x "$(command -v docker compose version)" ]; then
    echo 'Error: docker compose is not installed. Please install docker compose.' >&2
    exit 1
    fi
    version=$(docker compose version)
    echo "Docker Compose version: $version"
    echo "---"
}

function checkIfDirectoryIsCorrect {
    # Current subdirectory
    current_subdir=$(basename $(pwd))
    echo "$current_subdir"

    if [ "$current_subdir" == "bahmni-lite" ] || [ "$current_subdir" == "bahmni-standard" ] ; then
        return
    else
        echo "Error: This script should be run from either 'bahmni-lite' or 'bahmni-standard' subfolder. Please cd to the appropriate sub-folder and then execute the run-bahmni.sh command."
        exit 1
    fi
}

function start {
    echo "Executing command: 'docker compose up -d'"
    docker compose up -d
}


function stop {
    echo "Executing command: 'docker compose down'"
    docker compose down
}

function sshIntoService {
    echo "Listing the running services..."
    docker compose ps

    echo "Enter the SERVICE name which you wish to ssh into:"
    read serviceName
    
    docker compose exec $serviceName /bin/sh
}

function showLogsOfService {
    echo "Listing the running services..."
    docker compose ps

    echo "Enter the SERVICE name whose logs you wish to see:"
    read serviceName
    
    docker compose logs $serviceName -f
}


function showOpenMRSlogs {
    echo "Opening OpenMRS Logs..."
    docker compose logs openmrs -f 
}

function startMart {
    echo "Starting services with profile 'bahmni-mart'..."
    docker compose --profile bahmni-mart up -d
}

function pullLatestImages {
    echo "Pulling all latest images..."
    docker compose pull
}

function showStatus {
    echo "Listing status of running services with command: 'docker ps'"
    docker ps
}


# Function to prompt the user for a "Yes" or "No" answer
confirm() {
    read -p "$1 [y/n]: " response
    case $response in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        [nN][oO]|[nN])
            return 1
            ;;
        *)
            echo "Invalid input"
            return 1
    esac
}


function resetAndEraseALLVolumes {
  if confirm "Are you sure you want to DELETE all Data and Volumes in docker on this MACHINE?? Please say Yes/No to proceed if you are absolutely sure. This will delete even non-Bahmni volumes used by Docker!"; then
    echo "Proceeding with a DELETE.... "
    
    echo "1. Stopping all services.."
    docker compose down
    docker compose ps
    
    echo "2. Deleting all volumes .."
    docker volume rm $(docker volume ls -q)
    docker volume ls

    echo "All volumes/databases deleted"
    echo "Now you can start Bahmni fresh. If you want latest images, then PULL them first and then start Bahmni."

  else
    echo "OK Aborting :)"
  fi  
}

#Function to shutdown the script
function shutdown {
    exit 0
}

# Check Docker Compose versions first
checkDockerAndDockerComposeVersion
# Check Directory is correct
checkIfDirectoryIsCorrect

echo "Please select an option:"
echo "------------------------"
echo "1) START Bahmni services"
echo "2) STOP  Bahmni services"
echo "3) Show OpenMRS Logs"
echo "4) Show Logs of a service"
echo "5) SSH into a Container"
echo "6) Start Bahmni Analytics (Mart and Metabase)"
echo "7) PULL latest images from Docker hub for Bahmni"
echo "8) RESET and ERASE All Volumes/Databases from docker"
echo "0) Show STATUS of all containers"
echo "-------------------------"
read option

case $option in
    1) start;;
    2) stop;;
    3) showOpenMRSlogs;;
    4) showLogsOfService;;
    5) sshIntoService;;
    6) startMart;;
    7) pullLatestImages;;
    8) resetAndEraseALLVolumes;;
    0) showStatus;;   
    *) echo "Invalid option selected";;
esac
