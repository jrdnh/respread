from datetime import date
from dateutil.relativedelta import relativedelta
from typing import List


def is_month_end(dt: date) -> bool:
    return dt.month != (dt + relativedelta(days=1)).month


def thirty360(dt1: date, dt2: date) -> float:
    """Returns the fraction of a year between `dt1` and `dt2` on 30 / 360 day count basis"""

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


def compounded(start: date, end: date, freq: relativedelta, rate_cutoffs: List):
    """
    Annualized rate on a 30/360 basis
    Compounds at each cutoff date and at each interval defined by freq
    rate_cutoffs should be a list of (date, rate) tuples, where date is the righthand cutoff
    """
    rate_cutoffs = sorted(rate_cutoffs, key=lambda p: p[0])
    rate_dts, rates = zip(*rate_cutoffs)
    dts = date_range(start, end, freq)
    cutoff_dts = [dt for dt in rate_dts if dt > start and dt < end and dt not in dts]
    dts = dts + cutoff_dts
    dts.sort()
    
    period_iter = iter(dts)
    curr_period_start = next(period_iter)
    
    fv = 1.0
    for curr_period_end in period_iter:
        rate = [r for d, r in rate_cutoffs if d >= curr_period_end][0]
        fv = fv * (1 + rate * thirty360(curr_period_start, curr_period_end))
        
        curr_period_start = curr_period_end
    
    return (fv - 1) / thirty360(start, end)


def date_range(start: date, end: date, freq: relativedelta):
    """Range of dates from and including the start date and to and including the end date"""
    dt_range = [start]
    curr = start
    
    while curr != end:
        next = min(curr + freq, end)
        if abs(end - curr) <= abs(end - next):
            raise ValueError(f'freq {freq} does not result in converging series from {start} to {end}')
        curr = next
        dt_range.append(curr)
    
    return dt_range
