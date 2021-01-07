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

To build yamcs:

    make yamcs-build

To bring up yamcs container:

    make yamcs-up

To bring down yamcs container:

    make yamcs-down

To run simulator by connecting to container:

    make yamcs-simulator

To shell into yamcs container:

    make yamcs-shell
