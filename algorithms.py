"""
CPU Scheduling Algorithms
Implements: FCFS, SJF (Non-preemptive), SRT (Preemptive), Round Robin, MLFQ
"""

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
    queue_level: int = field(default=0, init=False)
    age: int = field(default=0, init=False)

    def __post_init__(self):
        self.remaining_time = self.burst_time

    @property
    def waiting_time(self) -> int:
        return self.turnaround_time - self.burst_time

    @property
    def turnaround_time(self) -> int:
        if self.finish_time is None:
            return 0
        return self.finish_time - self.arrival_time

    @property
    def response_time(self) -> int:
        if self.start_time is None:
            return 0
        return self.start_time - self.arrival_time


GanttEntry = Tuple[str, int, int]   # (pid or "IDLE", start, end)


def _clone(processes: List[Process]) -> List[Process]:
    return [Process(p.pid, p.arrival_time, p.burst_time) for p in processes]


# ── 1. FCFS ──────────────────────────────────────────────────────────────────
def fcfs(processes: List[Process]) -> Tuple[List[Process], List[GanttEntry]]:
    procs = sorted(_clone(processes), key=lambda p: (p.arrival_time, p.pid))
    gantt: List[GanttEntry] = []
    time = 0
    for p in procs:
        if time < p.arrival_time:
            gantt.append(("IDLE", time, p.arrival_time))
            time = p.arrival_time
        p.start_time = time
        p.finish_time = time + p.burst_time
        gantt.append((p.pid, time, p.finish_time))
        time = p.finish_time
    return procs, gantt


# ── 2. SJF Non-preemptive ────────────────────────────────────────────────────
def sjf(processes: List[Process]) -> Tuple[List[Process], List[GanttEntry]]:
    procs = _clone(processes)
    remaining = list(procs)
    gantt: List[GanttEntry] = []
    done = []
    time = 0
    while remaining:
        available = [p for p in remaining if p.arrival_time <= time]
        if not available:
            nxt = min(p.arrival_time for p in remaining)
            gantt.append(("IDLE", time, nxt))
            time = nxt
            continue
        chosen = min(available, key=lambda p: (p.burst_time, p.arrival_time, p.pid))
        remaining.remove(chosen)
        chosen.start_time = time
        chosen.finish_time = time + chosen.burst_time
        gantt.append((chosen.pid, time, chosen.finish_time))
        time = chosen.finish_time
        done.append(chosen)
    return done, gantt


# ── 3. SRT Preemptive ────────────────────────────────────────────────────────
def srt(processes: List[Process]) -> Tuple[List[Process], List[GanttEntry]]:
    procs = _clone(processes)
    procs.sort(key=lambda p: p.arrival_time)
    source = list(procs)
    ready = []
    done = []
    gantt: List[GanttEntry] = []
    time = 0
    current: Optional[Process] = None
    seg_start = 0

    while len(done) < len(procs):
        # admit newly arrived
        for p in source:
            if p.arrival_time <= time and p not in ready and p not in done:
                ready.append(p)

        if not ready:
            nxt = min(p.arrival_time for p in source if p not in done)
            if current is not None and seg_start < time:
                gantt.append((current.pid, seg_start, time))
                current = None
            gantt.append(("IDLE", time, nxt))
            time = nxt
            continue

        best = min(ready, key=lambda p: (p.remaining_time, p.arrival_time, p.pid))

        if current is not best:
            if current is not None and seg_start < time:
                gantt.append((current.pid, seg_start, time))
            current = best
            seg_start = time
            if current.start_time is None:
                current.start_time = time

        # next event: next arrival or this process finishing
        future = [p.arrival_time for p in source
                  if p.arrival_time > time and p not in ready and p not in done]
        future.append(time + current.remaining_time)
        nxt = min(future)

        elapsed = nxt - time
        current.remaining_time -= elapsed
        time = nxt

        if current.remaining_time == 0:
            current.finish_time = time
            gantt.append((current.pid, seg_start, time))
            done.append(current)
            ready.remove(current)
            current = None
            seg_start = time

    return done, gantt


