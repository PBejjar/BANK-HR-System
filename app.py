import streamlit as st
import pandas as pd
import sqlite3
import os
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from src.models import Employee, Branch
from src.optimization import LPSolver, GeneticAlgorithm
from modules.chatbot import AnalyticalHRBot

# ========== تنظیمات ==========
st.set_page_config(
    page_title="سیستم یکپارچه تصمیم‌یار بانک",
    page_icon="🏦",
    layout="wide"
)

DB_PATH = "data/bank_system.db"
bot = AnalyticalHRBot(DB_PATH)

# ========== مقداردهی session_state ==========
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None

# =========================================================
# ========== صفحه ورود (Login) ==========
# =========================================================
if not st.session_state.logged_in:
    st.title("🔐 پورتال جامع تصمیم‌یار بانکداری هوشمند")
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        with st.form("secure_login_form"):
            st.markdown("### 🔑 ورود به سامانه")
            username = st.text_input("👤 نام کاربری", placeholder="admin یا staff")
            password = st.text_input("🔒 رمز عبور", type="password", placeholder="****")
            
            role_selection = st.selectbox(
                "📋 سطح دسترسی سازمانی",
                ["رئیس بانک (مدیر ارشد)", "کارمند بانک / ناظر کیفی"]
            )
            
            submit_login = st.form_submit_button("🛡️ تأیید هویت و ورود ایمن", use_container_width=True)
            
            if submit_login:
                if role_selection == "رئیس بانک (مدیر ارشد)" and username == "admin" and password == "1234":
                    st.session_state.logged_in = True
                    st.session_state.user_role = "admin"
                    st.rerun()
                elif role_selection == "کارمند بانک / ناظر کیفی" and username == "staff" and password == "1111":
                    st.session_state.logged_in = True
                    st.session_state.user_role = "employee"
                    st.rerun()
                else:
                    st.error("❌ دسترسی غیرمجاز! مشخصات وارد شده نادرست است.")
    
    with col_right:
        st.markdown("")
    
    st.stop()

# =========================================================
# ========== سایدبار ==========
# =========================================================
st.sidebar.markdown(f"### 👤 سطح کاربری: { 'رئیس کل بانک' if st.session_state.user_role == 'admin' else 'کارمند سیستم' }")

if st.sidebar.button("🚪 خروج از سامانه", key="logout_button"):
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.rerun()

st.sidebar.markdown("---")

