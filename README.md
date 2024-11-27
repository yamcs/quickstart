BOSSY - Basic Open-source Spacecraft Simulator with Yamcs

### Clone the repository
```
git clone https://github.com/bossy-space/BOSSY.git
```

### Checkout the "basic" branch
```
git checkout basic
```

### Open two terminals

One terminal for the Yamcs server:
```
cd BOSSY/MCS
./mvnw clean && ./mvnw compile && ./mvnw yamcs:run
```

One terminal for the simulator:
```
cd BOSSY/SIM
python3 simulator.py
```
## Considerations
- As a BASIC simulator, the subsystems are not fully representative of real spacecraft subsystems. 
- The simulator does not yet fully support all the commands and telemetry.
- Some telemetry are shown, but not simulated properly (i.e. are not updated, just init values).
- This project is a work in progress.
