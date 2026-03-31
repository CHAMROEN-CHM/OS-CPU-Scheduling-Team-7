"""
File I/O — load processes from CSV or JSON (no priority field).

CSV format:
  pid,arrival_time,burst_time
  P1,0,5

JSON format:
  [{"pid":"P1","arrival_time":0,"burst_time":5}, ...]
"""

import csv, json
from typing import List
from algorithms import Process


def load_from_csv(filepath: str) -> List[Process]:
    procs = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid     = row.get("pid", row.get("PID", "")).strip()
            arrival = int(row.get("arrival_time", row.get("arrival", 0)))
            burst   = int(row.get("burst_time",   row.get("burst",   1)))
            if pid:
                procs.append(Process(pid, arrival, burst))
    return procs


def load_from_json(filepath: str) -> List[Process]:
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    procs = []
    for item in data:
        pid     = str(item.get("pid", "")).strip()
        arrival = int(item.get("arrival_time", item.get("arrival", 0)))
        burst   = int(item.get("burst_time",   item.get("burst",   1)))
        if pid:
            procs.append(Process(pid, arrival, burst))
    return procs


def load_file(filepath: str) -> List[Process]:
    if filepath.lower().endswith(".csv"):
        return load_from_csv(filepath)
    elif filepath.lower().endswith(".json"):
        return load_from_json(filepath)
    raise ValueError(f"Unsupported file type: {filepath}")


def export_results_csv(filepath: str, metrics: dict, algorithm: str):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([f"Algorithm: {algorithm}"])
        w.writerow(["PID","Arrival","Burst","Start","Finish",
                    "Waiting Time","Turnaround Time","Response Time"])
        for r in metrics["rows"]:
            w.writerow([r["pid"], r["arrival"], r["burst"],
                        r["start"], r["finish"],
                        r["waiting"], r["turnaround"], r["response"]])
        w.writerow([])
        w.writerow(["","","","","Averages",
                    f"{metrics['avg_wt']:.2f}",
                    f"{metrics['avg_tat']:.2f}",
                    f"{metrics['avg_rt']:.2f}"])
