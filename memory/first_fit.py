def first_fit(process, holes_table, allocated_table):
    holes_table.sort_holes()
    for segment in process.segments:
        for hole in holes_table.holes:
            if hole.size >= segment.size:
                segment.base = hole.start_address

                hole.size -= segment.size
                hole.start_address += segment.size

                if hole.size == 0:
                    holes_table.remove_hole(hole)
                

                allocated_table.add_segment(segment)

                break