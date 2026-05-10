from models.hole import Hole
from memory.tables import AllocatedTable, HolesTable
from memory.first_fit import first_fit
from memory.best_fit import best_fit


class MemoryManager:
    def __init__(self, total_memory):
        self.memory_size     = total_memory
        self.processes       = []
        self.holes_table     = HolesTable()
        self.allocated_table = AllocatedTable()

    def allocate_process(self, process, strategy):
        allocated = False
        if strategy == 'first_fit':
            allocated = first_fit(process, self.holes_table, self.allocated_table)
        elif strategy == 'best_fit':
            allocated = best_fit(process, self.holes_table, self.allocated_table)
        else:
            return False

        if allocated and process.is_fully_allocated:
            self.processes.append(process)
            return True

        return False

    def deallocate_process(self, process_name):
        segments = list(self.allocated_table.get_process_segments(process_name))

        if not segments:
            return False

        for segment in segments:
            self.holes_table.add_hole(Hole(segment.base, segment.size))
            self.allocated_table.remove_segment(segment)
            segment.base = None

        self.processes = [p for p in self.processes if p.name != process_name]
        self.merge_holes()
        return True

    def merge_holes(self):
        self.holes_table.merge_adjacent()