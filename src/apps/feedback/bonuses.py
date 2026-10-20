from abc import ABC, abstractmethod
from calendar import isleap
from math import isfinite

from .enums import Positions
from .util import DateTimeUtil


class AnnualBonusService(ABC):
    @abstractmethod
    def calculate(self, position, salary, bonus, work_days, year=None):
        raise NotImplementedError


class AnnualBonusServiceImpl(AnnualBonusService):
    def calculate(self, position, salary, bonus, work_days, year=None):
        year = DateTimeUtil.current_year() if year is None else year
        if not isinstance(position, Positions):
            raise ValueError('Неизвестная должность')
        if type(year) is not int or not 1 <= year <= 9999:
            raise ValueError('Год должен быть целым числом от 1 до 9999')
        days_in_year = 366 if isleap(year) else 365
        if type(work_days) is not int or not 1 <= work_days <= days_in_year:
            raise ValueError(f'workDays должен быть целым числом от 1 до {days_in_year}')
        for name, value in (('salary', salary), ('bonus', bonus)):
            try:
                valid = (type(value) in (int, float)
                         and isfinite(value) and value >= 0)
            except OverflowError:
                valid = False
            if not valid:
                raise ValueError(f'{name} должен быть конечным неотрицательным числом')
        try:
            result = salary * bonus * days_in_year * position.coefficient / work_days
        except OverflowError as error:
            raise ValueError('Результат расчёта превышает допустимый диапазон') from error
        if not isfinite(result):
            raise ValueError('Результат расчёта превышает допустимый диапазон')
        return result


class QuarterlyBonusService(ABC):
    @abstractmethod
    def calculate(self, position, salary, bonus, work_days, year=None):
        raise NotImplementedError


class QuarterlyBonusServiceImpl(QuarterlyBonusService):
    def __init__(self, annual_service=None):
        self.annual_service = (annual_service if annual_service is not None
                               else AnnualBonusServiceImpl())

    def calculate(self, position, salary, bonus, work_days, year=None):
        if not isinstance(position, Positions):
            raise ValueError('Неизвестная должность')
        if not position.isManager:
            raise ValueError('Квартальная премия доступна только руководителям')
        return self.annual_service.calculate(
            position, salary, bonus, work_days, year) / 4
