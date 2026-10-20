from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from app.services.slots import Block, classify_start, generate_slots

TZ = ZoneInfo("Africa/Nairobi")
DAY = date(2026, 10, 20)


def local(h, m=0, s=0):
    return datetime(2026, 10, 20, h, m, s, tzinfo=TZ)


def test_splits_block_into_30_minute_slots():
    slots = generate_slots([Block(time(9), time(11))], DAY, TZ, 30)
    assert slots == [local(9), local(9, 30), local(10), local(10, 30)]


def test_lunch_break_is_not_offered():
    slots = generate_slots([Block(time(8), time(12)), Block(time(13), time(17))], DAY, TZ, 30)
    assert local(12) not in slots
    assert local(12, 30) not in slots
    assert local(11, 30) in slots and local(13) in slots
    assert len(slots) == 16


def test_leftover_shorter_than_a_slot_is_dropped():
    slots = generate_slots([Block(time(9), time(10, 15))], DAY, TZ, 30)
    assert slots == [local(9), local(9, 30)]


def test_no_blocks_means_no_slots():
    assert generate_slots([], DAY, TZ, 30) == []


def test_slots_follow_block_start_not_the_clock_hour():
    slots = generate_slots([Block(time(9, 15), time(10, 15))], DAY, TZ, 30)
    assert slots == [local(9, 15), local(9, 45)]


def test_overlapping_blocks_do_not_duplicate_slots():
    slots = generate_slots([Block(time(9), time(10)), Block(time(9), time(10))], DAY, TZ, 30)
    assert slots == [local(9), local(9, 30)]


BLOCKS = [Block(time(8), time(12)), Block(time(13), time(17))]


def test_classify_valid_slot():
    assert classify_start(local(9, 30), BLOCKS, 30) == "ok"


def test_classify_last_slot_of_block_is_valid():
    assert classify_start(local(11, 30), BLOCKS, 30) == "ok"


def test_classify_off_boundary_inside_hours_is_misaligned():
    assert classify_start(local(9, 10), BLOCKS, 30) == "misaligned"


def test_classify_seconds_are_misaligned():
    assert classify_start(local(9, 0, 5), BLOCKS, 30) == "misaligned"


def test_classify_lunch_and_after_hours_are_outside():
    assert classify_start(local(12), BLOCKS, 30) == "outside"
    assert classify_start(local(17), BLOCKS, 30) == "outside"
    assert classify_start(local(7, 30), BLOCKS, 30) == "outside"


def test_classify_slot_that_would_run_past_block_end():
    assert classify_start(local(9, 45), [Block(time(9, 15), time(10, 0))], 30) == "misaligned"
