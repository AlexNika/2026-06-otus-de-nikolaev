from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Salary:
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    currency: str = "RUR"

    @property
    def average(self) -> Optional[float]:
        if self.min_value and self.max_value:
            return (self.min_value + self.max_value) / 2
        return self.min_value or self.max_value


@dataclass
class Vacancy:
    title: str
    key_skills: List[str] = field(default_factory=list)
    description_skills: List[str] = field(default_factory=list)
    description: str = ""
    salary: Optional[Salary] = None
    url: Optional[str] = None
    external_id: Optional[str] = None

    @property
    def all_skills(self) -> List[str]:
        return list(set(self.key_skills + self.description_skills))
