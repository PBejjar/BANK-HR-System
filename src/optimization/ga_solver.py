import random

class GeneticAlgorithm:
    def __init__(self, employees, team_size=3, population_size=20, generations=30, mutation_rate=0.1):
        self.employees = employees
        self.team_size = team_size
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.population = []
        self.best_solution = None
        self.best_fitness = -float('inf')
        self.fitness_history = []
    
    def create_chromosome(self):
        """ساخت یک کروموزوم (یک تیم)"""
        return random.sample(range(len(self.employees)), self.team_size)
    
    def initialize_population(self):
        """ساخت جمعیت اولیه"""
        self.population = [self.create_chromosome() for _ in range(self.population_size)]
    
    def calculate_fitness(self, chromosome):
        """محاسبه برازندگی یک کروموزوم"""
        team = [self.employees[i] for i in chromosome]
        
        # تنوع مهارتی
        skills = set()
        for emp in team:
            skills.update(emp.skills)
        skill_diversity = len(skills)
        
        # میانگین تجربه
        avg_exp = sum(emp.experience_years for emp in team) / len(team)
        
        # تعارضات (مهارت‌های مشترک زیاد)
        conflicts = 0
        for i in range(len(team)):
            for j in range(i+1, len(team)):
                common = set(team[i].skills) & set(team[j].skills)
                if len(common) >= 3:
                    conflicts += 1
        
        return (skill_diversity * 10) + (avg_exp * 2) - (conflicts * 5)
    
    def selection(self):
        """انتخاب والدین با روش تورنمنت"""
        tournament = random.sample(self.population, 3)
        return max(tournament, key=lambda x: self.calculate_fitness(x))
    
    def crossover(self, parent1, parent2):
        """تقاطع"""
        size = self.team_size
        point = random.randint(1, size - 1)
        
        child1 = parent1[:point] + [g for g in parent2 if g not in parent1[:point]]
        child2 = parent2[:point] + [g for g in parent1 if g not in parent2[:point]]
        
        # پر کردن اگر کوتاه بود
        while len(child1) < size:
            new = random.randint(0, len(self.employees)-1)
            if new not in child1:
                child1.append(new)
        while len(child2) < size:
            new = random.randint(0, len(self.employees)-1)
            if new not in child2:
                child2.append(new)
        
        return child1[:size], child2[:size]
    
    def mutate(self, chromosome):
        """جهش"""
        for i in range(len(chromosome)):
            if random.random() < self.mutation_rate:
                new = random.randint(0, len(self.employees)-1)
                while new in chromosome:
                    new = random.randint(0, len(self.employees)-1)
                chromosome[i] = new
        return chromosome
    
    def evolve(self):
        """اجرای الگوریتم"""
        print(f"🧬 Starting GA with {self.population_size} population, {self.generations} generations")
        self.initialize_population()
        
        for gen in range(self.generations):
            # محاسبه برازندگی
            fitness_scores = [self.calculate_fitness(chrom) for chrom in self.population]
            max_fitness = max(fitness_scores)
            best_idx = fitness_scores.index(max_fitness)
            self.fitness_history.append(max_fitness)
            
            # به‌روزرسانی بهترین
            if max_fitness > self.best_fitness:
                self.best_fitness = max_fitness
                self.best_solution = self.population[best_idx].copy()
            
            if gen % 5 == 0:
                print(f"  Generation {gen}: Best Fitness = {max_fitness:.2f}")
            
            # ساخت نسل جدید
            new_population = [self.population[best_idx].copy()]  # الیتیسم
            
            while len(new_population) < self.population_size:
                p1 = self.selection()
                p2 = self.selection()
                c1, c2 = self.crossover(p1, p2)
                new_population.append(self.mutate(c1))
                if len(new_population) < self.population_size:
                    new_population.append(self.mutate(c2))
            
            self.population = new_population
        
        print(f"✅ Best Fitness: {self.best_fitness:.2f}")
        return self.best_solution
    
    def get_best_team(self):
        """دریافت بهترین تیم"""
        if self.best_solution is None:
            return []
        return [self.employees[i] for i in self.best_solution]
    
    def get_fitness_history(self):
        return self.fitness_history