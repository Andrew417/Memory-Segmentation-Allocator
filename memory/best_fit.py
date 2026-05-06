def best_fit(process, holes_table, allocated_table):
    holes_table.sort_holes()
    for segment in process.segments:
        best_hole = None
        for hole in holes_table.holes:
            if hole.size >= segment.size:
                if best_hole is None or hole.size < best_hole.size:
                    best_hole = hole

        if best_hole is not None:
            segment.base = best_hole.start_address

            best_hole.size -= segment.size
            best_hole.start_address += segment.size

            if best_hole.size == 0:
                holes_table.remove_hole(best_hole)

            allocated_table.add_segment(segment)