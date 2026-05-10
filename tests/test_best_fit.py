import pytest
from models.hole import Hole
from models.segment import Segment
from models.process import Process
from memory.tables import HolesTable, AllocatedTable
from memory.best_fit import best_fit


def make_tables(holes):
    holes_table = HolesTable()
    for start, size in holes:
        holes_table.add_hole(Hole(start, size))
    return holes_table, AllocatedTable()


def make_process(name, segments):
    segs = [Segment(seg_name, seg_size, name) for seg_name, seg_size in segments]
    return Process(name, segs)


# ─────────────────────────────────────────
#  Basic Allocation
# ─────────────────────────────────────────

def test_best_fit_basic():
    """Single segment fits in a hole."""
    holes_table, allocated_table = make_tables([(0, 300)])
    process = make_process("P1", [("Code", 100)])

    best_fit(process, holes_table, allocated_table)

    assert process.is_fully_allocated == True
    assert process.segments[0].base == 0


def test_best_fit_picks_smallest_hole():
    """Best-Fit picks SMALLEST fitting hole, not first."""
    # Holes: [300, 150, 500]  Segment needs 100
    # Best-Fit should pick 150, NOT 300
    holes_table, allocated_table = make_tables([(0, 300), (400, 150), (700, 500)])
    process = make_process("P1", [("Code", 100)])

    best_fit(process, holes_table, allocated_table)

    assert process.segments[0].base == 400  # placed in smallest fitting hole


def test_best_fit_exact_fit_preferred():
    """Best-Fit prefers exact size hole."""
    # Holes: [200, 100, 500]  Segment needs 100
    # Best-Fit should pick 100 (exact fit)
    holes_table, allocated_table = make_tables([(0, 200), (300, 100), (500, 500)])
    process = make_process("P1", [("Code", 100)])

    best_fit(process, holes_table, allocated_table)

    assert process.segments[0].base == 300  # placed in exact fit hole


def test_best_fit_multiple_segments():
    """Multiple segments all fit."""
    holes_table, allocated_table = make_tables([(0, 500)])
    process = make_process("P1", [("Code", 50), ("Data", 200), ("Stack", 100)])

    best_fit(process, holes_table, allocated_table)

    assert process.is_fully_allocated == True
    assert len(allocated_table.segments) == 3


# ─────────────────────────────────────────
#  Hole Management
# ─────────────────────────────────────────

def test_best_fit_hole_shrinks():
    """Hole shrinks correctly after allocation."""
    holes_table, allocated_table = make_tables([(0, 300)])
    process = make_process("P1", [("Code", 100)])

    best_fit(process, holes_table, allocated_table)

    assert holes_table.holes[0].size == 200


def test_best_fit_hole_removed_on_exact_fit():
    """Hole removed when segment fits exactly."""
    holes_table, allocated_table = make_tables([(0, 100)])
    process = make_process("P1", [("Code", 100)])

    best_fit(process, holes_table, allocated_table)

    assert len(holes_table.holes) == 0


# ─────────────────────────────────────────
#  Failure Cases
# ─────────────────────────────────────────

def test_best_fit_no_hole_fits():
    """Process not allocated when no hole is big enough."""
    holes_table, allocated_table = make_tables([(0, 50)])
    process = make_process("P1", [("Code", 100)])

    best_fit(process, holes_table, allocated_table)

    assert process.is_fully_allocated == False


def test_best_fit_partial_failure_undoes_allocation():
    """If one segment fails, already allocated segments are undone."""
    holes_table, allocated_table = make_tables([(0, 150)])
    process = make_process("P1", [("Code", 100), ("Data", 200)])

    best_fit(process, holes_table, allocated_table)

    assert process.is_fully_allocated == False
    assert len(allocated_table.segments) == 0
    assert process.segments[0].base is None


def test_best_fit_no_holes():
    """Process not allocated when there are no holes."""
    holes_table, allocated_table = make_tables([])
    process = make_process("P1", [("Code", 100)])

    best_fit(process, holes_table, allocated_table)

    assert process.is_fully_allocated == False