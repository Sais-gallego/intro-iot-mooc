# Introduction to the Internet of Things (IoT) MOOC

[![IoT MOOC CI](https://github.com/Sais-gallego/intro-iot-mooc/actions/workflows/ci.yml/badge.svg)](https://github.com/Sais-gallego/intro-iot-mooc/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10 | 3.11 | 3.12](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)

Implementation of embedded hardware power modeling, RTOS preemptive priority scheduling with Priority Inheritance Protocol (PIP), analog sensing pipeline (ADC, Nyquist-Shannon sampling, 1D Kalman filter), IoT networking protocols (CoAP RFC 7252, MQTT Broker, LoRaWAN Time-on-Air), edge stream windowing/compression, and HMAC anti-replay security.

Developed for the **Introduction to the Internet of Things MOOC (3 ECTS)** at the **University of Helsinki**, Department of Computer Science.

---

## Architecture & Codebase Structure

```
intro-iot-mooc/
├── src/
│   ├── device_hardware.py       # MCU power modes, battery Peukert model, energy harvesting
│   ├── operating_systems.py     # RTOS task scheduler, Priority Inheritance Protocol (PIP)
│   ├── sensing_pipeline.py      # ADC quantization, Nyquist-Shannon validator, FIR/IIR & Kalman filter
│   ├── networking_protocols.py  # CoAP RFC 7252 / Observe RFC 7641, MQTT Broker, LoRaWAN ToA
│   ├── data_aggregation.py     # Stream tumbling/sliding windows, Delta/RLE/Deadband compression
│   ├── iot_security.py          # HMAC-SHA256 integrity, 64-bit sliding anti-replay window
│   └── __init__.py
├── tests/
│   ├── test_device_and_os.py    # Unit tests for hardware, battery, and RTOS scheduling
│   ├── test_sensing_pipeline.py # Unit tests for ADC, Nyquist theorem, and digital filters
│   ├── test_networking_protocols.py # Unit tests for CoAP, MQTT, and LoRaWAN modulation
│   └── test_data_and_security.py    # Unit tests for stream windowing, compression, and security
├── SOLUTIONS.md                 # Full 6-chapter theoretical guide & solutions manual
├── .github/workflows/ci.yml     # Multi-version Python GitHub Actions CI workflow
└── README.md
```

---

## Running Unit Tests

Run all 25 unit tests:

```bash
python -m unittest discover tests -v
```

---

## Author

**Sergio Andrés Ipuz Saavedra**  
Email: [afranklinromero@gmail.com](mailto:afranklinromero@gmail.com)  
GitHub: [@Sais-gallego](https://github.com/Sais-gallego)
