import streamlit as st
import pandas as pd
import sqlite3
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io

# Sahifa sozlamalari
st.set_page_config(page_title="Qurilish Boshqaruvi | Prorab Abdulla", layout="wide", initial_sidebar_state="collapsed")

# 🎨 Toza va Zamonaviy CSS dizayn
st.markdown("""
    <style>
    .main-header {
        font-size: 26px;
        font-weight: 700;
        color: #1a73e8;
        margin-bottom: 10px;
    }
    .card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .footer-brand {
        text-align: center;
        margin-top: 50px;
        font-size: 15px;
        color: #6c757d;
        font-weight: 600;
    }
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        font-weight: 600;
        background-color: #1a73e8;
        color: white;
    }
    .stButton>button:hover {
        background-color: #1557b0;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Ma'lumotlar bazasi
def init_db():
    conn = sqlite3.connect("construction_clean.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    role TEXT,
                    project_id INTEGER
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS owner_works (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    job_name TEXT,
                    unit TEXT,
                    quantity REAL,
                    price_per_unit REAL,
                    total_price REAL
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS worker_works (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    job_name TEXT,
                    unit TEXT,
                    quantity REAL,
                    price_per_unit REAL,
                    total_price REAL
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS owner_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    date TEXT,
                    amount REAL,
                    note TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS worker_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    worker_name TEXT,
                    date TEXT,
                    amount REAL,
                    note TEXT
                )''')
    
    # Prorab Abdulla hisobi
    c.execute("SELECT * FROM users WHERE username = 'abdulla'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role, project_id) VALUES ('abdulla', '1234', 'admin', NULL)")
    conn.commit()
    conn.close()

init_db()

def get_data(query, params=()):
    conn = sqlite3.connect("construction_clean.db")
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute_query(query, params=()):
    conn = sqlite3.connect("construction_clean.db")
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None

# =========================================================
# 1. LOGIN SAHIFASI
# =========================================================
if not st.session_state['logged_in']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<h2 style='text-align: center; color: #1a73e8;'>🏗️ Qurilish Boshqaruvi</h2>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("login_form"):
            st.markdown("### 🔐 Tizimga kirish")
            u_name = st.text_input("Login")
            u_pass = st.text_input("Parol", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("Kirish 🚀"):
                res = get_data("SELECT * FROM users WHERE username = ? AND password = ?", (u_name, u_pass))
                if not res.empty:
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = res.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("❌ Login yoki parol xato!")
        st.markdown("<div class='footer-brand'>👷‍♂️ Prorab: Abdulla</div>", unsafe_allow_html=True)

# =========================================================
# 2. TIZIM ICHKI QISMI
# =========================================================
else:
    user = st.session_state['user_info']
    role = user['role']
    
    st.sidebar.title(f"👤 {user['username'].capitalize()}")
    st.sidebar.markdown(f"**Rolingiz:** `{role.upper()}`")
    if st.sidebar.button("🚪 Tizimdan chiqish"):
        st.session_state['logged_in'] = False
        st.session_state['user_info'] = None
        st.rerun()
    st.sidebar.markdown("---")

    # ---------------------------------------------------------
    # A) PRORAB ABDULLA UCHUN
    # ---------------------------------------------------------
    if role == 'admin':
        st.markdown("<div class='main-header'>⚙️ Prorab Abdulla — Boshqaruv Markazi</div>", unsafe_allow_html=True)
        
        # Uy qo'shish va tanlash qismi
        col_h1, col_h2 = st.columns([2, 1])
        with col_h1:
            projects = get_data("SELECT * FROM projects")
            if not projects.empty:
                p_dict = {row['project_name']: row['id'] for _, row in projects.iterrows()}
                sel_p = st.selectbox("📂 Ishlamoqchi bo'lgan uyni tanlang:", list(p_dict.keys()))
                active_pid = p_dict[sel_p]
            else:
                active_pid = None
                st.warning("Hali uylar qo'shilmagan. O'ng tomondan uy qo'shing.")
        with col_h2:
            with st.form("add_house_form", clear_on_submit=True):
                h_name = st.text_input("Yangi uy nomi:")
                if st.form_submit_button("➕ Uy qo'shish") and h_name:
                    execute_query("INSERT INTO projects (project_name) VALUES (?)", (h_name,))
                    st.success("Qo'shildi!")
                    st.rerun()

        if active_pid:
            st.markdown("---")
            # Asosiy menyu (Tablar)
            t1, t2, t3, t4, t5, t6 = st.tabs([
                "🏠 Uy Egasi Smetasi", 
                "👷 Ustalar Smetasi", 
                "💰 Uy Egasi Pullari", 
                "💵 Ustalar Ish Haqlari", 
                "🔑 Login Berish",
                "📄 PDF Hisobot"
            ])
            
            # 1. Uy Egasi Smetasi
            with t1:
                st.markdown("### 🏠 Uy Egasi Smetasi")
                with st.form("pr_ow", clear_on_submit=True):
                    c1, c2, c3, c4 = st.columns(4)
                    jn = c1.text_input("Ish nomi")
                    un = c2.selectbox("Birlik", ["kv.m", "kub.m", "metr", "dona", "komplekt"])
                    qt = c3.number_input("Hajmi", min_value=0.0, step=0.1)
                    pr = c4.number_input("1 Birlik narxi", min_value=0.0, step=1000.0)
                    if st.form_submit_button("Qo'shish") and jn:
                        execute_query("INSERT INTO owner_works (project_id, job_name, unit, quantity, price_per_unit, total_price) VALUES (?, ?, ?, ?, ?, ?)",
                                      (active_pid, jn, un, qt, pr, qt*pr))
                        st.rerun()
                
                df = get_data("SELECT id, job_name, unit, quantity, price_per_unit, total_price FROM owner_works WHERE project_id = ?", (active_pid,))
                if not df.empty:
                    v_df = df[['job_name', 'unit', 'quantity', 'price_per_unit', 'total_price']].copy()
                    v_df.columns = ["Ish nomi", "Birlik", "Hajmi", "1 Birlik narxi", "Jami qiymat"]
                    v_df.index = range(1, len(v_df) + 1)
                    st.dataframe(v_df, use_container_width=True)
                    
                    del_r = st.number_input("O'chiriladigan qator raqami:", min_value=1, max_value=len(df), step=1, key="dow")
                    if st.button("Qatorni o'chirish", key="bou"):
                        execute_query("DELETE FROM owner_works WHERE id = ?", (df.iloc[del_r - 1]['id'],))
                        st.rerun()
                    st.metric("Uy egasi smetasining jami qiymati:", f"{df['total_price'].sum():,.2f}")
                else:
                    st.info("Hozircha ma'lumot kiritilmagan.")

            # 2. Ustalar Smetasi
            with t2:
                st.markdown("### 👷 Ustalar Smetasi")
                with st.form("pr_ww", clear_on_submit=True):
                    c1, c2, c3, c4 = st.columns(4)
                    jn = c1.text_input("Ish nomi", key="jn2")
                    un = c2.selectbox("Birlik", ["kv.m", "kub.m", "metr", "dona", "komplekt"], key="un2")
                    qt = c3.number_input("Hajmi", min_value=0.0, step=0.1, key="qt2")
                    pr = c4.number_input("1 Birlik ish haqi", min_value=0.0, step=1000.0, key="pr2")
                    if st.form_submit_button("Qo'shish", key="btn2") and jn:
                        execute_query("INSERT INTO worker_works (project_id, job_name, unit, quantity, price_per_unit, total_price) VALUES (?, ?, ?, ?, ?, ?)",
                                      (active_pid, jn, un, qt, pr, qt*pr))
                        st.rerun()
                
                df = get_data("SELECT id, job_name, unit, quantity, price_per_unit, total_price FROM worker_works WHERE project_id = ?", (active_pid,))
                if not df.empty:
                    v_df = df[['job_name', 'unit', 'quantity', 'price_per_unit', 'total_price']].copy()
                    v_df.columns = ["Ish nomi", "Birlik", "Hajmi", "1 Birlik ish haqi", "Jami ish haqi"]
                    v_df.index = range(1, len(v_df) + 1)
                    st.dataframe(v_df, use_container_width=True)
                    
                    del_r = st.number_input("O'chiriladigan qator raqami:", min_value=1, max_value=len(df), step=1, key="dww")
                    if st.button("Qatorni o'chirish", key="bow"):
                        execute_query("DELETE FROM worker_works WHERE id = ?", (df.iloc[del_r - 1]['id'],))
                        st.rerun()
                    st.metric("Ustalarning jami ish haqi qiymati:", f"{df['total_price'].sum():,.2f}")
                else:
                    st.info("Hozircha ma'lumot kiritilmagan.")

            # 3. Uy Egasidan Olingan Pullar
            with t3:
                st.markdown("### 💰 Uy Egasidan Olingan Pullar")
                with st.form("pr_op", clear_on_submit=True):
                    c1, c2, c3 = st.columns(3)
                    dt = c1.date_input("Sana")
                    am = c2.number_input("Summa", min_value=0.0, step=10000.0)
                    nt = c3.text_input("Izoh")
                    if st.form_submit_button("Saqlash") and am > 0:
                        execute_query("INSERT INTO owner_payments (project_id, date, amount, note) VALUES (?, ?, ?, ?)", (active_pid, str(dt), am, nt))
                        st.rerun()
                
                df = get_data("SELECT id, date, amount, note FROM owner_payments WHERE project_id = ?", (active_pid,))
                if not df.empty:
                    v_df = df[['date', 'amount', 'note']].copy()
                    v_df.columns = ["Sana", "Olingan summa", "Izoh"]
                    v_df.index = range(1, len(v_df) + 1)
                    st.dataframe(v_df, use_container_width=True)
                    
                    del_r = st.number_input("O'chiriladigan qator raqami:", min_value=1, max_value=len(df), step=1, key="dop")
                    if st.button("Qatorni o'chirish", key="bop"):
                        execute_query("DELETE FROM owner_payments WHERE id = ?", (df.iloc[del_r - 1]['id'],))
                        st.rerun()
                    st.metric("Jami olingan pul:", f"{df['amount'].sum():,.2f}")
                else:
                    st.info("To'lovlar kiritilmagan.")

            # 4. Ustalarga Berilgan Pullar
            with t4:
                st.markdown("### 💵 Ustalarga Berilgan Pullar")
                with st.form("pr_wp", clear_on_submit=True):
                    c1, c2, c3, c4 = st.columns(4)
                    wn = c1.text_input("Usta nomi")
                    dt = c2.date_input("Sana", key="dt2")
                    am = c3.number_input("Summa", min_value=0.0, step=5000.0, key="am2")
                    nt = c4.text_input("Izoh", key="nt2")
                    if st.form_submit_button("Saqlash", key="sb2") and am > 0:
                        execute_query("INSERT INTO worker_payments (project_id, worker_name, date, amount, note) VALUES (?, ?, ?, ?, ?)", (active_pid, wn, str(dt), am, nt))
                        st.rerun()
                
                df = get_data("SELECT id, worker_name, date, amount, note FROM worker_payments WHERE project_id = ?", (active_pid,))
                if not df.empty:
                    v_df = df[['worker_name', 'date', 'amount', 'note']].copy()
                    v_df.columns = ["Usta nomi", "Sana", "Berilgan summa", "Izoh"]
                    v_df.index = range(1, len(v_df) + 1)
                    st.dataframe(v_df, use_container_width=True)
                    
                    del_r = st.number_input("O'chiriladigan qator raqami:", min_value=1, max_value=len(df), step=1, key="dwp")
                    if st.button("Qatorni o'chirish", key="bwp"):
                        execute_query("DELETE FROM worker_payments WHERE id = ?", (df.iloc[del_r - 1]['id'],))
                        st.rerun()
                    st.metric("Jami berilgan pul:", f"{df['amount'].sum():,.2f}")
                else:
                    st.info("To'lovlar kiritilmagan.")

            # 5. Login Berish
            with t5:
                st.markdown(f"### 🔑 '{sel_p}' uchun Login va Parol berish")
                c_l1, c_l2 = st.columns(2)
                with c_l1:
                    with st.form("form_o_log", clear_on_submit=True):
                        st.markdown("##### 🏠 Uy Egasi")
                        lg = st.text_input("Login", key="l1")
                        ps = st.text_input("Parol", type="password", key="p1")
                        if st.form_submit_button("Uy egasiga login berish") and lg and ps:
                            try:
                                execute_query("INSERT INTO users (username, password, role, project_id) VALUES (?, ?, 'uy_egasi', ?)", (lg, ps, active_pid))
                                st.success("Muvaffaqiyatli yaratildi!")
                            except:
                                st.error("Bu login allaqachon mavjud!")
                with c_l2:
                    with st.form("form_w_log", clear_on_submit=True):
                        st.markdown("##### 👷 Usta")
                        lg = st.text_input("Login", key="l2")
                        ps = st.text_input("Parol", type="password", key="p2")
                        if st.form_submit_button("Ustaga login berish") and lg and ps:
                            try:
                                execute_query("INSERT INTO users (username, password, role, project_id) VALUES (?, ?, 'usta', ?)", (lg, ps, active_pid))
                                st.success("Muvaffaqiyatli yaratildi!")
                            except:
                                st.error("Bu login allaqachon mavjud!")
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("##### 👥 Berilgan loginlar ro'yxati")
                u_df = get_data("SELECT id, username AS 'Login', role AS 'Rol' FROM users WHERE project_id = ?", (active_pid,))
                if not u_df.empty:
                    u_df.index = range(1, len(u_df) + 1)
                    st.dataframe(u_df, use_container_width=True)
                    u_id = st.number_input("O'chiriladigan User ID si:", min_value=1, step=1)
                    if st.button("Foydalanuvchini o'chirish"):
                        execute_query("DELETE FROM users WHERE id = ?", (u_id,))
                        st.success("O'chirildi!")
                        st.rerun()
                else:
                    st.info("Hozircha login berilmagan.")

            # 6. PDF Hisobot
            with t6:
                st.markdown("### 📄 PDF Hisobot Yaratish")
                def generate_pdf():
                    buffer = io.BytesIO()
                    doc = SimpleDocTemplate(buffer, pagesize=A4)
                    elements = []
                    styles = getSampleStyleSheet()
                    elements.append(Paragraph(f"<b>Obyekt Hisoboti: {sel_p}</b>", styles['Title']))
                    elements.append(Paragraph("<b>Prorab: Abdulla</b>", styles['Normal']))
                    elements.append(Spacer(1, 12))
                    
                    w_data = get_data("SELECT job_name, unit, quantity, price_per_unit, total_price FROM owner_works WHERE project_id = ?", (active_pid,))
                    if not w_data.empty:
                        data = [["Ish nomi", "Birlik", "Hajm", "Narx", "Jami"]]
                        for _, r in w_data.iterrows():
                            data.append([str(r['job_name']), str(r['unit']), str(r['quantity']), str(r['price_per_unit']), str(r['total_price'])])
                        t = Table(data)
                        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.grey), ('GRID', (0,0), (-1,-1), 1, colors.black)]))
                        elements.append(t)
                    doc.build(elements)
                    buffer.seek(0)
                    return buffer
                st.download_button("📥 PDF Hisobotni Yuklab Olish", generate_pdf(), file_name=f"{sel_p}_hisobot.pdf", mime="application/pdf")

    # ---------------------------------------------------------
    # B) UY EGASI PANELI
    # ---------------------------------------------------------
    elif role == 'uy_egasi':
        p_id = user['project_id']
        p_info = get_data("SELECT project_name FROM projects WHERE id = ?", (p_id,))
        p_name = p_info.iloc[0]['project_name'] if not p_info.empty else "Uyingiz"
        
        st.markdown(f"<div class='main-header'>🏡 {p_name} — Uy Egasi Paneli</div>", unsafe_allow_html=True)
        
        t1, t2 = st.tabs(["📊 Smetani Ko'rish", "💰 Men Bergan Pullar"])
        with t1:
            df = get_data("SELECT job_name, unit, quantity, price_per_unit, total_price FROM owner_works WHERE project_id = ?", (p_id,))
            if not df.empty:
                df.columns = ["Ish nomi", "Birlik", "Hajmi", "1 Birlik narxi", "Jami qiymat"]
                df.index = range(1, len(df) + 1)
                st.dataframe(df, use_container_width=True)
                st.metric("Uyingizning umumiy summasi:", f"{df['Jami qiymat'].sum():,.2f}")
            else:
                st.info("Hozircha smeta kiritilmagan.")
        with t2:
            df = get_data("SELECT date, amount, note FROM owner_payments WHERE project_id = ?", (p_id,))
            if not df.empty:
                df.columns = ["Sana", "Berilgan summa", "Izoh"]
                df.index = range(1, len(df.index) + 1)
                st.dataframe(df, use_container_width=True)
                given = df['Berilgan summa'].sum()
                tot_df = get_data("SELECT total_price FROM owner_works WHERE project_id = ?", (p_id,))
                tot = tot_df['total_price'].sum() if not tot_df.empty else 0
                c1, c2 = st.columns(2)
                c1.metric("Jami bergan pulingiz:", f"{given:,.2f}")
                c2.metric("Qolgan qarzdorlik:", f"{tot - given:,.2f}")
            else:
                st.info("To'lovlar tarixi yo'q.")

    # ---------------------------------------------------------
    # C) USTA PANELI
    # ---------------------------------------------------------
    elif role == 'usta':
        p_id = user['project_id']
        p_info = get_data("SELECT project_name FROM projects WHERE id = ?", (p_id,))
        p_name = p_info.iloc[0]['project_name'] if not p_info.empty else "Ob'ekt"
        
        st.markdown(f"<div class='main-header'>👷 {p_name} — Usta Paneli</div>", unsafe_allow_html=True)
        
        t1, t2 = st.tabs(["📋 Ish Hajmlari va Ish Haqi", "💵 Olingan Pullar Tarixi"])
        with t1:
            df = get_data("SELECT job_name, unit, quantity, price_per_unit, total_price FROM worker_works WHERE project_id = ?", (p_id,))
            if not df.empty:
                df.columns = ["Ish nomi", "Birlik", "Hajmi", "1 Birlik ish haqi", "Jami ish haqi"]
                df.index = range(1, len(df.index) + 1)
                st.dataframe(df, use_container_width=True)
                st.metric("Umumiy ish haqigingiz:", f"{df['Jami ish haqi'].sum():,.2f}")
            else:
                st.info("Hozircha ishlar kiritilmagan.")
        with t2:
            df = get_data("SELECT worker_name, date, amount, note FROM worker_payments WHERE project_id = ?", (p_id,))
            if not df.empty:
                df.columns = ["Usta nomi", "Sana", "Olingan summa", "Izoh"]
                df.index = range(1, len(df.index) + 1)
                st.dataframe(df, use_container_width=True)
                st.metric("Siz olgan jami pul:", f"{df['Olingan summa'].sum():,.2f}")
            else:
                st.info("Sizga hali pul berilmagan.")

    st.markdown("---")
    st.markdown("<div class='footer-brand'>👷‍♂️ Prorab: Abdulla — Qurilish Boshqaruvi Tizimi</div>", unsafe_allow_html=True)
