# Yamcs QuickStart's Docker and Makefile

This folder contains content to run yamcs in a docker container

## Prerequisites

* make
* docker
* docker-compose

## Builing, running, and simulating data in Yamcs

Here are some commands to get things started:

To list available make targets:

    make

To run the all target:

    make all

To bring up yamcs container:

    make yamcs-up

This also starts the simulator in a companion container, so telemetry is
flowing as soon as Yamcs is up. Ports 8090 (web) and 10015/udp (TM) are
published on 127.0.0.1 only, since the quickstart runs without
authentication.

To bring down yamcs container:

    make yamcs-down

To run simulator by connecting to container:

    make yamcs-simulator

To shell into yamcs container:

    make yamcs-shell
