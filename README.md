
# Distributed DDoS Attack Simulator

**Disclaimer:**  
This project is designed strictly for educational purposes and controlled network security testing. Use this tool only in isolated, authorized environments. Unauthorized usage against public or private systems is illegal and unethical.

## Overview

This project implements a distributed simulation and planning tool for network attacks (DDoS) as part of a bachelor thesis. It consists of:

- A **Lead** server that loads or creates an attack plan, listens for incoming bot connections, and distributes the attack plan.
- A **Bot** client that connects to the Lead server, receives the attack plan, and executes the specified attacks.
- A set of **Attack** classes (e.g., **SynFloodAttack**, **ICMPFlood**, **UDPFlood**, **HTTPFlood**, **SlowLorisAttack**) that simulate various types of network attacks.
- A **Plan** class that serializes and deserializes attack plans in JSON format.
- A **DetailedLogger** class for granular logging and debugging with configurable options.

## Features

- **Modular Design:**  
  Each attack and core functionality is implemented in separate modules, making the project easy to extend and maintain.

- **Pluggable Attack Plan:**  
  The Lead server attempts to load an attack plan from a JSON file (`attack_plan.json`). If the file is missing or invalid, a fallback plan is used.

- **Attack Scheduling:**  
  Each attack can be scheduled to start at a precise time (with timezone support). If no start time is provided, the attack begins immediately.

- **Configurable Logging:**  
  Detailed logging is provided with multiple levels (INFO, DEBUG, WARNING, ERROR, CRITICAL). Command-line options allow you to control debug logging, extra printing, and statistics output.

- **Command-Line Flexibility:**  
  Both the Lead and Bot scripts support command-line arguments for configuration (e.g., IP, port, debug mode, logging options).

## Dependencies

- **Scapy:**  
  - [Scapy Documentation](https://scapy.readthedocs.io/en/latest/installation.html#installing-scapy-v2-x)  
  - Install via pip:
    ```bash
    pip install scapy
    ```
- **Npcap:**  
  - [Npcap Download](https://nmap.org/npcap/#download)  
  - Required for running Scapy on Windows.
- **Python 3.6+**  
  (for f-strings and timezone-aware datetime features)

## Installation

1. **Clone the Repository:**
    ```bash
    git clone https://github.com/yourusername/your-repo-name.git
    cd your-repo-name
    ```
2. **Install Dependencies:**
    ```bash
    pip install scapy
    ```
3. **(Windows Only)**  
   Download and install Npcap from [here](https://nmap.org/npcap/#download).

## Running Options

### Lead Server

To run the **Lead** server:

```bash
python lead.py [options]
```

### Lead Server Options Table

| Option       | Description                                                  | Default |
|--------------|--------------------------------------------------------------|---------|
| `-d`         | Enable debug logging                                         | False   |
| `-p`         | Disable extra console output (printing)                      | False   |
| `-s`         | Enable printing/logging of statistics on exit                | False   |
| `--no-trace` | Disable all logging, printing, and statistics                | False   |

### Default Configuration (when no options are provided)

| Setting          | Value     |
|------------------|-----------|
| Host             | localhost |
| Port             | 9999      |
| Debug            | False     |
| Extra Printing   | Enabled   |
| Statistics       | Enabled   |
| Tracing          | Enabled   |

**Example:**
```bash
python lead.py -d -s
```

---

### Bot Client

To run the **Bot** client:

```bash
python bot.py [lead_ip lead_port] [-d]
```

### Bot Client Options Table

| Argument(s)               | Description                                   |
|---------------------------|-----------------------------------------------|
| `[lead_ip lead_port]`     | Connect to a specific Lead server (optional)  |
| `-d`                      | Enable debug logging                          |

### Examples

**Fallback (no arguments):**

```bash
python bot.py
```
*Connects to `localhost:9999` without debug logging.*

**Custom host/port with debug logging:**

```bash
python bot.py 192.168.0.5 8888 -d
```


## Attack Scheduling

Each attack can include an optional `start_time` (in ISO 8601 format with timezone). If no start time is provided, the attack begins immediately. The `wait_until_start()` method in the base `Attack` class ensures that each attack executes at its scheduled time.

## License

This project is licensed under the MIT License

## Contributing

Contributions are welcome! Please fork this repository and submit pull requests for any enhancements or bug fixes. Ensure your contributions adhere to the project’s coding standards and include proper documentation.
