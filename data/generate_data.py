import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import random
from pathlib import Path
from src.models import Employee, Branch

# تنظیم seed برای تکرارپذیری
random.seed(42)

def generate_employees(count=30):
    """تولید کارمندان نمونه"""
    
    names = ['علی رضایی', 'مریم احمدی', 'رضا کریمی', 'سارا حسینی', 'محمد محمدی',
             'زهرا علی‌پور', 'حسین نظری', 'الناز شیری', 'امیر طاهری', 'نگین مرادی',
             'کیان رستمی', 'دینا محمدی', 'آرمان صادقی', 'هستی رحیمی', 'بهمن احمدی',
             'نازنین عباسی', 'پوریا کاظمی', 'سیمین نوروزی', 'ارشیا حیدری', 'مینا قاسمی']
    
    skills_pool = ['python', 'sql', 'management', 'communication', 'analytics', 
                   'finance', 'marketing', 'hr', 'sales', 'leadership']
    
    employees = []
    
    for i in range(count):
        name = names[i % len(names)]
        if i >= len(names):
            name = f"{name} {i+1}"
        
        emp = Employee(
            id=i + 1,
            name=name,
            skill_level=random.randint(2, 5),
            hourly_cost=round(random.uniform(80000, 250000), 0),
            skills=random.sample(skills_pool, random.randint(2, 4)),
            experience_years=round(random.uniform(1, 12), 1),
            is_available=random.random() > 0.15
        )
        employees.append(emp)
    
    return employees

def generate_branches(count=5):
    """تولید شعب نمونه"""
    
    branches_data = [
        {"name": "شعبه مرکزی", "location": "تهران", "min": 2, "max": 8},
        {"name": "شعبه شرق", "location": "مشهد", "min": 2, "max": 6},
        {"name": "شعبه غرب", "location": "اصفهان", "min": 2, "max": 5},
        {"name": "شعبه شمال", "location": "رشت", "min": 2, "max": 5},
        {"name": "شعبه جنوب", "location": "شیراز", "min": 2, "max": 6},
    ]
    
    branches = []
    
    for i, data in enumerate(branches_data[:count]):
        br = Branch(
            id=i + 1,
            name=data["name"],
            location=data["location"],
            transaction_volume=random.randint(150, 1200),
            required_skill_min=random.randint(1, 3),
            min_employees=data["min"],
            max_employees=data["max"],
            budget=round(random.uniform(30000000, 60000000), 0)
        )
        branches.append(br)
    
    return branches

def save_data():
    """ذخیره داده‌ها در فایل‌های JSON"""
    
    print("🔄 در حال تولید داده‌های نمونه...")
    
    employees = generate_employees(30)
    branches = generate_branches(5)
    
    print(f"✅ {len(employees)} کارمند تولید شد")
    print(f"✅ {len(branches)} شعبه تولید شد")
    
    data_dir = Path(__file__).parent
    
    with open(data_dir / 'employees.json', 'w', encoding='utf-8') as f:
        json.dump([e.__dict__ for e in employees], f, ensure_ascii=False, indent=2)
    print("✅ employees.json ذخیره شد")
    
    with open(data_dir / 'branches.json', 'w', encoding='utf-8') as f:
        json.dump([b.__dict__ for b in branches], f, ensure_ascii=False, indent=2)
    print("✅ branches.json ذخیره شد")
    
    print("\n📊 خلاصه داده‌ها:")
    print(f"   میانگین سطح مهارت: {sum(e.skill_level for e in employees) / len(employees):.1f}")
    print(f"   میانگین هزینه ساعتی: {sum(e.hourly_cost for e in employees) / len(employees):,.0f} تومان")
    print(f"   میانگین بودجه شعب: {sum(b.budget for b in branches) / len(branches):,.0f} تومان")
    
    return employees, branches

if __name__ == "__main__":
    save_data()
    print("\n✅ تولید داده با موفقیت انجام شد!")