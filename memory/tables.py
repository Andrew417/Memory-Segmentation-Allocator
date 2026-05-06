class HolesTable:
    def __init__(self, holes = None):
        self.holes = holes if holes is not None else []

    def add_hole(self, hole):
        self.holes.append(hole)

    def remove_hole(self, hole):
        self.holes.remove(hole)

    def sort_holes(self):
        self.holes.sort(key=lambda hole: hole.start_address)

    def __repr__(self):
        return f"HolesTable(holes={len(self.holes)})"   


class AllocatedTable:
    def __init__(self, segments = None):
        self.segments = segments if segments is not None else []

    def add_segment(self, segment):
        self.segments.append(segment)

    def remove_segment(self, segment):
        self.segments.remove(segment)

    def sort_segments(self):
        self.segments.sort(key=lambda segment: segment.base)

    def get_process_segments(self, process_name):
        return [seg for seg in self.segments if seg.process_name == process_name]

    def __repr__(self):
        return f"AllocatedTable(segments={len(self.segments)})"