# ── 4. Round Robin ───────────────────────────────────────────────────────────
def round_robin(processes: List[Process], quantum: int) -> Tuple[List[Process], List[GanttEntry]]:
    procs = sorted(_clone(processes), key=lambda p: (p.arrival_time, p.pid))
    queue: deque = deque()
    in_queue: set = set()
    remaining = list(procs)
    done = []
    gantt: List[GanttEntry] = []
    time = 0

    def enqueue():
        for p in remaining:
            if p.arrival_time <= time and p.pid not in in_queue and p not in done:
                queue.append(p)
                in_queue.add(p.pid)

    enqueue()

    while remaining:
        if not queue:
            nxt = min(p.arrival_time for p in remaining if p not in done)
            gantt.append(("IDLE", time, nxt))
            time = nxt
            enqueue()
            continue

        p = queue.popleft()
        if p.start_time is None:
            p.start_time = time

        run = min(quantum, p.remaining_time)
        gantt.append((p.pid, time, time + run))
        p.remaining_time -= run
        time += run
        enqueue()

        if p.remaining_time == 0:
            p.finish_time = time
            done.append(p)
            remaining.remove(p)
        else:
            queue.append(p)
            in_queue.add(p.pid)

    return done, gantt


# ── 5. MLFQ ──────────────────────────────────────────────────────────────────
AGING_THRESHOLD = 10


def mlfq(processes: List[Process],
         quanta: List[Optional[int]] = None,
         aging_threshold: int = AGING_THRESHOLD) -> Tuple[List[Process], List[GanttEntry]]:

    if quanta is None:
        quanta = [2, 4, None]

    procs = _clone(processes)
    procs.sort(key=lambda p: p.arrival_time)

    num_q = len(quanta)
    queues: List[deque] = [deque() for _ in range(num_q)]
    in_queue: dict = {}   # pid -> level
    done_pids: set = set()
    remaining = list(procs)
    done = []
    gantt: List[GanttEntry] = []
    time = 0

    def enqueue():
        for p in remaining:
            if p.arrival_time <= time and p.pid not in in_queue and p.pid not in done_pids:
                p.queue_level = 0
                queues[0].append(p)
                in_queue[p.pid] = 0

    def aging():
        for lvl in range(1, num_q):
            promote = [p for p in queues[lvl] if p.age >= aging_threshold]
            for p in promote:
                queues[lvl].remove(p)
                p.age = 0
                target = lvl - 1
                p.queue_level = target
                queues[target].append(p)
                in_queue[p.pid] = target

    enqueue()

    while len(done) < len(procs):
        # pick highest-priority non-empty queue
        lvl = next((i for i, q in enumerate(queues) if q), None)

        if lvl is None:
            waiting = [p for p in remaining if p.pid not in in_queue and p.pid not in done_pids]
            if waiting:
                nxt = min(p.arrival_time for p in waiting)
                gantt.append(("IDLE", time, nxt))
                time = nxt
                enqueue()
            continue

        p = queues[lvl].popleft()
        del in_queue[p.pid]

        if p.start_time is None:
            p.start_time = time

        q_time = quanta[lvl]
        run = p.remaining_time if q_time is None else min(q_time, p.remaining_time)

        if run > 0:
            gantt.append((p.pid, time, time + run))
        p.remaining_time -= run
        time += run
        p.age = 0

        enqueue()
        aging()

        if p.remaining_time == 0:
            p.finish_time = time
            done.append(p)
            done_pids.add(p.pid)
            remaining[:] = [x for x in remaining if x.pid != p.pid]
        else:
            nxt_lvl = min(lvl + 1, num_q - 1)
            p.queue_level = nxt_lvl
            queues[nxt_lvl].append(p)
            in_queue[p.pid] = nxt_lvl

    return done, gantt


# ── Metrics ───────────────────────────────────────────────────────────────────
def compute_metrics(procs: List[Process]) -> dict:
    rows = sorted([{
        "pid":        p.pid,
        "arrival":    p.arrival_time,
        "burst":      p.burst_time,
        "start":      p.start_time,
        "finish":     p.finish_time,
        "waiting":    p.waiting_time,
        "turnaround": p.turnaround_time,
        "response":   p.response_time,
    } for p in procs], key=lambda x: x["pid"])

    n = len(rows)
    return {
        "rows":    rows,
        "avg_wt":  sum(r["waiting"]    for r in rows) / n,
        "avg_tat": sum(r["turnaround"] for r in rows) / n,
        "avg_rt":  sum(r["response"]   for r in rows) / n,
    }
