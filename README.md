# CPU Scheduling Algorithm Simulator

A desktop GUI application built with **Python + Tkinter** that simulates and compares
five CPU scheduling algorithms with real-time Gantt chart visualization and metrics.

---

## Features

| Feature | Details |
|---|---|
| Algorithms | FCFS, SJF (non-preemptive), SRT (preemptive), Round Robin, MLFQ |
| Visualization | Colour-coded scrollable Gantt chart + ASCII text Gantt |
| Metrics | Waiting Time, Turnaround Time, Response Time (per process + averages) |
| Input | Manual GUI form, CSV file, JSON file |
| Export | Results exportable to CSV |
| Compare | One-click "Run All" comparison table across all algorithms |

---

## Requirements

- Python 3.8+
- `tkinter` (usually bundled; on Ubuntu: `sudo apt install python3-tk`)

No third-party packages required.

---

## Installation & Running

```bash
# Clone / unzip the project
cd cpu_scheduler

# Run the application
python3 main.py
```

---

## File Structure

```
cpu_scheduler/
├── main.py            # Tkinter GUI application (entry point)
├── algorithms.py      # All 5 scheduling algorithms + metrics
├── gantt.py           # Gantt chart canvas widget
├── file_io.py         # CSV/JSON file loader + exporter
├── sample_processes.csv
├── sample_processes.json
└── README.md
```

---

## Algorithm Descriptions

### 1. FCFS – First Come First Serve
Processes are executed in the order they arrive. Simple, non-preemptive.
- **Data structure**: Sorted list by arrival time
- **Edge cases**: CPU idle time inserted when no process is ready

### 2. SJF – Shortest Job First (Non-preemptive)
Among all ready processes, the one with the shortest burst time runs next.
- **Data structure**: Priority selection from available list each dispatch
- **Note**: May cause starvation of long processes

### 3. SRT – Shortest Remaining Time (Preemptive)
Preemptive version of SJF. A running process is interrupted if a newly arrived
process has a shorter remaining time.
- **Preemption logic**: At every arrival event and completion event, re-evaluate
- **Tracking**: Remaining time decremented tick by tick (event-driven)

### 4. Round Robin (RR)
Each process gets a fixed time quantum. After the quantum expires, it is moved
to the back of the ready queue.
- **Data structure**: `collections.deque` as circular queue
- **Context switching**: After each quantum, newly arrived processes enqueued first

### 5. MLFQ – Multilevel Feedback Queue
Three-level queue with demotion on quantum expiry and promotion via aging:

| Queue | Algorithm | Quantum |
|---|---|---|
| Q0 (highest) | Round Robin | 2 |
| Q1 | Round Robin | 4 |
| Q2 (lowest) | FCFS | — |

- **Demotion**: A process that uses its full quantum is demoted one level
- **Aging**: A process waiting ≥ `aging_threshold` ticks in a lower queue is
  promoted up one level (prevents starvation)

---

## Sample Scenario

| Process | Arrival | Burst |
|---|---|---|
| P1 | 0 | 5 |
| P2 | 1 | 3 |
| P3 | 2 | 8 |
| P4 | 3 | 6 |

### Expected Results Summary

| Algorithm | Avg WT | Avg TAT | Avg RT |
|---|---|---|---|
| FCFS | 5.75 | 11.25 | 5.75 |
| SJF | 5.25 | 10.75 | 5.25 |
| SRT | 5.00 | 10.50 | 4.25 |
| Round Robin (q=2) | 9.75 | 15.25 | 2.00 |
| MLFQ (q=2,4,FCFS) | 10.50 | 14.50 | 1.50 |

---

## Loading Processes from File

**CSV format** (`sample_processes.csv`):
```csv
pid,arrival_time,burst_time,priority
P1,0,5,0
P2,1,3,0
```

**JSON format** (`sample_processes.json`):
```json
[
  {"pid": "P1", "arrival_time": 0, "burst_time": 5, "priority": 0}
]
```

Click **📂 Load File** in the GUI to import either format.

---

## How to Use the GUI

1. **Add processes** using the input fields and **＋ Add** button, or load from file.
2. Select an **algorithm** from the dropdown.
3. Set **RR Quantum** (for Round Robin) or **MLFQ Quanta** (for MLFQ).
4. Click **▶ RUN SIMULATION** to run the selected algorithm.
5. Click **⚡ Run All Algorithms** to run all 5 and see the comparison table.
6. Switch tabs to view **Metrics Table**, **Compare All**, or **Gantt Text**.
7. Click **💾 Export CSV** to save results.
