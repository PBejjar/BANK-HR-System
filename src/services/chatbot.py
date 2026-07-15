from hermex import Gemini

class Chatbot:
    def __init__(self):
        self.gemini = None
        print("✅ Chatbot ready with Gemini")
    
    def ask(self, question, context=""):
        """پرسش از Gemini بدون کلید"""
        try:
            # سوال رو با زمینه ترکیب کن
            full_question = f"{question}\n\nزمینه: {context}" if context else question
            
            # سوال رو بفرست به Gemini
            response = Gemini.simple_query(full_question)
            return response.text
            
        except Exception as e:
            return f"❌ خطا: {str(e)}"
    
    def analyze_optimization(self, result, employees, branches):
        """تحلیل نتایج LP"""
        if not result or result.get('status') != 'Optimal':
            return "❌ ابتدا LP رو اجرا کن."
        
        # اطلاعات رو جمع کن
        info = f"""
        نتایج بهینه‌سازی:
        - هزینه کل: {result.get('objective_value', 0):,.0f} تومان
        - تعداد کارمندان: {len(employees)}
        - تعداد شعب: {len(branches)}
        - کارمندان تخصیص یافته: {len(result.get('assignment', {}))}
        """
        
        question = "این نتایج رو تحلیل کن و پیشنهادات مدیریتی بده."
        return self.ask(question, info)
    
    def analyze_ga_team(self, team, fitness_history):
        """تحلیل تیم GA"""
        if not team:
            return "❌ ابتدا GA رو اجرا کن."
        
        # اطلاعات تیم
        team_info = "\n".join([
            f"- {emp.name}: مهارت {emp.skill_level}, تجربه {emp.experience_years} سال"
            for emp in team
        ])
        
        info = f"""
        تیم چابک پیدا شده:
        {team_info}
        
        تاریخچه برازندگی:
        - شروع: {fitness_history[0] if fitness_history else 0:.2f}
        - پایان: {fitness_history[-1] if fitness_history else 0:.2f}
        """
        
        question = "این تیم رو تحلیل کن و نقاط قوت و ضعفش رو بگو."
        return self.ask(question, info)