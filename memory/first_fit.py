from models.hole import Hole


def first_fit(process, holes_table, allocated_table):
    holes_table.sort_holes()

    if not process.segments:
        return True

    for segment in process.segments:
        allocated = False

        for hole in list(holes_table.holes):
            if hole.size >= segment.size:
                segment.base = hole.start_address
                hole.start_address += segment.size
                hole.size -= segment.size

                if hole.size == 0:
                    holes_table.remove_hole(hole)

                allocated_table.add_segment(segment)
                allocated = True
                break

        if not allocated:
            for seg in allocated_table.get_process_segments(process.name):
                holes_table.add_hole(Hole(seg.base, seg.size))
                allocated_table.remove_segment(seg)
                seg.base = None

            holes_table.merge_adjacent()
            return False

    return True