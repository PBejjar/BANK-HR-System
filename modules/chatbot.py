import pandas as pd
import sqlite3
from typing import Dict, Any

class AnalyticalHRBot:
    """
    چت‌بات هوشمند تحلیلی با اتصال مستقیم به دیتابیس SQLite
    """
    def __init__(self, db_path: str = "data/bank_system.db"):
        self.db_path = db_path
        self.cached_data = None

    def _get_data(self):
        """دریافت داده‌ها با کش‌سازی"""
        if self.cached_data is not None:
            return self.cached_data
        
        try:
            conn = sqlite3.connect(self.db_path)
            df_emp = pd.read_sql_query("SELECT * FROM employees", conn)
            df_br = pd.read_sql_query("SELECT * FROM branches", conn)
            conn.close()
            self.cached_data = (df_emp, df_br)
            return self.cached_data
        except:
            return pd.DataFrame(), pd.DataFrame()

    def generate_analysis_response(self, query: str, lp_results: Dict[str, Any] = None, ga_results: Dict[str, Any] = None, **kwargs) -> str:
        """
        تولید پاسخ هوشمند - هر سوالی رو تحلیل میکنه
        """
        q = query.lower()
        df_emp, df_br = self._get_data()
        
        # ========== ۱. تحلیل تیم پروژه (GA) ==========
        if "تیم" in q or "پروژه" in q or "ga" in q or "ژنتیک" in q:
            if ga_results:
                skills = ga_results.get('skills_covered', [])
                fitness = ga_results.get('fitness', 0)
                team = ga_results.get('team', [])
                
                team_names = "\n".join([f"  - {emp.name} (مهارت: {emp.skill_level}, تجربه: {emp.experience_years} سال)" for emp in team[:5]])
                
                return (
                    f"🧬 **تحلیل تیم چابک پروژه تحول دیجیتال:**\n\n"
                    f"✅ **امتیاز هم‌افزایی:** {fitness:.2f}\n"
                    f"👥 **تعداد اعضای تیم:** {len(team)} نفر\n"
                    f"📚 **تعداد مهارت‌های پوشش‌داده‌شده:** {len(skills)} مورد\n\n"
                    f"**📋 مهارت‌های کلیدی:**\n"
                    f"  {', '.join(skills[:5]) if skills else 'نامشخص'}\n\n"
                    f"**👤 اعضای تیم:**\n{team_names}\n\n"
                    f"💡 **نتیجه‌گیری:** این تیم بالاترین هم‌افزایی را برای پروژه دارد."
                )
            else:
                return "⚠️ **تیم پروژه‌ای پیدا نشد.**\nلطفاً ابتدا در تب **🧬 تیم‌سازی چابک (GA)** دکمه **'اجرای الگوریتم ژنتیک'** را بزنید تا تیم بهینه ساخته شود."
        
        # ========== ۲. تحلیل تخصیص بهینه (LP) ==========
        elif "تخصیص" in q or "بهینه" in q or "lp" in q:
            if lp_results:
                if lp_results.get('status') == 'Optimal':
                    summary = lp_results.get('summary', {})
                    total_staff = sum(info.get('Total_Staff', 0) for info in summary.values())
                    objective = lp_results.get('objective_value', 0)
                    
                    result = f"📊 **تحلیل تخصیص بهینه پرسنل:**\n\n"
                    result += f"✅ **وضعیت:** بهینه\n"
                    result += f"👥 **کل پرسنل تخصیص‌یافته:** {total_staff} نفر\n"
                    result += f"💰 **هزینه کل:** {objective:,.0f} تومان\n\n"
                    result += f"**🏢 جزئیات شعب:**\n"
                    
                    for branch, info in summary.items():
                        result += f"  • {branch}: {info.get('Total_Staff', 0)} نفر (بودجه مصرفی: {info.get('Budget_Spent', 0):,})\n"
                    
                    return result
                else:
                    return "⚠️ **نتایج بهینه‌سازی در دسترس نیست.**\nلطفاً ابتدا در تب **📊 تخصیص بهینه (LP)** دکمه **'اجرای بهینه‌سازی LP'** را بزنید."
            else:
                return "⚠️ **نتایج بهینه‌سازی پیدا نشد.**\nلطفاً ابتدا در تب **📊 تخصیص بهینه (LP)** دکمه **'اجرای بهینه‌سازی LP'** را بزنید."
        
        # ========== ۳. تعداد کارمندان ==========
        elif "تعداد" in q and ("کارمند" in q or "پرسنل" in q or "نفر" in q):
            total = len(df_emp)
            role_counts = df_emp['role'].value_counts()
            roles_text = "\n".join([f"  • {role}: {count} نفر" for role, count in role_counts.items()])
            return f"👥 **تعداد کل کارمندان:** {total} نفر\n\n📊 **ترکیب نیروی انسانی:**\n{roles_text}"
        
        # ========== ۴. شلوغ‌ترین شعبه ==========
        elif "شلوغ" in q or "تراکنش" in q:
            if not df_br.empty:
                max_row = df_br.loc[df_br['daily_transactions'].idxmax()]
                return (
                    f"🏢 **شلوغ‌ترین شعبه:** {max_row['branch_name']}\n"
                    f"📊 **تراکنش روزانه:** {max_row['daily_transactions']:,}\n"
                    f"⏳ **نرخ ورود مشتری:** {max_row['lambda_arrival']} نفر در ساعت\n"
                    f"🕒 **نرخ سرویس‌دهی:** {max_row['mu_service']} نفر در ساعت"
                )
            return "⚠️ اطلاعات شعب در دیتابیس موجود نیست."
        
        # ========== ۵. میانگین حقوق ==========
        elif "حقوق" in q or "دستمزد" in q:
            if not df_emp.empty:
                avg_sal = int(df_emp['salary'].mean())
                max_sal = int(df_emp['salary'].max())
                min_sal = int(df_emp['salary'].min())
                total_sal = int(df_emp['salary'].sum())
                
                if "میانگین" in q:
                    return f"💰 **میانگین حقوق:** {avg_sal:,} واحد"
                elif "بیشترین" in q or "بالاترین" in q:
                    return f"💰 **بیشترین حقوق:** {max_sal:,} واحد"
                elif "کمترین" in q:
                    return f"💰 **کمترین حقوق:** {min_sal:,} واحد"
                else:
                    return (
                        f"💰 **گزارش جامع حقوق:**\n"
                        f"  • مجموع حقوق: {total_sal:,} واحد\n"
                        f"  • میانگین حقوق: {avg_sal:,} واحد\n"
                        f"  • بیشترین حقوق: {max_sal:,} واحد\n"
                        f"  • کمترین حقوق: {min_sal:,} واحد"
                    )
            return "⚠️ اطلاعات پرسنل در دیتابیس موجود نیست."
        
        # ========== ۶. پیشنهادات مدیریتی ==========
        elif "پیشنهاد" in q or "توصیه" in q or "بهبود" in q or "بهره وری" in q or "چگونه" in q or "چطور" in q:
            recs = []
            
            if not df_br.empty:
                max_row = df_br.loc[df_br['daily_transactions'].idxmax()]
                avg_tx = df_br['daily_transactions'].mean()
                if max_row['daily_transactions'] > avg_tx * 1.5:
                    recs.append(f"📌 **شعبه {max_row['branch_name']}** بیش از حد شلوغ است. افزایش پرسنل یا تجهیزات پیشنهاد می‌شود.")
            
            if not df_emp.empty:
                avg_sal = df_emp['salary'].mean()
                high_sal = df_emp[df_emp['salary'] > avg_sal * 1.3]
                if len(high_sal) > 0:
                    recs.append(f"📌 {len(high_sal)} نفر حقوق بالاتر از میانگین دارند. بررسی عملکرد آن‌ها توصیه می‌شود.")
            
            if not df_br.empty:
                avg_lambda = df_br['lambda_arrival'].mean()
                avg_mu = df_br['mu_service'].mean()
                if avg_lambda / avg_mu > 0.8:
                    recs.append(f"📌 سیستم نزدیک به اشباع است. افزایش تعداد باجه‌ها یا کارمندان توصیه می‌شود.")
            
            if ga_results:
                fitness = ga_results.get('fitness', 0)
                if fitness < 50:
                    recs.append(f"📌 تیم پروژه امتیاز {fitness:.2f} دارد. بهبود ترکیب مهارت‌ها پیشنهاد می‌شود.")
            
            if lp_results and lp_results.get('status') == 'Optimal':
                objective = lp_results.get('objective_value', 0)
                recs.append(f"📌 هزینه کل تخصیص: {objective:,.0f} تومان. کاهش هزینه با تخصیص بهینه‌تر امکان‌پذیر است.")
            
            if not recs:
                recs.append("✅ سیستم در وضعیت متعادل قرار دارد. برنامه‌های بهبود فعلی را ادامه دهید.")
            
            return "💡 **پیشنهادات مدیریتی برای افزایش بهره‌وری:**\n" + "\n".join([f"  {r}" for r in recs])
        
        # ========== ۷. پاسخ پیش‌فرض ==========
        else:
            total_emp = len(df_emp)
            total_br = len(df_br)
            
            return (
                f"🤖 **دستیار هوشمند مدیریت بانک:**\n\n"
                f"📊 **خلاصه وضعیت فعلی:**\n"
                f"  • 👥 تعداد کارمندان: {total_emp} نفر\n"
                f"  • 🏢 تعداد شعب: {total_br} شعبه\n"
                f"  • 💰 میانگین حقوق: {int(df_emp['salary'].mean()) if not df_emp.empty else 0:,} واحد\n"
                f"  • 📊 کل تراکنش‌ها: {df_br['daily_transactions'].sum() if not df_br.empty else 0:,}\n\n"
                f"💡 **سوالات قابل پاسخ:**\n"
                f"  • تیم پروژه رو تحلیل کن\n"
                f"  • تخصیص بهینه رو بررسی کن\n"
                f"  • تعداد کارمندان؟\n"
                f"  • شلوغ‌ترین شعبه؟\n"
                f"  • میانگین حقوق؟\n"
                f"  • پیشنهادات مدیریتی بده"
            )