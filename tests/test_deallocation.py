import pytest
from models.hole import Hole
from models.segment import Segment
from models.process import Process
from memory.memory_manager import MemoryManager


def setup_manager(total_memory, holes, processes, strategy='first_fit'):
    """Helper — builds a fully set up MemoryManager."""
    manager = MemoryManager(total_memory)
    for start, size in holes:
        manager.holes_table.add_hole(Hole(start, size))
    for name, segments in processes:
        segs = [Segment(seg_name, seg_size, name) for seg_name, seg_size in segments]
        manager.allocate_process(Process(name, segs), strategy)
    return manager


# ─────────────────────────────────────────
#  Basic Deallocation
# ─────────────────────────────────────────

def test_deallocation_basic():
    """Process segments are removed from allocated table."""
    manager = setup_manager(
        total_memory=500,
        holes=[(0, 500)],
        processes=[("P1", [("Code", 100), ("Data", 200)])]
    )

    manager.deallocate_process("P1")

    assert len(manager.allocated_table.segments) == 0


def test_deallocation_segments_become_holes():
    """Freed segments become holes."""
    manager = setup_manager(
        total_memory=500,
        holes=[(0, 500)],
        processes=[("P1", [("Code", 100)])]
    )
    holes_before = len(manager.holes_table.holes)
    manager.deallocate_process("P1")

    assert len(manager.holes_table.holes) >= holes_before


def test_deallocation_process_removed_from_list():
    """Process is removed from processes list."""
    manager = setup_manager(
        total_memory=500,
        holes=[(0, 500)],
        processes=[("P1", [("Code", 100)])]
    )

    manager.deallocate_process("P1")

    assert not any(p.name == "P1" for p in manager.processes)


def test_deallocation_segment_base_reset():
    """Segment base is reset to None after deallocation."""
    manager = setup_manager(
        total_memory=500,
        holes=[(0, 500)],
        processes=[("P1", [("Code", 100)])]
    )
    segment = manager.allocated_table.segments[0]

    manager.deallocate_process("P1")

    assert segment.base is None


def test_deallocation_process_not_found():
    """Does nothing when process doesn't exist."""
    manager = MemoryManager(500)
    manager.holes_table.add_hole(Hole(0, 500))

    manager.deallocate_process("P99")

    assert not any(p.name == "P99" for p in manager.processes)


# ─────────────────────────────────────────
#  Hole Merging
# ─────────────────────────────────────────

def test_merge_left_neighbour():
    """Freed segment merges with left neighbouring hole only."""
    # Layout: [HOLE:0-99] [P1:Code:100-199]
    manager = MemoryManager(200)
    manager.holes_table.add_hole(Hole(0, 100))  # left hole only
    segs = [Segment("Code", 100, "P1", base=100)]
    manager.allocated_table.add_segment(segs[0])
    manager.processes.append(Process("P1", segs))

    manager.deallocate_process("P1")

    assert len(manager.holes_table.holes) == 1
    assert manager.holes_table.holes[0].start_address == 0
    assert manager.holes_table.holes[0].size == 200


def test_merge_right_neighbour():
    """Freed segment merges with right neighbouring hole."""
    # Layout: [P1:Code:0-99] [HOLE:100-299]
    manager = MemoryManager(300)
    manager.holes_table.add_hole(Hole(100, 200))  # right hole
    segs = [Segment("Code", 100, "P1", base=0)]
    manager.allocated_table.add_segment(segs[0])
    manager.processes.append(Process("P1", segs))

    manager.deallocate_process("P1")

    assert manager.holes_table.holes[0].start_address == 0
    assert manager.holes_table.holes[0].size == 300


def test_merge_both_neighbours():
    """Freed segment merges with both left and right neighbouring holes."""
    # Layout: [HOLE:0-99] [P1:Code:100-199] [HOLE:200-299]
    manager = MemoryManager(300)
    manager.holes_table.add_hole(Hole(0, 100))   # left hole
    manager.holes_table.add_hole(Hole(200, 100)) # right hole
    segs = [Segment("Code", 100, "P1", base=100)]
    manager.allocated_table.add_segment(segs[0])
    manager.processes.append(Process("P1", segs))

    manager.deallocate_process("P1")

    assert len(manager.holes_table.holes) == 1
    assert manager.holes_table.holes[0].start_address == 0
    assert manager.holes_table.holes[0].size == 300


def test_merge_chain():
    """Multiple adjacent holes all merge into one."""
    manager = MemoryManager(500)
    manager.holes_table.add_hole(Hole(0, 100))
    manager.holes_table.add_hole(Hole(100, 100))
    manager.holes_table.add_hole(Hole(200, 100))
    manager.holes_table.add_hole(Hole(300, 100))
    manager.holes_table.add_hole(Hole(400, 100))

    manager.merge_holes()

    assert len(manager.holes_table.holes) == 1
    assert manager.holes_table.holes[0].size == 500


def test_no_merge_non_adjacent():
    """Non-adjacent holes are NOT merged."""
    manager = MemoryManager(500)
    manager.holes_table.add_hole(Hole(0, 100))
    manager.holes_table.add_hole(Hole(200, 100))  # gap at 100-199

    manager.merge_holes()

    assert len(manager.holes_table.holes) == 2