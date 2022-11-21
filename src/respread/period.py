from functools import partial
from dateutil.relativedelta import relativedelta
from datetime import date


class Period:
    """Date periods based on a reference date.
    
    Represents a date period based on a number of date offsets from a reference date.
    The period start and end dates are calculated by adding (period_num * (freq - 1))
    and (period_num * freq) to the reference start date.
    `Period`s are comparable to numbers and dates.
    
    Attributes:
        period: The period number
        freq: Period frequency, or delta between periods
        ref_date: The reference start date
    """
    
    def __init__(self, index: int, ref_date: date, freq: relativedelta) -> None:
        self._index = None
        self.index = index
        self.freq = freq
        self.ref_date = ref_date
    
    @property
    def index(self):
        """Period number"""
        return self._index
    
    @index.setter
    def index(self, value):
        try:
            self._index = int(value)
        except:
            raise TypeError(f'Index value must be an integer, received {value} of type {type(value)}')
    
    @property
    def start(self) -> date:
        """Period start date"""
        return self.ref_date + self.freq * (self.index - 1)
    
    @property
    def end(self) -> date:
        """Period end date"""
        return self.ref_date + self.freq * self.index

    # Built-in methods
    def __eq__(self, __o) -> bool:
        if isinstance(__o, int):
            return self.index == __o
        if isinstance(__o, Period):
            return hash(__o) == hash(self)  # should periods with the same start and end dates eval to True or should freq/ref_date also be the same?
        raise NotImplemented
    
    def __ne__(self, __o: object) -> bool:
        if isinstance(__o, int):
            return self.index != __o
        if isinstance(__o, Period):
            return not self.__eq__(__o)
        raise NotImplemented
    
    def __lt__(self, __o: object) -> bool:
        if isinstance(__o, int):
            return self.index < __o
        raise NotImplemented
    
    def __le__(self, __o: object) -> bool:
        if isinstance(__o, int):
            return self.index <= __o
        raise NotImplemented
    
    def __gt__(self, __o: object) -> bool:
        if isinstance(__o, int):
            return self.index > __o
        raise NotImplemented
    
    def __ge__(self, __o: object) -> bool:
        if isinstance(__o, int):
            return self.index >= __o
        raise NotImplemented
    
    def __add__(self, other):
        if isinstance(other, int):
            return type(self)(self.index + other, self.ref_date, self.freq)
        raise NotImplemented
    
    def __radd__(self, other):
        return self.__add__(other)
    
    def __sub__(self, other):
        if isinstance(other, int):
            return type(self)(self.index - other, self.ref_date, self.freq)
        raise NotImplemented
    
    def __contains__(self, item: object) -> bool:
        if isinstance(item, date):
            return self.start <= item <= self.end
        raise TypeError(f'Item must be a date object, received {item}')
        
    def __repr__(self) -> str:
        res = f'Period(index={self.index}, freq={self.freq}'
        if self.ref_date is not None:
            res += f', from={self.start}, to={self.end}'
        res += ')'
        return res
    
    def __hash__(self) -> int:
        return hash((self.index, self.freq, self.ref_date)) 
    
    
    # Convenience constructors
    @classmethod
    def monthly(cls, index: int, ref_date: date):
        """Period with monthly date offset."""
        return cls(index, relativedelta(months=1), ref_date)
    
    @classmethod
    def quarterly(cls, index: int, ref_date: date):
        """Period with quarterly date offset."""
        return cls(index, relativedelta(months=3), ref_date)

    @classmethod
    def semiannually(cls, index: int, ref_date: date):
        """Period with 6 month date offset."""
        return cls(index, relativedelta(months=6), ref_date)
    
    @classmethod
    def yearly(cls, index: int, ref_date: date):
        """Period with one year date offset."""
        return cls(index, relativedelta(years=1), ref_date)
    
    @classmethod
    def from_date(cls, dt: date, ref_date: date, freq: relativedelta, closed_right: bool = True):
        """Create Period instance that contains the specified date based on the given reference start date and offset.
        If `closed_right` is `True` periods include the first date and exclude the last date."""
        step = 1 if (dt - (ref_date + freq)) < (dt - ref_date) else -1
        period_iterator = PeriodIterator(ref_date, freq, 0, step=step)
        
        for period in period_iterator:
            if closed_right:
                if period.start < dt <= period.end:
                    return period
            else:
                if period.start <= dt < period.end:
                    return period
    
    @classmethod
    def range(cls, ref_date: date, freq: relativedelta, start: int, end: int, step: int=1):
        """Return iterator of Periods from index number `start` to `end`."""
        return PeriodIterator(freq, ref_date, start, end, step)


class PeriodIterator:
    """Iterate over Periods."""
    def __init__(self, ref_date: date, freq: relativedelta, start: int=0, end: int=None, step: int=1) -> None:
        self.period_factory = partial(Period, ref_date=ref_date, freq=freq)
        self.end = end
        self.current_index = start
        self.step = step
    
    def __next__(self):
        current_period = self.period_factory(self.current_index)
        if (self.end is None) or (current_period.end  <= self.end):
            self.current_index += self.step
            return current_period
        else:
            raise StopIteration
    
    def __iter__(self):
        return self