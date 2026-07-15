from dataclasses import dataclass

@dataclass
class Branch:
    """مدل شعبه بانک"""
    id: int
    name: str
    location: str
    transaction_volume: int  # تعداد تراکنش‌های روزانه
    required_skill_min: int  # حداقل سطح مهارت مورد نیاز (1 تا 5)
    min_employees: int  # حداقل کارمند مورد نیاز
    max_employees: int  # حداکثر کارمند مجاز
    budget: float  # بودجه ماهانه به تومان
    
    def __post_init__(self):
        """اعتبارسنجی داده‌ها بعد از ایجاد"""
        if not 1 <= self.required_skill_min <= 5:
            raise ValueError("حداقل مهارت باید بین 1 تا 5 باشد")
        if self.min_employees > self.max_employees:
            raise ValueError("حداقل کارمند نباید از حداکثر بیشتر باشد")
        if self.budget <= 0:
            raise ValueError("بودجه باید مثبت باشد")