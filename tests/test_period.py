from datetime import date
from dateutil.relativedelta import relativedelta
from respread.period import Period


def test_from_date_middle():
    p = Period.from_date(date(2020, 1, 15), ref_date=date(2020, 1, 1), 
                         freq=relativedelta(months=1), closed_right=True)
    assert p.index == 1
    assert p.start == date(2020, 1, 1)
    assert p.end == date(2020, 2, 1)
    assert p.ref_date == date(2020, 1, 1)

def test_from_date_start_date():
    p = Period.from_date(date(2020, 1, 1), ref_date=date(2020, 1, 1), 
                         freq=relativedelta(months=1), closed_right=True)
    assert p.index == 0
    assert p.start == date(2019, 12, 1)
    assert p.end == date(2020, 1, 1)
    assert p.ref_date == date(2020, 1, 1)

def test_from_date_end_date():
    p = Period.from_date(date(2020, 2, 1), ref_date=date(2020, 1, 1), 
                         freq=relativedelta(months=1), closed_right=True)
    assert p.index == 1
    assert p.start == date(2020, 1, 1)
    assert p.end == date(2020, 2, 1)
    assert p.ref_date == date(2020, 1, 1)

def test_from_date_start_date_closed_left():
    p = Period.from_date(date(2020, 1, 1), ref_date=date(2020, 1, 1), 
                         freq=relativedelta(months=1), closed_right=False)
    assert p.index == 1
    assert p.start == date(2020, 1, 1)
    assert p.end == date(2020, 2, 1)
    assert p.ref_date == date(2020, 1, 1)

def test_from_date_end_date_closed_left():
    p = Period.from_date(date(2020, 2, 1), ref_date=date(2020, 1, 1), 
                         freq=relativedelta(months=1), closed_right=False)
    assert p.index == 2
    assert p.start == date(2020, 2, 1)
    assert p.end == date(2020, 3, 1)
    assert p.ref_date == date(2020, 1, 1)

def test_from_date_none_converging():
    pass
