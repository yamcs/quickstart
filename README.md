# Yamcs QuickStart

This repository holds the source code to start a basic Yamcs application that monitors a simulated spacecraft in low earth orbit.

You may find it useful as a starting point for your own project.


## Prerequisites

* Java 11
* Maven 3.1+
* Linux x64 or macOS


## Running Yamcs

Here are some commands to get things started:

Compile this project:

    mvn compile

Start Yamcs on localhost:

    mvn yamcs:run

Same as yamcs:run, but allows a debugger to attach at port 7896:

    mvn yamcs:debug
    
Delete all generated outputs and start over:

    mvn clean

This will also delete Yamcs data. Change the `dataDir` property in `yamcs.yaml` to another location on your file system if you don't want that.


## Telemetry

To start pushing CCSDS packets into Yamcs, run the included Python script:

    python simulator.py

This script will send packets at 1 Hz over UDP to Yamcs. There is enough test data to run for a full calendar day.

The packets are a bit artificial and include a mixture of HK and accessory data.


## Telecommanding

This project defines a few example CCSDS telecommands. They are sent to UDP port 10025. The simulator.py script listens to this port. Commands  have no side effects. The script will only count them.


## Bundling

Running through Maven is useful during development, but it is not recommended for production environments. Instead bundle up your Yamcs application in a tar.gz file:

    mvn package
