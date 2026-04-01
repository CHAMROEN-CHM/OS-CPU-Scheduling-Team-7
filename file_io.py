import csv, json
from algorithms import Process

def load_from_csv(path):
    procs = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pid  = row.get("pid", row.get("PID","")).strip()
            arr  = int(row.get("arrival_time", row.get("arrival", 0)))
            bst  = int(row.get("burst_time",   row.get("burst",   1)))
            if pid: procs.append(Process(pid, arr, bst))
    return procs

def load_from_json(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    procs = []
    for item in data:
        pid = str(item.get("pid","")).strip()
        arr = int(item.get("arrival_time", item.get("arrival",0)))
        bst = int(item.get("burst_time",   item.get("burst",  1)))
        if pid: procs.append(Process(pid, arr, bst))
    return procs

def load_file(path):
    if path.lower().endswith(".csv"):  return load_from_csv(path)
    if path.lower().endswith(".json"): return load_from_json(path)
    raise ValueError("Unsupported file type")

def export_results_csv(path, metrics, algorithm):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([f"Algorithm: {algorithm}"])
        w.writerow(["PID","Arrival","Burst","Start","Finish",
                    "Waiting","Turnaround","Response"])
        for r in metrics["rows"]:
            w.writerow([r["pid"],r["arrival"],r["burst"],
                        r["start"],r["finish"],
                        r["waiting"],r["turnaround"],r["response"]])
        w.writerow([])
        w.writerow(["","","","","Averages",
                    f"{metrics['avg_wt']:.2f}",
                    f"{metrics['avg_tat']:.2f}",
                    f"{metrics['avg_rt']:.2f}"])