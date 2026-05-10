from models.hole import Hole


def best_fit(process, holes_table, allocated_table):
    holes_table.sort_holes()

    if not process.segments:
        return True

    for segment in process.segments:
        best_hole = None

        for hole in list(holes_table.holes):
            if hole.size >= segment.size:
                if best_hole is None or hole.size < best_hole.size:
                    best_hole = hole

        if best_hole is not None:
            segment.base = best_hole.start_address
            best_hole.start_address += segment.size
            best_hole.size -= segment.size

            if best_hole.size == 0:
                holes_table.remove_hole(best_hole)

            allocated_table.add_segment(segment)
        else:
            for seg in allocated_table.get_process_segments(process.name):
                holes_table.add_hole(Hole(seg.base, seg.size))
                allocated_table.remove_segment(seg)
                seg.base = None

            holes_table.merge_adjacent()
            return False

    return True