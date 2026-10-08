#!/bin/bash


function checkDockerAndDockerComposeVersion {
    if ! command -v docker >/dev/null 2>&1; then
        echo 'Error: docker is not installed. Please install Docker first.' >&2
        exit 1
    fi

    if ! COMPOSE_VERSION=$(docker compose version 2>&1); then
        echo 'Error: Docker Compose V2 is not available. Please install the Docker Compose plugin.' >&2
        exit 1
    fi

    if ! DOCKER_SERVER_VERSION=$(docker version --format '{{.Server.Version}}' 2>/dev/null); then
        echo 'Error: Cannot connect to the Docker daemon. Start Docker and check that the selected Docker context is reachable.' >&2
        exit 1
    fi

    if [[ ! "$DOCKER_SERVER_VERSION" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
        echo "Error: Unable to determine Docker Engine version from '$DOCKER_SERVER_VERSION'." >&2
        exit 1
    fi

    DOCKER_SERVER_VERSION_MAJOR=$((10#${BASH_REMATCH[1]}))
    DOCKER_SERVER_VERSION_MINOR=$((10#${BASH_REMATCH[2]}))
    DOCKER_SERVER_VERSION_PATCH=$((10#${BASH_REMATCH[3]}))

    if (( DOCKER_SERVER_VERSION_MAJOR < 20 ||
          (DOCKER_SERVER_VERSION_MAJOR == 20 && DOCKER_SERVER_VERSION_MINOR < 10) ||
          (DOCKER_SERVER_VERSION_MAJOR == 20 && DOCKER_SERVER_VERSION_MINOR == 10 && DOCKER_SERVER_VERSION_PATCH < 13) )); then
        echo "Error: Docker Engine version >= 20.10.13 is required; found $DOCKER_SERVER_VERSION." >&2
        exit 1
    fi

    echo "Docker Engine version: $DOCKER_SERVER_VERSION (minimum 20.10.13)"
    echo "Docker Compose version: $COMPOSE_VERSION"
    echo "---"
}

function checkIfDirectoryIsCorrect {
    # Current subdirectory
    current_subdir=$(basename "$(pwd)")

    if [ "$current_subdir" == "bahmni-lite" ] || [ "$current_subdir" == "bahmni-standard" ] ; then
        return
    else
        echo "Error: This script should be run from either 'bahmni-lite' or 'bahmni-standard' subfolder. Please cd to the appropriate sub-folder and then execute the run-bahmni.sh command."
        exit 1
    fi
}

function start {
    local file=$1
    echo "Executing command: 'docker compose up -d' with the images specified in the $file file"
    echo "Starting Bahmni with default profile from $file file"
    docker compose --env-file "$file" up -d
}

function setAllProfiles {
    local file=$1
    local profiles
    local profile
    composeProfileArgs=()

    if profiles=$(docker compose --env-file "$file" config --profiles 2>/dev/null); then
        while IFS= read -r profile; do
            if [ -n "$profile" ]; then
                composeProfileArgs+=(--profile "$profile")
            fi
        done <<< "$profiles"
    fi

    if [ ${#composeProfileArgs[@]} -eq 0 ]; then
        composeProfileArgs=(--profile emr --profile bahmni-lite --profile bahmni-standard --profile bahmni-mart)
    fi
}


function stop {
    local file=$1
    echo "Executing command: 'docker compose down' with all profiles"
    setAllProfiles "$file"
    docker compose --env-file "$file" "${composeProfileArgs[@]}" down
}

function sshIntoService {
    local file=$1
    # Using all profiles, so that we can status of all services
    echo "Listing the running services..."
    docker compose --env-file "$file" --profile bahmni-lite --profile bahmni-standard --profile bahmni-mart ps

    echo "Enter the SERVICE name which you wish to ssh into:"
    read -r serviceName

    docker compose --env-file "$file" exec "$serviceName" /bin/sh
}

function showLogsOfService {
    local file=$1
    # Using all profiles, so that we can status of all services
    echo "Listing the running services..."
    docker compose --env-file "$file" --profile bahmni-lite --profile bahmni-standard --profile bahmni-mart ps

    echo "Enter the SERVICE name whose logs you wish to see:"
    read -r serviceName

    docker compose --env-file "$file" logs "$serviceName" -f
}


function showOpenMRSlogs {
    local file=$1
    echo "Opening OpenMRS Logs..."
    docker compose --env-file "$file" logs openmrs -f
}

function startMart {
    local file=$1
    echo "Starting services with profile 'bahmni-mart'..."
    docker compose --env-file "$file" --profile bahmni-mart up -d
}

function pullLatestImages {
    local file=$1
    echo "Pulling all the images specified in the $file file..."
    docker compose --env-file "$file" pull
}

function showStatus {
    local file=$1
    echo "Listing status of running Services with command: 'docker compose ps'"
    # Using all profiles, so that we can status of all services
    setAllProfiles "$file"
    docker compose --env-file "$file" "${composeProfileArgs[@]}" ps

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
  local file=$1
  echo "Listing current volumes..."
  docker volume ls
  echo "---"
  if confirm "WARNING: Are you sure you want to DELETE all Bahmni Data and Volumes??"; then
    echo "Proceeding with a DELETE.... "

    echo "1. Stopping all services, using all profiles.."
    setAllProfiles "$file"
    docker compose --env-file "$file" "${composeProfileArgs[@]}" down

    docker compose --env-file "$file" ps

    echo "2. Deleting all volumes (-v) .."
    docker compose --env-file "$file" "${composeProfileArgs[@]}" down -v
    RESULT=$?
    if [ $RESULT -eq 0 ]; then
        echo "Volumes deleted successfully."
    else
        echo "[ERROR] Command threw an error! Trying stopping all services, and then retry."
    fi

    echo "Volumes remaining on machine 'docker volume ls': "
    docker volume ls

    echo "-"
    echo "Note:"
    echo "-----"
    echo "1. If you still wish to delete some other volumes you can use the 'docker volume rm' command."
    echo "2. Alternatively, to delete all containers, networks, volumes you can look at the 'docker system prune --volumes' command. Read more here: https://docs.docker.com/config/pruning/"
    echo "3. If you want the latest Bahmni images, then PULL them first and then start Bahmni."

  else
    echo "OK Aborting :)"
  fi
}

function restartService {
    local file=$1
    # One can ONLY restart services in current profile (limitation of docker compose restart command).
    echo "Listing the running services from current profile ($file file) that can be restarted..."
    docker compose --env-file "$file" ps

    echo "Enter the name of the SERVICE to restart:"
    read -r serviceName

    echo "Restarting SERVICE: $serviceName"
    docker compose --env-file "$file" restart "$serviceName"

    if confirm "Do you want to see the service logs?"; then
        docker compose --env-file "$file" logs "$serviceName" -f
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
echo "3) LOGS: Show OpenMRS Logs"
echo "4) LOGS: Show LOGS of a service"
echo "5) SSH into a Container"
echo "6) START Bahmni Analytics (Mart and Metabase)"
echo "7) PULL latest images from Docker hub for Bahmni"
echo "8) RESET and ERASE All Volumes/Databases from docker!"
echo "9) RESTART a service"
echo "0) STATUS of all services"
echo "-------------------------"
read option

file=".env"
if ! [ "$1" == "" ]; then
    file="$1"
fi

case $option in
    1) start $file;;
    2) stop $file;;
    3) showOpenMRSlogs $file;;
    4) showLogsOfService $file;;
    5) sshIntoService $file;;
    6) startMart $file;;
    7) pullLatestImages $file;;
    8) resetAndEraseALLVolumes $file;;
    9) restartService $file;;
    0) showStatus $file;;
    *) echo "Invalid option selected";;
esac
