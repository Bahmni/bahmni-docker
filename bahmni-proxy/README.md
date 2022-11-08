# Bahmni Proxy

This directory contains resources for building Docker image for Bahmni Proxy Container. The proxy container is a Apache Httpd server with overridden configurations. The proxy container is used for the following purposes.
1. Serve `Bahmni Index Page`
2. Proxy rules for different components of the application is configured.
3. SSL configurations for the application are done through this service.

## Building the image locally
1. Checkout this repository and navigate into the `bahmni-proxy` folder.
2. Run the docker build command to build the image
    ```shell
     docker build -t bahmni/proxy:local .
     ```
3. Once the image is successfully built, update the image tag in the [.env](../.env) file in the `PROXY_IMAGE_TAG` variable.


### Notes:

  * Bahmni proxy has configuration to intercept websocket request to support [speech-assistant feature](https://github.com/Bahmni/speech-assistant-package)
