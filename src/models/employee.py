from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Employee:
    """مدل کارمند"""
    id: int
    name: str
    skill_level: int  # 1 تا 5
    hourly_cost: float  # هزینه ساعتی به تومان
    skills: List[str]  # لیست مهارت‌ها مثل ['python', 'sql', 'management']
    experience_years: float  # سال‌های تجربه
    is_available: bool = True  # در دسترس هست یا نه
    preferred_branch: Optional[str] = None  # شعبه ترجیحی (اختیاری)
    
    def __post_init__(self):
        """اعتبارسنجی داده‌ها بعد از ایجاد"""
        if not 1 <= self.skill_level <= 5:
            raise ValueError("سطح مهارت باید بین 1 تا 5 باشد")
        if self.hourly_cost <= 0:
            raise ValueError("هزینه ساعتی باید مثبت باشد")