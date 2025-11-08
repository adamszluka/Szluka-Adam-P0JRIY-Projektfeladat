from statistics import mean, median, stdev

class SADataStore:
    def __init__(self):
        self.entries = []

    def add_entry(self, day, distance):
        for d, _ in self.entries:
            if d == day:
                return False
        self.entries.append((day, distance))
        self.entries.sort(key=lambda x: x[0])
        return True

    def delete_indices(self, indices):
        indices_set = set(indices)
        new_entries = []
        for i, entry in enumerate(self.entries):
            if i not in indices_set:
                new_entries.append(entry)
        self.entries = new_entries

    def clear(self):
        self.entries = []

    def get_days(self):
        return [d for d, _ in self.entries]

    def get_distances(self):
        return [dist for _, dist in self.entries]

def calculate_stats_SA(values):
    if not values:
        return {"total": 0.0, "mean": 0.0, "median": 0.0, "stdev": 0.0}
    if len(values) == 1:
        v = float(values[0])
        return {"total": v, "mean": v, "median": v, "stdev": 0.0}
    vals = [float(v) for v in values]
    total = sum(vals)
    m = mean(vals)
    med = median(vals)
    try:
        s = stdev(vals)
    except Exception:
        s = 0.0
    return {"total": total, "mean": m, "median": med, "stdev": s}
