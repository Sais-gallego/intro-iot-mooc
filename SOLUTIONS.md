# Introduction to the Internet of Things (IoT) MOOC — Comprehensive Study Guide & Reference Solutions

**Course:** Introduction to the Internet of Things MOOC (3 ECTS) — University of Helsinki, Faculty of Science, Department of Computer Science.  
**Platform:** [MOOC.fi](https://iot.mooc.fi)  
**Student & Author:** Sergio Andrés Ipuz Saavedra (`@Sais-gallego`, `afranklinromero@gmail.com`)

---

## Executive Summary & IoT System Architecture

The Internet of Things (IoT) transforms everyday physical artifacts into active network entities capable of autonomous sensing, computation, actuation, and distributed collaboration.

The canonical IoT reference architecture spans five hierarchical tiers:

```
+-----------------------------------------------------------+
| 5. Application Layer                                      |
|    (Smart Cities, Industrial Automation, eHealth, Agritech)|
+-----------------------------------------------------------+
                             |
+-----------------------------------------------------------+
| 4. Data Management & Analytics Layer                      |
|    (Cloud Time-Series DBs, Edge Windowing, Stream ML)     |
+-----------------------------------------------------------+
                             |
+-----------------------------------------------------------+
| 3. Networking & Transport Layer                           |
|    (CoAP/UDP, MQTT/TCP, 6LoWPAN, RPL, LoRaWAN, BLE)       |
+-----------------------------------------------------------+
                             |
+-----------------------------------------------------------+
| 2. Embedded Software & Operating System Layer             |
|    (FreeRTOS, Zephyr, RIOT, Low-Power Schedulers, PIP)    |
+-----------------------------------------------------------+
                             |
+-----------------------------------------------------------+
| 1. Perception & Sensing Layer                             |
|    (Transducers, ADC Quantization, Signal Conditioning)   |
+-----------------------------------------------------------+
```

---

## Chapter 1: Introduction to IoT & Hardware Foundations

### 1.1 Architecture & Device Taxonomy
Constrained IoT nodes are classified by IETF RFC 7228 into three distinct capability classes:
- **Class 0 ($< 10\text{ KiB}$ RAM, $< 100\text{ KiB}$ Flash):** Highly constrained sensor motes; cannot directly support native IP stacks without proxy gateways.
- **Class 1 ($\sim 10\text{ KiB}$ RAM, $\sim 100\text{ KiB}$ Flash):** Capable of running optimized IP stacks (6LoWPAN, CoAP, DTLS) without full HTTP/TLS overhead.
- **Class 2 ($\sim 50\text{ KiB}$ RAM, $\sim 250\text{ KiB}$ Flash):** Can run embedded Linux or full-featured RTOS (Zephyr, FreeRTOS), supporting multiple communication stacks concurrently.

### 1.2 Low-Power States & Energy Harvesting
To achieve multi-year lifespans on coin cells (e.g. CR2032, $240\text{ mAh}$), MCUs cycle between power regimes:
- **Active Mode ($10 - 25\text{ mA}$):** CPU executes instructions at full clock frequency ($32 - 80\text{ MHz}$).
- **Idle Mode ($1 - 3\text{ mA}$):** CPU core halted; peripheral clocks (DMA, timers) remain active.
- **Standby Mode ($20 - 50\ \mu\text{A}$):** High-speed oscillators powered down; low-frequency RTC ($32.768\text{ kHz}$) active.
- **Deep Sleep Mode ($1 - 3\ \mu\text{A}$):** SRAM state partially retained; wake-up strictly triggered by external interrupt or watchdog.

Energy-neutral operation criterion for ambient harvesting (Solar, TEG):
$$P_{\text{harvest\_avg}} \ge \delta \cdot P_{\text{active}} + (1 - \delta) \cdot P_{\text{sleep}}$$
where $\delta = \frac{T_{\text{active}}}{T_{\text{period}}}$ is the system duty cycle.

---

## Chapter 2: Embedded Operating Systems and Real-Time Scheduling

### 2.1 Embedded OS Architectures
Unlike general-purpose OSes (Linux, Windows) requiring megabytes of RAM and MMUs, embedded IoT OSes operate under strict footprint constraints:
- **Event-Driven Cooperative (e.g., Contiki-OS / Protothreads):** Tasks run to completion or explicitly yield control. Extremely low memory overhead (shared single stack), but vulnerable to unbounded task execution blocking the CPU.
- **Preemptive Multi-Threaded RTOS (e.g., FreeRTOS, Zephyr, RIOT):** Priority-based preemptive scheduling with individual task stacks. Guarantees deterministic interrupt latency and bounded context switching overhead.

### 2.2 Priority Inversion & Priority Inheritance Protocol (PIP)
When a high-priority task ($T_{\text{high}}$) is blocked waiting for a shared mutex held by a low-priority task ($T_{\text{low}}$), a medium-priority task ($T_{\text{med}}$) can preempt $T_{\text{low}}$, indefinitely delaying $T_{\text{high}}$ (the Mars Pathfinder anomaly).

**Solution (Priority Inheritance):**
As soon as $T_{\text{high}}$ attempts to acquire the mutex owned by $T_{\text{low}}$, the scheduler temporarily boosts $T_{\text{low}}$'s priority to $\text{prio}(T_{\text{high}})$. This prevents intermediate tasks ($T_{\text{med}}$) from preempting $T_{\text{low}}$ until it exits the critical section and releases the mutex.

---

## Chapter 3: Sensing Layer & Digital Signal Conditioning

### 3.1 Analog-to-Digital Conversion (ADC)
Transducers convert physical phenomena into analog voltages $V_{\text{in}} \in [0, V_{\text{ref}}]$.
- **Quantization Step (LSB Voltage):**
  $$\Delta V = \frac{V_{\text{ref}}}{2^N - 1}$$
- **Digital Output Code:**
  $$D = \text{round}\left(\frac{V_{\text{in}}}{\Delta V}\right)$$
- **Theoretical Signal-to-Quantization-Noise Ratio:**
  $$\text{SQNR}_{\text{dB}} \approx 6.02 \cdot N + 1.76\text{ dB}$$

### 3.2 Nyquist-Shannon Sampling & Anti-Aliasing
To perfectly reconstruct a continuous band-limited signal, the sampling frequency $f_s$ must satisfy:
$$f_s \ge 2 f_{\text{max}}$$
If $f_s < 2 f_{\text{max}}$, high frequencies fold back into the baseband:
$$f_{\text{alias}} = |f - k \cdot f_s|$$

### 3.3 Discrete-Time Signal Filtering
1. **Moving Average (FIR Filter):**
   $$y[n] = \frac{1}{W} \sum_{k=0}^{W-1} x[n-k]$$
2. **Exponential Moving Average (IIR Low-Pass Filter):**
   $$y[n] = \alpha x[n] + (1 - \alpha) y[n-1], \quad \alpha \in (0, 1]$$
3. **1D Discrete Kalman Filter (Optimal MMSE State Estimator):**
   $$\text{Predict:} \quad \hat{x}_k^- = \hat{x}_{k-1}, \quad P_k^- = P_{k-1} + Q$$
   $$\text{Kalman Gain:} \quad K_k = \frac{P_k^-}{P_k^- + R}$$
   $$\text{Update:} \quad \hat{x}_k = \hat{x}_k^- + K_k(z_k - \hat{x}_k^-), \quad P_k = (1 - K_k) P_k^-$$

---

## Chapter 4: IoT Networking Protocols & LPWAN

### 4.1 CoAP (Constrained Application Protocol - RFC 7252)
A binary RESTful application protocol designed over UDP for constrained IP networks:
- **Header:** Fixed 4-byte compact header (Version, Type: CON/NON/ACK/RST, Token Length, Code, Message ID).
- **Asynchronous Publish/Observe (RFC 7641):** Clients register interest in resources; servers stream state changes without polling.
- **Transport:** UDP + optional DTLS (Datagram Transport Layer Security).

### 4.2 MQTT (Message Queuing Telemetry Transport - ISO/IEC 20922)
A lightweight publish/subscribe messaging protocol over TCP:
- **Topic Hierarchy & Wildcards:**
  - `+` (Single-level wildcard): `home/+/temperature` matches `home/kitchen/temperature`.
  - `#` (Multi-level wildcard): `factory/#` matches all descendants.
- **Quality of Service (QoS):**
  - **QoS 0 (At most once):** Fire-and-forget, no acknowledgement.
  - **QoS 1 (At least once):** Packet acknowledged via `PUBACK`; duplicated on retransmission.
  - **QoS 2 (Exactly once):** Four-step handshake (`PUBLISH` $\to$ `PUBREC` $\to$ `PUBREL` $\to$ `PUBCOMP`).

### 4.3 LoRaWAN & Chirp Spread Spectrum (CSS)
Long-range, low-power LPWAN operating in sub-GHz ISM bands (EU868, US915):
- **Symbol Duration:**
  $$T_{\text{sym}} = \frac{2^{\text{SF}}}{\text{BW}}$$
- **Time-on-Air (ToA):**
  $$T_{\text{ToA}} = T_{\text{preamble}} + N_{\text{payload}} \cdot T_{\text{sym}}$$
- **Regulatory Duty Cycle:** In EU868, transmitters are legally capped at $\le 1\%$ duty cycle ($36\text{ seconds/hour}$).

---

## Chapter 5: Data Management Layer & Edge Processing

### 5.1 Real-Time Stream Windowing
- **Tumbling Window:** Contiguous, non-overlapping intervals $[t_0, t_0 + W), [t_0 + W, t_0 + 2W)$.
- **Sliding Window:** Overlapping intervals with stride $S < W$, computing rolling statistics.

### 5.2 Edge Compression Algorithms
1. **Delta Encoding:** Encodes differences $\Delta_i = x_i - x_{i-1}$, compressing dynamic integer ranges.
2. **Run-Length Encoding (RLE):** Collapses consecutive runs of identical sensor states $(v, n)$.
3. **Deadband Filter (Piecewise Constant Compression):** Transmits updates only when $|x_t - x_{\text{last}}| \ge \epsilon$, saving up to $90\%$ of wireless transmissions.

---

## Chapter 6: IoT Security, Privacy & TinyML

### 6.1 Cryptographic Primitives for Constrained Nodes
- **Message Integrity & Authentication:** HMAC-SHA256 with Pre-Shared Keys (PSK).
- **Anti-Replay Sliding Window:** Tracks monotonic sequence numbers across a 64-bit sliding bitmask, mitigating radio packet replay attacks without persistent flash writes.

### 6.2 TinyML & Edge Intelligence
Deploying quantized neural networks (INT8/binary weights) directly onto Cortex-M microcontrollers ($< 256\text{ KiB}$ RAM) using frameworks like TensorFlow Lite for Microcontrollers (TFLM), eliminating privacy risks and cloud bandwidth costs.

---

## Test Verification

Execute all unit tests validating hardware, OS scheduling, sensing, networking, and security:

```bash
python -m unittest discover tests -v
```

Output:
```
Ran 25 tests in 0.002s
OK
```
