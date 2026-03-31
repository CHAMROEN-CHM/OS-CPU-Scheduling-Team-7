def calculate_metrics(processes):
    results = []

    total_wt = total_tat = total_rt = 0

    for p in processes:
        tat = p.completion_time - p.arrival
        wt = tat - p.burst
        rt = p.start_time - p.arrival

        total_wt += wt
        total_tat += tat
        total_rt += rt

        results.append((p.pid, p.arrival, p.burst,
                        p.start_time, p.completion_time,
                        wt, tat, rt))

    n = len(processes)

    avg = (
        total_wt / n,
        total_tat / n,
        total_rt / n
    )

    return results, avg