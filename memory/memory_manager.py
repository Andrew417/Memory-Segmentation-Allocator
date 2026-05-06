from models.hole import Hole
from models.process import Process
from memory.tables import AllocatedTable, HolesTable
from memory.first_fit import first_fit
from memory.best_fit import best_fit

class MemoryManager:
    def __init__(self,total_memory):
        self.processes = []
        self.memory_size = total_memory
        self.allocated_table = AllocatedTable()
        self.holes_table = HolesTable()


    def allocate_process(self, process, strategy):
        if strategy == 'first_fit':
            first_fit(process, self.holes_table, self.allocated_table)
        elif strategy == 'best_fit':
            best_fit(process, self.holes_table, self.allocated_table)

    def deallocate_process(self, process_name):
        segments = list(self.allocated_table.get_process_segments(process_name))

        if not segments:
            print(f"Process {process_name} not found!")
            return False

        for segment in segments:
            self.holes_table.add_hole(Hole(segment.base, segment.size))
            self.allocated_table.remove_segment(segment)
            segment.base = None

        self.processes = [p for p in self.processes if p.name != process_name]
        self.merge_holes()

    def merge_holes(self):
        self.holes_table.sort_holes()
        merged = []
        for hole in self.holes_table.holes:
            if merged and merged[-1].end_address + 1 == hole.start_address:
                merged[-1].size += hole.size  
            else:
                merged.append(hole)           
        self.holes_table.holes = merged