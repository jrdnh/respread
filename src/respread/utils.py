from datetime import date
from functools import partial
from dateutil.relativedelta import relativedelta
from .period import Period, PeriodIterator


def is_month_end(dt: date) -> bool:
    return dt.month != (dt + relativedelta(days=1)).month


def thirty360(dt1: date, dt2: date) -> float:
    """Returns the fraction of a year between `dt1` and `dt2` on 30 / 360 day count basis."""

    y1, m1, d1 = dt1.year, dt1.month, dt1.day
    y2, m2, d2 = dt2.year, dt2.month, dt2.day

    if is_month_end(dt1) and (dt1.month == 2) and is_month_end(dt2) and (dt2.month == 2):
        d2 = 30
    if is_month_end(dt1) and (dt1.month == 2):
        d1 = 30
    if (d2 == 31) and ((d1 == 30) or (d1 == 31)):
        d2 = 30
    if d1 == 31:
        d1 = 30

    days = 360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)

    return days / 360

def actual360(dt1: date, dt2: date):
    """Returns the fraction of a year between `dt1` and `dt2` on actual / 360 day count basis."""
    return (dt2 - dt1).days / 360


def compounded(rate: float, from_dt: date, to_dt: date, comp_ref_dt: date, comp_freq: relativedelta, day_count: callable) -> float:
    """
    Compounded growth between dates.
    
    Arguments:
        float: Growth rate
        from_dt: First day of period
        to_dt: Last day of period
        comp_ref_dt: Reference date to calculate compounding dates
        comp_freq: Compounding frequency
        day_count: Function that takes two dates and returns the fraction of a year between them
    """
    initial_index = Period.from_date(from_dt, ref_date=comp_ref_dt, freq=comp_freq).index
    period_generator = PeriodIterator(ref_date=comp_ref_dt, freq=comp_freq, start=initial_index)
    
    compounded_rate = 1
    for period in period_generator:
        yf = day_count(max(from_dt, period.start), min(to_dt, period.end))
        compounded_rate = compounded_rate * (1+ yf * rate)
        if period.end >= to_dt:
            break
    
    return compounded_rate - 1


def date_range(start: date, end: date, freq: relativedelta):
    """Range of dates from and including the start date and to and including the end date."""
    dt_range = [start]
    curr = start
    
    while curr != end:
        next = min(curr + freq, end)
        if abs(end - curr) <= abs(end - next):
            raise ValueError(f'freq {freq} does not result in converging series from {start} to {end}')
        curr = next
        dt_range.append(curr)
    
    return dt_range
