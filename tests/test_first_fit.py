import pytest
from models.hole import Hole
from models.segment import Segment
from models.process import Process
from memory.tables import HolesTable, AllocatedTable
from memory.first_fit import first_fit


def make_tables(holes):
    """Helper — creates tables with given holes."""
    holes_table = HolesTable()
    for start, size in holes:
        holes_table.add_hole(Hole(start, size))
    return holes_table, AllocatedTable()


def make_process(name, segments):
    """Helper — creates process with given segments."""
    segs = [Segment(seg_name, seg_size, name) for seg_name, seg_size in segments]
    return Process(name, segs)


# ─────────────────────────────────────────
#  Basic Allocation
# ─────────────────────────────────────────

def test_first_fit_basic():
    """Single segment fits in first hole."""
    holes_table, allocated_table = make_tables([(0, 300)])
    process = make_process("P1", [("Code", 100)])

    first_fit(process, holes_table, allocated_table)

    assert process.is_fully_allocated == True
    assert process.segments[0].base == 0
    assert len(allocated_table.segments) == 1


def test_first_fit_picks_first_not_smallest():
    """First-Fit picks FIRST hole, not smallest."""
    # Holes: [300, 150, 500]  Segment needs 100
    # First-Fit should pick 300, NOT 150
    holes_table, allocated_table = make_tables([(0, 300), (400, 150), (700, 500)])
    process = make_process("P1", [("Code", 100)])

    first_fit(process, holes_table, allocated_table)

    assert process.segments[0].base == 0  # placed in first hole


def test_first_fit_multiple_segments():
    """Multiple segments all fit."""
    holes_table, allocated_table = make_tables([(0, 500)])
    process = make_process("P1", [("Code", 50), ("Data", 200), ("Stack", 100)])

    first_fit(process, holes_table, allocated_table)

    assert process.is_fully_allocated == True
    assert process.segments[0].base == 0    # Code at 0
    assert process.segments[1].base == 50   # Data at 50
    assert process.segments[2].base == 250  # Stack at 250


# ─────────────────────────────────────────
#  Hole Management
# ─────────────────────────────────────────

def test_first_fit_hole_shrinks():
    """Hole shrinks correctly after allocation."""
    holes_table, allocated_table = make_tables([(0, 300)])
    process = make_process("P1", [("Code", 100)])

    first_fit(process, holes_table, allocated_table)

    assert holes_table.holes[0].start_address == 100
    assert holes_table.holes[0].size == 200


def test_first_fit_hole_removed_on_exact_fit():
    """Hole is removed when segment fits exactly."""
    holes_table, allocated_table = make_tables([(0, 100)])
    process = make_process("P1", [("Code", 100)])

    first_fit(process, holes_table, allocated_table)

    assert len(holes_table.holes) == 0


def test_first_fit_uses_correct_hole():
    """Segment goes into first fitting hole, not any hole."""
    # Hole 1: size 50 (too small)
    # Hole 2: size 200 (fits!)
    holes_table, allocated_table = make_tables([(0, 50), (100, 200)])
    process = make_process("P1", [("Code", 100)])

    first_fit(process, holes_table, allocated_table)

    assert process.segments[0].base == 100  # placed in second hole


# ─────────────────────────────────────────
#  Failure Cases
# ─────────────────────────────────────────

def test_first_fit_no_hole_fits():
    """Process not allocated when no hole is big enough."""
    holes_table, allocated_table = make_tables([(0, 50)])
    process = make_process("P1", [("Code", 100)])

    first_fit(process, holes_table, allocated_table)

    assert process.is_fully_allocated == False


def test_first_fit_partial_failure_undoes_allocation():
    """If one segment fails, already allocated segments are undone."""
    # Only 150 KB total — Code(100) fits, Data(200) does NOT
    holes_table, allocated_table = make_tables([(0, 150)])
    process = make_process("P1", [("Code", 100), ("Data", 200)])

    first_fit(process, holes_table, allocated_table)

    assert process.is_fully_allocated == False
    assert len(allocated_table.segments) == 0       # nothing stays allocated
    assert process.segments[0].base is None          # Code was undone
    assert holes_table.holes[0].start_address == 0  # hole restored


def test_first_fit_no_holes():
    """Process not allocated when there are no holes at all."""
    holes_table, allocated_table = make_tables([])
    process = make_process("P1", [("Code", 100)])

    first_fit(process, holes_table, allocated_table)

    assert process.is_fully_allocated == False