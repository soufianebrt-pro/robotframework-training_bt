# Robot Framework Wipers CAN Simulation

This repository contains a Robot Framework example that tests a simulated
automotive wiper system over a virtual CAN bus. The Python library models the
vehicle's CAN nodes, uses a DBC file to encode and decode messages, and records
the bus traffic. No physical CAN hardware is needed.

## Project layout

```text
.
├── .devcontainer/                         # Development-container setup
├── logs/                                  # Sample CAN trace files
├── wipers_bcm_sim_v3/
│   ├── CAN_Sim_Library_Wipers.py          # Robot Framework CAN simulation library
│   ├── wipers_fcn_bcm_logic.py            # BCM wiper behavior
│   ├── wipers_can_db_adv.dbc              # CAN messages, signals, and value tables
│   └── testcases/
│       └── wipers_bcm_testsuite_v1.robot  # Wiper behavior tests
├── requirements.txt                       # Robot Framework dependencies
└── README.md
```

## Prerequisites

- Python 3.8 or newer
- Robot Framework and the Python CAN/DBC libraries

Install the declared Python dependencies and the CAN simulation libraries:

```bash
python -m pip install -r requirements.txt
python -m pip install python-can cantools
```

The development container installs the dependencies in `requirements.txt`
automatically. The simulation also imports `python-can` and `cantools`, so
install those separately as shown above if they are not already available.

## Run the tests

From the repository root, run:

```bash
robot --outputdir results wipers_bcm_sim_v3/testcases/wipers_bcm_testsuite_v1.robot
```

The suite contains tests for:

- A manual fast-wiper command and the resulting `Wipers_Status` message.
- Automatic wiping with a valid rain-sensor status.

The suite records CAN traffic to `wipers_bcm_testrun_output.asc` in the current
working directory. Robot Framework writes its `output.xml`, `log.html`, and
`report.html` files to `results/`.

## Simulation overview

`CAN_Sim_Library_Wipers.py` creates virtual CAN nodes for the wiper switch,
body control module (BCM), rain sensor, wiper motor, and tester. The DBC file
defines their messages, signals, and enumerated values. When the test sends
input messages, the BCM logic updates and transmits the wiper status, which the
suite checks.

The library and DBC are located in `wipers_bcm_sim_v3/`; the Robot Framework
suite imports them using paths relative to its own directory.
