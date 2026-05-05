class Hole:
    def __init__(self, start_address, size):
        self.start_address = start_address
        self.size = size

    @property
    def end_address(self):
        return self.start_address + self.size - 1

    def __repr__(self):
        return f"Hole(start_address={self.start_address}, size={self.size}, end_address={self.end_address})"
