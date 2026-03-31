class Process:
    def __init__(self, pid, arrival, burst):
        self.pid = pid
        self.arrival = arrival
        self.burst = burst
        self.remaining = burst

        self.start_time = None
        self.completion_time = 0

    def reset(self):
        self.remaining = self.burst
        self.start_time = None
        self.completion_time = 0