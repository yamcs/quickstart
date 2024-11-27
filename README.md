BOSSY - Basic Open-source Spacecraft Simulator with Yamcs

### Clone the repository
```
git clone https://github.com/Meridian-Space-Command/BOSSY.git
```

### Change directory to BOSSY
```
cd BOSSY
```

### Checkout the "basic" branch
```
git checkout basic
```

### Open two terminals

One terminal for the Yamcs server:
```
cd MCS
./mvnw clean && ./mvnw compile && ./mvnw yamcs:run
```

One terminal for the simulator:
```
cd SIM
```

- Edit the config.py file to set the initial state of the simulation, spacecraft, environment, orbit, etc.

Run the simulator from this terminal:
```
python3 simulator.py
```

## Considerations
- As a BASIC simulator, the subsystems are not fully representative of real spacecraft subsystems. 
- The simulator does not yet fully support all the commands and telemetry.
- Some telemetry are shown, but not simulated properly (i.e. are not updated, just init values).
- This project is a work in progress.
