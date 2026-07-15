import pulp

class LPSolver:
    def __init__(self, employees, branches):
        self.employees = employees
        self.branches = branches
        self.model = None
        self.result = None
    
    def solve(self):
        print("🔄 Solving LP problem...")
        
        # ایجاد مدل
        self.model = pulp.LpProblem("Employee_Assignment", pulp.LpMinimize)
        
        # متغیرها
        x = {}
        for emp in self.employees:
            for br in self.branches:
                x[(emp.id, br.id)] = pulp.LpVariable(f"x_{emp.id}_{br.id}", cat='Binary')
        
        # تابع هدف
        self.model += pulp.lpSum([
            x[(emp.id, br.id)] * emp.hourly_cost * 8 * 22
            for emp in self.employees
            for br in self.branches
        ])
        
        # قید ۱: هر کارمند حداکثر به یک شعبه
        for emp in self.employees:
            self.model += pulp.lpSum([x[(emp.id, br.id)] for br in self.branches]) <= 1
        
        # قید ۲: حداقل و حداکثر کارمند در هر شعبه
        for br in self.branches:
            self.model += pulp.lpSum([x[(emp.id, br.id)] for emp in self.employees]) >= br.min_employees
            self.model += pulp.lpSum([x[(emp.id, br.id)] for emp in self.employees]) <= br.max_employees
        
        # قید ۳: محدودیت مهارت
        for emp in self.employees:
            for br in self.branches:
                if emp.skill_level < br.required_skill_min:
                    self.model += x[(emp.id, br.id)] == 0
        
        # قید ۴: محدودیت بودجه
        for br in self.branches:
            self.model += pulp.lpSum([
                x[(emp.id, br.id)] * emp.hourly_cost * 8 * 22
                for emp in self.employees
            ]) <= br.budget
        
        # حل کردن
        self.model.solve(pulp.PULP_CBC_CMD(msg=False))
        
        # استخراج نتیجه
        if self.model.status == pulp.LpStatusOptimal:
            assignment = {}
            for emp in self.employees:
                for br in self.branches:
                    if x[(emp.id, br.id)].varValue > 0.5:
                        assignment[emp.id] = br.id
            
            self.result = {
                'status': 'Optimal',
                'objective_value': pulp.value(self.model.objective),
                'assignment': assignment
            }
            print("✅ Optimal solution found!")
        else:
            self.result = {
                'status': pulp.LpStatus[self.model.status],
                'objective_value': None,
                'assignment': {}
            }
            print(f"❌ Status: {self.result['status']}")
        
        return self.result
    
    def print_results(self):
        if not self.result:
            print("❌ Run solve() first")
            return
        
        print("\n" + "="*50)
        print("📊 Results")
        print("="*50)
        print(f"Status: {self.result['status']}")
        if self.result['objective_value']:
            print(f"Total Cost: {self.result['objective_value']:,.0f} تومان")
            print("\nAssignments:")
            for emp_id, br_id in self.result['assignment'].items():
                emp = next(e for e in self.employees if e.id == emp_id)
                br = next(b for b in self.branches if b.id == br_id)
                print(f"  {emp.name} → {br.name}")
        print("="*50)