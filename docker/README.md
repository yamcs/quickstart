# Yamcs QuickStart's Docker and Makefile

This folder contains content to run yamcs in a docker container

## Prerequisites

* make
* docker
* docker-compose

## Building, running, and simulating data in Yamcs

Here are some commands to get things started:

To list available make targets:

    make

To run the all target (clean, yamcs-up, and yamcs-simulator at 1 Hz):

    make all

To run the all target at 10 Hz:

    make all-10hz

To bring up yamcs container:

    make yamcs-up

To bring down yamcs container:

    make yamcs-down

To run simulator by connecting to container:

    make yamcs-simulator

To run simulator at 10 Hz:

    make yamcs-simulator-10hz

To stop the simulator:

    make yamcs-simulator-down

To stop and restart the simulator:

    make yamcs-simulator-restart

To shell into yamcs container:

    make yamcs-shell

To remove build artifacts and docker resources:

    make clean

To bring up yamcs and wait up to 10 minutes for telemetry to be sent:

    make wait-for-sent

## Simulator arguments

The simulator targets support overriding the Yamcs connection via environment variables:

| Variable           | Default       | Description         |
|--------------------|---------------|---------------------|
| `YAMCS_HOST`       | `127.0.0.1`   | Yamcs HTTP host     |
| `YAMCS_PORT`       | `8090`        | Yamcs HTTP port     |
| `YAMCS_INSTANCE`   | `myproject`   | Yamcs instance name |

Example:

    make yamcs-simulator YAMCS_HOST=192.168.1.10 YAMCS_INSTANCE=myproject
