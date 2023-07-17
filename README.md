# Bahmni Docker

Refer this [Wiki Page](https://bahmni.atlassian.net/wiki/spaces/BAH/pages/299630726/Running+Bahmni+on+Docker) for Running Bahmni on Docker for detailed instructions.

## Running Bahmni LITE or STANDARD using docker compose: 
1. Navigate to the relevant subfolder for your desired configuration. For example: `cd bahmni-lite`.
2. Execute the script: `./run-bahmni.sh`. This script provides various options such as start, stop, view logs, pull updates, reset, etc.
3. Before executing the above commands, ensure that your `.env` file in the sub-folder is correctly configured with the appropriate PROFILE.

## Environment Variable Configuration
The `.env` file is used for configuring environment variables for the Bahmni Docker setup. By default, the `run-bahmni.sh` script relies on the `.env` file, which points to the `1.0.0` image tag.

If you wish to use the `latest` images instead, there is an alternative script available named `run-bahmni-dev.sh`. This script relies on the `.env-dev` file for environment variable configuration.

Please choose the appropriate script based on your requirements and make sure the respective `.env` or `.env-dev` file is properly configured before running the commands.

For detailed instructions and further information, please refer to the [Wiki Page](https://bahmni.atlassian.net/wiki/spaces/BAH/pages/299630726/Running+Bahmni+on+Docker) mentioned above.