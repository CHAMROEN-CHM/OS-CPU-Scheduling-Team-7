from collections import deque

# FCFS
def fcfs(processes):
    time = 0
    gantt = []

    processes = sorted(processes, key=lambda x: x.arrival)

    for p in processes:
        if time < p.arrival:
            time = p.arrival

        p.start_time = time
        time += p.burst
        p.completion_time = time

        gantt.append((p.pid, p.start_time, p.completion_time))

    return gantt


# SJF
def sjf(processes):
    time = 0
    gantt = []
    processes = processes[:]

    while processes:
        ready = [p for p in processes if p.arrival <= time]

        if not ready:
            time += 1
            continue

        p = min(ready, key=lambda x: x.burst)
        processes.remove(p)

        p.start_time = time
        time += p.burst
        p.completion_time = time

        gantt.append((p.pid, p.start_time, p.completion_time))

    return gantt


# SRT
def srt(processes):
    time = 0
    gantt = []
    current = None

    processes = processes[:]

    while True:
        ready = [p for p in processes if p.arrival <= time and p.remaining > 0]

        if not ready:
            if all(p.remaining == 0 for p in processes):
                break
            time += 1
            continue

        p = min(ready, key=lambda x: x.remaining)

        if current != p:
            gantt.append((p.pid, time, time+1))
            current = p
        else:
            gantt[-1] = (p.pid, gantt[-1][1], time+1)

        if p.start_time is None:
            p.start_time = time

        p.remaining -= 1
        time += 1

        if p.remaining == 0:
            p.completion_time = time

    return gantt


# Round Robin
def rr(processes, quantum=2):
    time = 0
    queue = deque()
    gantt = []

    processes = sorted(processes, key=lambda x: x.arrival)
    i = 0

    while queue or i < len(processes):

        while i < len(processes) and processes[i].arrival <= time:
            queue.append(processes[i])
            i += 1

        if not queue:
            time += 1
            continue

        p = queue.popleft()

        if p.start_time is None:
            p.start_time = time

        exec_time = min(quantum, p.remaining)
        gantt.append((p.pid, time, time + exec_time))

        time += exec_time
        p.remaining -= exec_time

        while i < len(processes) and processes[i].arrival <= time:
            queue.append(processes[i])
            i += 1

        if p.remaining > 0:
            queue.append(p)
        else:
            p.completion_time = time

    return gantt