from abc import ABC, abstractmethod
from typing import List

from models.vacancy import Vacancy


class JobParserStrategy(ABC):
    """
    Абстрактный класс стратегии (интерфейс).
    Все парсеры (HH.RU, SuperJob, Rabota.ru, и т.д.)
    должны реализовывать этот контракт.
    """

    @abstractmethod
    def parse(self, query: str, max_pages: int = 2) -> List[Vacancy]:
        pass
