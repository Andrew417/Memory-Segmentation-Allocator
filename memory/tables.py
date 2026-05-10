class HolesTable:
    def __init__(self, holes = None):
        self.holes = holes if holes is not None else []

    def add_hole(self, hole):
        self.holes.append(hole)

    def remove_hole(self, hole):
        self.holes.remove(hole)

    def sort_holes(self):
        self.holes.sort(key=lambda hole: hole.start_address)

    def merge_adjacent(self):
        self.sort_holes()
        i = 0
        while i < len(self.holes) - 1:
            current = self.holes[i]
            next_hole = self.holes[i + 1]

            if current.end_address + 1 == next_hole.start_address:
                merged_end = max(current.end_address, next_hole.end_address)
                current.size = merged_end - current.start_address + 1
                self.remove_hole(next_hole)
            else:
                i += 1

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