# ========== راه‌اندازی دیتابیس SQLite ==========
def init_sqlite_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            employee_id TEXT PRIMARY KEY,
            role TEXT,
            salary INTEGER
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS branches (
            branch_id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch_name TEXT,
            daily_transactions INTEGER,
            budget INTEGER,
            lambda_arrival REAL,
            mu_service REAL
        )
    """)
    
    cursor.execute("SELECT count(*) FROM employees")
    if cursor.fetchone()[0] == 0:
        emp_data = [
            ("EMP-101", "Teller", 12000), ("EMP-102", "Teller", 12500),
            ("EMP-103", "Teller", 11800), ("EMP-104", "Credit_Analyst", 18000),
            ("EMP-105", "Credit_Analyst", 19500), ("EMP-106", "Branch_Manager", 30000),
            ("EMP-107", "Teller", 13000), ("EMP-108", "Credit_Analyst", 17500),
            ("EMP-109", "Branch_Manager", 29000), ("EMP-110", "Teller", 12100)
        ]
        cursor.executemany("INSERT INTO employees VALUES (?, ?, ?)", emp_data)

    cursor.execute("SELECT count(*) FROM branches")
    if cursor.fetchone()[0] == 0:
        branch_data = [
            ("شعبه مرکزی", 1850, 85000, 32.5, 15.0),
            ("شعبه آزادی", 1100, 55000, 18.0, 15.0),
            ("شعبه ونک", 1450, 70000, 25.0, 15.0)
        ]
        cursor.executemany("INSERT INTO branches (branch_name, daily_transactions, budget, lambda_arrival, mu_service) VALUES (?, ?, ?, ?, ?)", branch_data)
        
    conn.commit()
    conn.close()

init_sqlite_db()

# ========== بارگذاری داده‌های JSON ==========
@st.cache_data
def load_json_data():
    with open('data/employees.json', 'r', encoding='utf-8') as f:
        emp_data = json.load(f)
        employees = [Employee(**e) for e in emp_data]
    
    with open('data/branches.json', 'r', encoding='utf-8') as f:
        br_data = json.load(f)
        branches = [Branch(**b) for b in br_data]
    
    return employees, branches

employees, branches = load_json_data()

# ========== تابع برای دریافت داده‌های SQLite ==========
@st.cache_data
def get_sqlite_data():
    conn = sqlite3.connect(DB_PATH)
    df_emp = pd.read_sql_query("SELECT * FROM employees", conn)
    df_br = pd.read_sql_query("SELECT * FROM branches", conn)
    conn.close()
    return df_emp, df_br

# ========== تابع برای تحلیل فعالیت شعب ==========
def get_branch_analysis(df_br):
    if df_br.empty:
        return {}
    
    max_tx = df_br.loc[df_br['daily_transactions'].idxmax()]
    min_tx = df_br.loc[df_br['daily_transactions'].idxmin()]
    avg_tx = df_br['daily_transactions'].mean()
    
    return {
        'busiest': {'name': max_tx['branch_name'], 'transactions': max_tx['daily_transactions']},
        'quietest': {'name': min_tx['branch_name'], 'transactions': min_tx['daily_transactions']},
        'average': avg_tx,
        'total': df_br['daily_transactions'].sum()
    }

# ========== تابع برای تحلیل مهارت‌های تیم ==========
def analyze_team_skills(team):
    all_skills = {}
    for emp in team:
        for skill in emp.skills:
            all_skills[skill] = all_skills.get(skill, 0) + 1
    return dict(sorted(all_skills.items(), key=lambda x: x[1], reverse=True))

# ========== عنوان اصلی ==========
st.title("🏦 سامانه یکپارچه برنامه‌ریزی ریاضی و منابع بانکی")
st.markdown("---")

# =========================================================
# ========== تب‌ها با محدودیت دسترسی ==========
# =========================================================
if st.session_state.user_role == "admin":
    tab_home, tab_lp, tab_ga, tab_chat = st.tabs([
        "🏠 صفحه اصلی",
        "📊 تخصیص بهینه (LP)",
        "🧬 تیم‌سازی چابک (GA)",
        "🤖 چت‌بات هوشمند"
    ])
else:
    tab_home, tab_chat = st.tabs([
        "🏠 صفحه اصلی",
        "🤖 چت‌بات هوشمند"
    ])

# =========================================================
# ========== تب صفحه اصلی (HOME) ==========
# =========================================================
with tab_home:
    st.header("📋 داشبورد مدیریت منابع انسانی")
    
    df_emp_sql, df_br_sql = get_sqlite_data()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="👥 کل کارمندان", value=f"{len(df_emp_sql)} نفر", delta="فعال")
    with col2:
        total_salary = df_emp_sql['salary'].sum()
        st.metric(label="💰 مجموع حقوق ماهانه", value=f"{total_salary:,}", delta="واحد")
    with col3:
        total_transactions = df_br_sql['daily_transactions'].sum()
        st.metric(label="📊 کل تراکنش‌های روزانه", value=f"{total_transactions:,}", delta="تراکنش")
    with col4:
        avg_salary = int(df_emp_sql['salary'].mean())
        st.metric(label="📈 میانگین حقوق", value=f"{avg_salary:,}", delta="واحد")
    
    st.markdown("---")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("👥 لیست کارمندان")
        df_emp_display = df_emp_sql.copy()
        df_emp_display['وضعیت'] = ['🟢 فعال' if i % 3 != 0 else '🟡 در مرخصی' for i in range(len(df_emp_display))]
        df_emp_display['سابقه (سال)'] = [i % 15 + 1 for i in range(len(df_emp_display))]
        
        st.dataframe(
            df_emp_display[['employee_id', 'role', 'salary', 'وضعیت', 'سابقه (سال)']].rename(columns={
                'employee_id': 'کد پرسنلی',
                'role': 'سمت',
                'salary': 'حقوق'
            }),
            use_container_width=True,
            height=300
        )
        
        role_counts = df_emp_sql['role'].value_counts()
        st.caption(f"📌 **تفکیک شغلی:** {', '.join([f'{role}: {count} نفر' for role, count in role_counts.items()])}")
    
    with col_right:
        st.subheader("🏢 فعالیت شعب")
        df_br_display = df_br_sql.copy()
        max_tx = df_br_display['daily_transactions'].max()
        df_br_display['درصد اشغال'] = (df_br_display['daily_transactions'] / max_tx * 100).round(1)
        
        for _, row in df_br_display.iterrows():
            st.markdown(f"""
            <div style="margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between;">
                    <span><b>{row['branch_name']}</b></span>
                    <span>{row['daily_transactions']:,} تراکنش</span>
                </div>
                <div style="background-color: #f0f0f0; border-radius: 10px; height: 8px; margin-top: 3px;">
                    <div style="background-color: {'#4CAF50' if row['درصد اشغال'] < 60 else '#FF9800' if row['درصد اشغال'] < 80 else '#f44336'}; 
                                width: {row['درصد اشغال']}%; border-radius: 10px; height: 8px;"></div>
                </div>
                <div style="font-size: 12px; color: #666; margin-top: 2px;">
                    ⏳ نرخ ورود: {row['lambda_arrival']} نفر/ساعت | 🕒 سرویس: {row['mu_service']} نفر/ساعت
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.subheader("📊 تحلیل گرافیکی وضعیت شعب")
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        fig_tx = px.bar(
            df_br_sql,
            x='branch_name',
            y='daily_transactions',
            color='daily_transactions',
            title='حجم تراکنش روزانه شعب',
            labels={'branch_name': 'شعبه', 'daily_transactions': 'تعداد تراکنش'},
            color_continuous_scale='Blues'
        )
        fig_tx.update_layout(showlegend=False)
        st.plotly_chart(fig_tx, use_container_width=True)
    
    with col_chart2:
        role_dist = df_emp_sql['role'].value_counts().reset_index()
        role_dist.columns = ['نقش', 'تعداد']
        fig_pie = px.pie(
            role_dist,
            values='تعداد',
            names='نقش',
            title='توزیع نیروی انسانی بر اساس نقش',
            color_discrete_sequence=px.colors.sequential.Purples_r
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    st.markdown("---")
    st.subheader("🕐 فعالیت‌های اخیر سیستم")
    recent_activities = [
        {"زمان": "۱۴:۳۰", "کاربر": "admin", "عملکرد": "به‌روزرسانی بودجه شعبه مرکزی"},
        {"زمان": "۱۴:۱۵", "کاربر": "admin", "عملکرد": "اجرای الگوریتم تخصیص بهینه"},
        {"زمان": "۱۳:۴۵", "کاربر": "staff", "عملکرد": "مشاهده گزارش تراکنش‌ها"},
        {"زمان": "۱۳:۲۰", "کاربر": "admin", "عملکرد": "افزودن کارمند جدید"},
        {"زمان": "۱۲:۵۰", "کاربر": "staff", "عملکرد": "درخواست تحلیل تیم چابک"},
    ]
    df_activities = pd.DataFrame(recent_activities)
    st.dataframe(df_activities, use_container_width=True, hide_index=True)

# =========================================================
# ========== تب LP (فقط admin) ==========
# =========================================================
if st.session_state.user_role == "admin":
    with tab_lp:
        st.header("📊 تخصیص بهینه کارمندان به شعب")
        
        df_emp_sql, df_br_sql = get_sqlite_data()
        branch_analysis = get_branch_analysis(df_br_sql)
        
        st.subheader("👥 لیست کارمندان فعال")
        
        search = st.text_input("🔍 جستجوی کارمند (کد یا نام)", placeholder="مثال: EMP-101")
        
        if search:
            filtered_emp = df_emp_sql[df_emp_sql['employee_id'].str.contains(search, case=False, na=False)]
        else:
            filtered_emp = df_emp_sql
        
        st.dataframe(
            filtered_emp[['employee_id', 'role', 'salary']].rename(columns={
                'employee_id': 'کد پرسنلی',
                'role': 'سمت',
                'salary': 'حقوق'
            }),
            use_container_width=True,
            height=200
        )
        
        st.subheader("📊 تحلیل فعالیت لحظه‌ای شعب")
        
        col_analysis1, col_analysis2, col_analysis3, col_analysis4 = st.columns(4)
        
        with col_analysis1:
            st.metric(
                label="🏢 شلوغ‌ترین شعبه",
                value=branch_analysis.get('busiest', {}).get('name', 'نامشخص'),
                delta=f"{branch_analysis.get('busiest', {}).get('transactions', 0):,} تراکنش"
            )
        
        with col_analysis2:
            st.metric(
                label="🟢 کم‌ترافیک‌ترین شعبه",
                value=branch_analysis.get('quietest', {}).get('name', 'نامشخص'),
                delta=f"{branch_analysis.get('quietest', {}).get('transactions', 0):,} تراکنش"
            )
        
        with col_analysis3:
            st.metric(
                label="📈 میانگین تراکنش",
                value=f"{branch_analysis.get('average', 0):,.0f}",
                delta="تراکنش در روز"
            )
        
        with col_analysis4:
            st.metric(
                label="📊 مجموع تراکنش‌ها",
                value=f"{branch_analysis.get('total', 0):,}",
                delta="تراکنش در روز"
            )
        
        st.session_state.employee_data = {
            'list': df_emp_sql.to_dict('records'),
            'total': len(df_emp_sql),
            'roles': df_emp_sql['role'].value_counts().to_dict()
        }
        
        st.session_state.branch_analysis = branch_analysis
        st.session_state.branch_data = df_br_sql.to_dict('records')
        
        st.success("✅ اطلاعات کارمندان و تحلیل شعب برای چت‌بات ذخیره شد.")
        
        st.markdown("---")
        st.subheader("⚙️ اجرای بهینه‌سازی تخصیص")
        
        if st.button("🚀 اجرای بهینه‌سازی LP", type="primary"):
            with st.spinner("🔄 در حال حل..."):
                solver = LPSolver(employees, branches)
                result = solver.solve()
                st.session_state.lp_results = result
            
            if result['status'] == 'Optimal':
                st.success(f"✅ هزینه کل: {result['objective_value']:,.0f} تومان")
                
                assignment_data = []
                for emp_id, br_id in result['assignment'].items():
                    emp = next(e for e in employees if e.id == emp_id)
                    br = next(b for b in branches if b.id == br_id)
                    assignment_data.append({
                        'کارمند': emp.name,
                        'مهارت': emp.skill_level,
                        'شعبه': br.name,
                    })
                st.dataframe(pd.DataFrame(assignment_data), use_container_width=True)
            else:
                st.error(f"❌ خطا: {result['status']}")

# =========================================================
# ========== تب GA (فقط admin) ==========
# =========================================================
if st.session_state.user_role == "admin":
    with tab_ga:
        st.header("🧬 تیم‌سازی چابک با الگوریتم ژنتیک")
        
        col1, col2 = st.columns(2)
        with col1:
            team_size = st.slider("اندازه تیم", 2, 6, 3, key="ga_team_size")
        with col2:
            generations = st.slider("تعداد نسل‌ها", 10, 100, 30, key="ga_generations")
        
        if st.button("🧬 اجرای الگوریتم ژنتیک", type="primary"):
            with st.spinner("🔄 در حال تکامل..."):
                ga = GeneticAlgorithm(
                    employees=employees,
                    team_size=team_size,
                    population_size=20,
                    generations=generations,
                    mutation_rate=0.1
                )
                best = ga.evolve()
                
                best_team = ga.get_best_team()
                fitness_history = ga.get_fitness_history()
                
                st.session_state.ga_results = {
                    'fitness': ga.best_fitness,
                    'skills_covered': list(set().union(*[set(e.skills) for e in best_team])),
                    'average_behavioral': 7.5,
                    'team': best_team,
                    'fitness_history': fitness_history,
                    'generations': generations
                }
            
            st.success(f"✅ بهترین برازندگی: {ga.best_fitness:.2f}")
            
            team = ga.get_best_team()
            team_data = []
            for i, emp in enumerate(team, 1):
                team_data.append({
                    'ردیف': i,
                    'نام': emp.name,
                    'مهارت': emp.skill_level,
                    'تجربه': f"{emp.experience_years} سال",
                    'مهارت‌ها': ', '.join(emp.skills)
                })
            
            col_table, col_metrics = st.columns([2, 1])
            
            with col_table:
                st.subheader("👥 بهترین تیم پیدا شده")
                st.dataframe(pd.DataFrame(team_data), use_container_width=True)
            
            with col_metrics:
                st.subheader("📊 آمار تیم")
                st.metric("🎯 برازندگی نهایی", f"{ga.best_fitness:.2f}")
                st.metric("👤 تعداد اعضا", len(team))
                st.metric("📚 مهارت‌های منحصربه‌فرد", len(set().union(*[set(e.skills) for e in team])))
            
            st.markdown("---")
            st.subheader("📈 نمودارهای تحلیلی")
            
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                fitness_history = ga.get_fitness_history()
                df_fitness = pd.DataFrame({
                    'نسل': list(range(len(fitness_history))),
                    'برازندگی': fitness_history
                })
                
                fig_line = px.line(
                    df_fitness,
                    x='نسل',
                    y='برازندگی',
                    title='📈 روند بهبود برازندگی',
                    labels={'نسل': 'تعداد نسل', 'برازندگی': 'امتیاز برازندگی'},
                    color_discrete_sequence=['#6C63FF']
                )
                
                fig_line.add_scatter(
                    x=[0, len(fitness_history)-1],
                    y=[fitness_history[0], fitness_history[-1]],
                    mode='markers',
                    marker=dict(size=10, color=['#FF6B6B', '#4CAF50']),
                    name='نقاط شروع و پایان'
                )
                
                fig_line.update_layout(hovermode='x', showlegend=True)
                st.plotly_chart(fig_line, use_container_width=True)
            
            with col_chart2:
                skill_analysis = analyze_team_skills(team)
                
                if skill_analysis:
                    df_skills = pd.DataFrame({
                        'مهارت': list(skill_analysis.keys()),
                        'تعداد': list(skill_analysis.values())
                    })
                    
                    fig_bar = px.bar(
                        df_skills,
                        x='مهارت',
                        y='تعداد',
                        title='📊 توزیع مهارت‌ها در تیم',
                        labels={'مهارت': 'مهارت', 'تعداد': 'تعداد اعضا'},
                        color='تعداد',
                        color_continuous_scale='Viridis'
                    )
                    fig_bar.update_layout(xaxis={'categoryorder': 'total descending'}, showlegend=False)
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("ℹ️ اطلاعات مهارتی برای نمایش وجود ندارد.")
        
        else:
            st.info("ℹ️ برای مشاهده نمودارهای تحلیلی، دکمه اجرا را بزنید.")
            
            sample_data = pd.DataFrame({
                'نسل': list(range(30)),
                'برازندگی': [20 + i * 1.5 + (i ** 0.5) * 2 for i in range(30)]
            })
            
            fig_sample = px.line(
                sample_data,
                x='نسل',
                y='برازندگی',
                title='📈 روند تقریبی برازندگی (پیش‌نمایش)',
                labels={'نسل': 'تعداد نسل', 'برازندگی': 'امتیاز برازندگی'},
                color_discrete_sequence=['#B3B3B3']
            )
            fig_sample.update_layout(showlegend=False)
            st.plotly_chart(fig_sample, use_container_width=True)

# =========================================================
# ========== تب چت‌بات (همه کاربران) ==========
# =========================================================
with tab_chat:
    st.header("🤖 چت‌بات هوشمند تحلیل‌گر")
    st.caption("این چت‌بات به دیتابیس SQLite متصل است و با اعداد واقعی پاسخ می‌دهد.")
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "سلام! من مشاور تحلیلی بانک هستم. سوال بپرسید!"}
        ]

    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.write(chat["content"])

    if user_prompt := st.chat_input("سوال خود را بپرسید...", key="chat_input"):
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.write(user_prompt)

        with st.chat_message("assistant"):
            lp_results = st.session_state.get('lp_results', None)
            ga_results = st.session_state.get('ga_results', None)
            
            response = bot.generate_analysis_response(
                query=user_prompt,
                lp_results=lp_results,
                ga_results=ga_results
            )
            st.write(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response})

st.markdown("---")
st.caption("🏦 سیستم مدیریت سرمایه انسانی - یکپارچه")