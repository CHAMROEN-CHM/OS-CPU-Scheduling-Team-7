from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from collections import deque

@dataclass
class Process:
    pid: str
    arrival_time: int
    burst_time: int
    remaining_time: int = field(init=False)
    start_time: Optional[int] = field(default=None, init=False)
    finish_time: Optional[int] = field(default=None, init=False)

    def __post_init__(self):
        self.remaining_time = self.burst_time

    @property
    def waiting_time(self):
        return self.turnaround_time - self.burst_time

    @property
    def turnaround_time(self):
        if self.finish_time is None: return 0
        return self.finish_time - self.arrival_time

    @property
    def response_time(self):
        if self.start_time is None: return 0
        return self.start_time - self.arrival_time

def _clone(processes):
    return [Process(p.pid, p.arrival_time, p.burst_time) for p in processes]

# FCFS
def fcfs(processes):
    procs = sorted(_clone(processes), key=lambda p: (p.arrival_time, p.pid))
    gantt, time = [], 0
    for p in procs:
        if time < p.arrival_time:
            gantt.append(("IDLE", time, p.arrival_time))
            time = p.arrival_time
        p.start_time = time
        p.finish_time = time + p.burst_time
        gantt.append((p.pid, time, p.finish_time))
        time = p.finish_time
    return procs, gantt

# SJF Non-preemptive
def sjf(processes):
    procs = _clone(processes)
    remaining, done, gantt, time = list(procs), [], [], 0
    while remaining:
        avail = [p for p in remaining if p.arrival_time <= time]
        if not avail:
            nxt = min(p.arrival_time for p in remaining)
            gantt.append(("IDLE", time, nxt)); time = nxt; continue
        p = min(avail, key=lambda x: (x.burst_time, x.arrival_time, x.pid))
        remaining.remove(p)
        p.start_time = time
        p.finish_time = time + p.burst_time
        gantt.append((p.pid, time, p.finish_time))
        time = p.finish_time
        done.append(p)
    return done, gantt

# SRT Preemptive
def srt(processes):
    procs = sorted(_clone(processes), key=lambda p: p.arrival_time)
    source, ready, done, gantt = list(procs), [], [], []
    time, current, seg_start = 0, None, 0
    while len(done) < len(procs):
        for p in source:
            if p.arrival_time <= time and p not in ready and p not in done:
                ready.append(p)
        if not ready:
            nxt = min(p.arrival_time for p in source if p not in done)
            if current and seg_start < time:
                gantt.append((current.pid, seg_start, time)); current = None
            gantt.append(("IDLE", time, nxt)); time = nxt; continue
        best = min(ready, key=lambda p: (p.remaining_time, p.arrival_time, p.pid))
        if current is not best:
            if current and seg_start < time:
                gantt.append((current.pid, seg_start, time))
            current = best; seg_start = time
            if current.start_time is None: current.start_time = time
        future = [p.arrival_time for p in source if p.arrival_time > time and p not in ready and p not in done]
        future.append(time + current.remaining_time)
        nxt = min(future)
        current.remaining_time -= (nxt - time); time = nxt
        if current.remaining_time == 0:
            current.finish_time = time
            gantt.append((current.pid, seg_start, time))
            done.append(current); ready.remove(current)
            current = None; seg_start = time
    return done, gantt

# Round Robin
def round_robin(processes, quantum):
    procs = sorted(_clone(processes), key=lambda p: (p.arrival_time, p.pid))
    queue, in_q, remaining, done, gantt, time = deque(), set(), list(procs), [], [], 0
    def enqueue():
        for p in remaining:
            if p.arrival_time <= time and p.pid not in in_q and p not in done:
                queue.append(p); in_q.add(p.pid)
    enqueue()
    while remaining:
        if not queue:
            nxt = min(p.arrival_time for p in remaining if p not in done)
            gantt.append(("IDLE", time, nxt)); time = nxt; enqueue(); continue
        p = queue.popleft()
        if p.start_time is None: p.start_time = time
        run = min(quantum, p.remaining_time)
        gantt.append((p.pid, time, time + run))
        p.remaining_time -= run; time += run; enqueue()
        if p.remaining_time == 0:
            p.finish_time = time; done.append(p); remaining.remove(p)
        else:
            queue.append(p); in_q.add(p.pid)
    return done, gantt

# MLFQ
def mlfq(processes, quanta=None, aging_threshold=10):
    if quanta is None: quanta = [2, 4, None]
    procs = sorted(_clone(processes), key=lambda p: p.arrival_time)
    num_q = len(quanta)
    queues = [deque() for _ in range(num_q)]
    in_queue, done_pids, remaining, done, gantt, time = {}, set(), list(procs), [], [], 0
    age = {}

    def enqueue():
        for p in remaining:
            if p.arrival_time <= time and p.pid not in in_queue and p.pid not in done_pids:
                queues[0].append(p); in_queue[p.pid] = 0; age[p.pid] = 0

    def do_aging():
        for lvl in range(1, num_q):
            promote = [p for p in list(queues[lvl]) if age.get(p.pid, 0) >= aging_threshold]
            for p in promote:
                queues[lvl].remove(p)
                target = lvl - 1
                queues[target].append(p); in_queue[p.pid] = target; age[p.pid] = 0

    enqueue()
    while len(done) < len(procs):
        lvl = next((i for i, q in enumerate(queues) if q), None)
        if lvl is None:
            waiting = [p for p in remaining if p.pid not in in_queue and p.pid not in done_pids]
            if waiting:
                nxt = min(p.arrival_time for p in waiting)
                gantt.append(("IDLE", time, nxt)); time = nxt; enqueue()
            continue
        p = queues[lvl].popleft(); del in_queue[p.pid]
        if p.start_time is None: p.start_time = time
        run = p.remaining_time if quanta[lvl] is None else min(quanta[lvl], p.remaining_time)
        if run > 0:
            gantt.append((p.pid, time, time + run))
        p.remaining_time -= run; time += run; age[p.pid] = 0
        # increment age for waiting processes
        for q in queues:
            for wp in q:
                if wp.pid != p.pid: age[wp.pid] = age.get(wp.pid, 0) + 1
        enqueue(); do_aging()
        if p.remaining_time == 0:
            p.finish_time = time; done.append(p); done_pids.add(p.pid)
            remaining[:] = [x for x in remaining if x.pid != p.pid]
        else:
            nxt_lvl = min(lvl + 1, num_q - 1)
            queues[nxt_lvl].append(p); in_queue[p.pid] = nxt_lvl
    return done, gantt

def compute_metrics(procs):
    rows = sorted([{
        "pid": p.pid, "arrival": p.arrival_time, "burst": p.burst_time,
        "start": p.start_time, "finish": p.finish_time,
        "waiting": p.waiting_time, "turnaround": p.turnaround_time,
        "response": p.response_time,
    } for p in procs], key=lambda x: x["pid"])
    n = len(rows)
    return {
        "rows": rows,
        "avg_wt":  sum(r["waiting"]    for r in rows) / n,
        "avg_tat": sum(r["turnaround"] for r in rows) / n,
        "avg_rt":  sum(r["response"]   for r in rows) / n,
    }