from dateutil.relativedelta import relativedelta
from datetime import date


class Period:
    
    def __init__(self, period: int, ref_date: date, freq: relativedelta) -> None:
        self._period = None
        self.period = period
        self.freq = freq
        self.ref_date = ref_date
    
    @property
    def period(self):
        return self._period
    
    @period.setter
    def period(self, value):
        try:
            self._period = int(value)
        except:
            raise TypeError(f'Period value must be an integer, received {value} of type {type(value)}')
    
    # Methods
    @property
    def start(self) -> date:
        return self.ref_date + self.freq * (self.period - 1)
    
    @property
    def end(self) -> date:
        return self.ref_date + self.freq * self.period

    # Built-in methods
    def __eq__(self, __o) -> bool:
        if isinstance(__o, int):
            return self.period == __o
        if isinstance(__o, Period):
            return hash(__o) == hash(self)  # should periods with the same start and end dates eval to True or should freq/ref_date also be the same?
        raise NotImplemented
    
    def __ne__(self, __o: object) -> bool:
        if isinstance(__o, int):
            return self.period != __o
        if isinstance(__o, Period):
            return not self.__eq__(__o)
        raise NotImplemented
    
    def __lt__(self, __o: object) -> bool:
        if isinstance(__o, int):
            return self.period < __o
        raise NotImplemented
    
    def __le__(self, __o: object) -> bool:
        if isinstance(__o, int):
            return self.period <= __o
        raise NotImplemented
    
    def __gt__(self, __o: object) -> bool:
        if isinstance(__o, int):
            return self.period > __o
        raise NotImplemented
    
    def __ge__(self, __o: object) -> bool:
        if isinstance(__o, int):
            return self.period >= __o
        raise NotImplemented
    
    def __add__(self, other):
        if isinstance(other, int):
            return type(self)(self.period + other, self.ref_date, self.freq)
        raise NotImplemented
    
    def __radd__(self, other):
        return self.__add__(other)
    
    def __sub__(self, other):
        if isinstance(other, int):
            return type(self)(self.period - other, self.ref_date, self.freq)
        raise NotImplemented
    
    def __contains__(self, item: object) -> bool:
        if isinstance(item, date):
            return self.start <= item <= self.end
        raise TypeError(f'Item must be a date object, received {item}')
        
    def __repr__(self) -> str:
        res = f'Period(num={self.period}, freq={self.freq}'
        if self.ref_date is not None:
            res += f', from={self.start}, to={self.end}'
        res += ')'
        return res
    
    def __hash__(self) -> int:
        return hash((self.period, self.freq, self.ref_date)) 
    
    
    # Convenience constructors
    @classmethod
    def monthly(cls, period: int, ref_date: date):
        return cls(period, relativedelta(months=1), ref_date)
    
    @classmethod
    def quarterly(cls, period: int, ref_date: date):
        return cls(period, relativedelta(months=3), ref_date)

    @classmethod
    def semiannually(cls, period: int, ref_date: date):
        return cls(period, relativedelta(months=6), ref_date)
    
    @classmethod
    def yearly(cls, period: int, ref_date: date):
        return cls(period, relativedelta(years=1), ref_date)
    
    @classmethod
    def from_date(cls, dt: date, freq: relativedelta, ref_date: date, closed_right: bool = True):
        """Create Period instance that contains the specified date. If `closed_right` is `True` periods include the first date and exclude the last date."""
        if (dt == ref_date):
            return 0 if closed_right else 1
        if (dt + freq) == dt:
            raise ValueError('Adding the frequency to the start date must not equal the start date')
        
        period = 0
        shift = relativedelta(days=0) if closed_right else relativedelta(days=1)
        period_start = ref_date + shift
        period_end = period_start + freq
        increment = 1 if (dt > ref_date) and ((ref_date + freq) > ref_date) else -1
        in_period = period_start <= dt < period_end
        
        while not in_period:
            # Increment period range
            period_start = period_start + freq
            period_end = period_end + freq
            period += increment
            in_period = period_start <= dt < period_end
            
        return cls(period, freq, ref_date)
    
    @classmethod
    def range(cls, freq: relativedelta, ref_date: date, start: int, end: int, step: int=1):
        return PeriodIterator(freq, ref_date, start, end, step)


class PeriodIterator:
    
    def __init__(self, freq: relativedelta, ref_date: date, start: int, end: int, step: int=1) -> None:
        self.freq = freq
        self.ref_date = ref_date
        self.range = range(start, end, step)
    
    def __next__(self):
        return Period(next(self.range), self.freq, self.ref_date)