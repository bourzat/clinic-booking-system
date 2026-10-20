"""Pure slot arithmetic. No database, no clock: easy to test, easy to trust."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Block:
    start: time
    end: time


def generate_slots(blocks: Iterable[Block], day: date, tz: ZoneInfo, slot_minutes: int) -> list[datetime]:
    """Split each working block into fixed-length slots starting at the block's start.

    A leftover piece shorter than one slot at the end of a block is not offered.
    Returns timezone-aware start times in the clinic zone, sorted.
    """
    step = timedelta(minutes=slot_minutes)
    starts: set[datetime] = set()
    for block in blocks:
        cursor = datetime.combine(day, block.start, tzinfo=tz)
        block_end = datetime.combine(day, block.end, tzinfo=tz)
        while cursor + step <= block_end:
            starts.add(cursor)
            cursor += step
    return sorted(starts)


def classify_start(start_local: datetime, blocks: Iterable[Block], slot_minutes: int) -> str:
    """Say whether a local start time is a valid slot for the given blocks.

    Returns "ok", "misaligned" (inside working hours but not on a slot boundary,
    or would run past the end of the block) or "outside" (not in any block).
    """
    step = timedelta(minutes=slot_minutes)
    if start_local.second or start_local.microsecond:
        return "misaligned"
    day = start_local.date()
    inside_any = False
    for block in blocks:
        block_start = datetime.combine(day, block.start, tzinfo=start_local.tzinfo)
        block_end = datetime.combine(day, block.end, tzinfo=start_local.tzinfo)
        if block_start <= start_local < block_end:
            inside_any = True
            offset = start_local - block_start
            if offset % step == timedelta(0) and start_local + step <= block_end:
                return "ok"
    return "misaligned" if inside_any else "outside"
