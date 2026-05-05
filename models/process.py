class Process:
    def __init__(self, name, segments=None):
        self.name = name
        self.segments = segments if segments is not None else []

    @property
    def no_segments(self):
        return len(self.segments)

    @property
    def total_size(self):
        return sum(seg.size for seg in self.segments)

    @property
    def is_fully_allocated(self):
        return all(seg.is_allocated for seg in self.segments)

    def __repr__(self):
        return f"Process(name={self.name}, no_segments={self.no_segments}, total_size={self.total_size})"