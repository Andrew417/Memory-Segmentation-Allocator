class Segment:
    def __init__(self, name, size, process_name, base=None,):
        self.name = name
        self.base = base
        self.size = size
        self.process_name = process_name

    @property
    def end_address(self):
        if self.base is None:
            return None
        return self.base + self.size - 1
    
    @property
    def is_allocated(self):
        return self.base is not None

    def __repr__(self):
        return f"Segment(name={self.name}, base={self.base}, size={self.size}, end_address={self.end_address}, process={self.process_name})"
