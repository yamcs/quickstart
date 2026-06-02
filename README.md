# Yamcs QuickStart

This repository holds the source code to start a basic Yamcs application that monitors a simulated spacecraft in low earth orbit.

You may find it useful as a starting point for your own project.


## Prerequisites

* Java 17+
* Linux x64/aarch64, macOS x64/aarch64, or Windows x64

A copy of Maven is also required, however this gets automatically downloaded an installed by using the `./mvnw` shell script as detailed below.


## Running Yamcs

Here are some commands to get things started:

Compile this project:

    ./mvnw compile

Start Yamcs on localhost:

    ./mvnw yamcs:run

Same as yamcs:run, but allows a debugger to attach at port 7896:

    ./mvnw yamcs:debug
    
Delete all generated outputs and start over:

    ./mvnw clean

This will also delete Yamcs data. Change the `dataDir` property in `yamcs.yaml` to another location on your file system if you don't want that.


## Telemetry

To start pushing CCSDS packets into Yamcs, run the included Python script:

    python simulator.py

This script will poll the Yamcs HTTP API until the target instance reports a `RUNNING` state before sending any packets, avoiding dropped telemetry during Yamcs startup.

It sends packets at 1 Hz over UDP to Yamcs. There is enough test data to run for a full calendar day.

The packets are a bit artificial and include a mixture of HK and accessory data.

The following optional arguments control which Yamcs instance to wait for:

| Argument            | Default       | Description               |
|---------------------|---------------|---------------------------|
| `--yamcs_host`      | `127.0.0.1`   | Yamcs HTTP host            |
| `--yamcs_port`      | `8090`        | Yamcs HTTP port            |
| `--yamcs_instance`  | `myproject`   | Yamcs instance name        |

Example:

    python simulator.py --yamcs_instance myproject --rate 10


## Telecommanding

This project defines a few example CCSDS telecommands. They are sent to UDP port 10025. The simulator.py script listens to this port. Commands  have no side effects. The script will only count them.


## Bundling

Running through Maven is useful during development, but it is not recommended for production environments. Instead bundle up your Yamcs application in a tar.gz file:

    ./mvnw package
