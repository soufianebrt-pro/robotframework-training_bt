This is the training for Test Automation using Robot Framework


# Virtual CAN Bus Testing with Robot Framework

This project demonstrates how to perform virtual Controller Area Network (CAN) communication testing using **Robot Framework**, **`python-can`**, and **`cantools`** with a custom DBC database (`wipers_can_db.dbc`). No physical CAN hardware is required, as everything runs on a virtual bus channel.

---

## Prerequisites

* Python 3.8 or higher installed on your system.

---

## Project Structure

```text
can_simulation/
│
├── FunctionSimulationLibrary.py          # Custom Python keyword library for CAN bus interaction
├── wipers_can_db.dbc      # DBC database file defining the messages and signals
├── wipers_test.robot      # Robot Framework test suite
└── README.md              # Project documentation

How It Works
------------

CanLibrary.py: Acts as a bridge. It uses cantools to load the DBC file and encode/decode signals, and python-can to manage a virtual bus channel with receive_own_messages=True enabled so loopback transmission can be tested locally.

wipers_can_db.dbc: Defines the BodyControlModule message (CAN ID 0x123) and the WiperMode signal mapping numeric values and textual states (e.g., 0 for Off, 3 for Fast).

wipers_test.robot: Contains the test cases that send commands, capture the frames on the virtual bus, decode them back via the DBC definition, and validate the expected values.