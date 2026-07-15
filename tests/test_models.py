from src.models import Employee, Branch

# تست کارمند
emp = Employee(
    id=1,
    name="علی رضایی",
    skill_level=4,
    hourly_cost=120000,
    skills=['python', 'sql', 'analytics'],
    experience_years=5.5
)
print(f"✅ کارمند: {emp.name} - سطح مهارت: {emp.skill_level}")

# تست شعبه
br = Branch(
    id=1,
    name="شعبه مرکزی",
    location="تهران",
    transaction_volume=850,
    required_skill_min=3,
    min_employees=5,
    max_employees=12,
    budget=25000000
)
print(f"✅ شعبه: {br.name} - بودجه: {br.budget:,} تومان")