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

# 🎨 Zamonaviy va Chiroyli CSS Dizayn
st.markdown("""
    <style>
    /* Asosiy fon va shriftlar */
    .main {
        background-color: #f8f9fa;
    }
    /* Login oynasi uchun card dizayni */
    .login-container {
        background: #ffffff;
        padding: 40px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        max-width: 450px;
        margin: 50px auto;
    }
    .login-title {
        text-align: center;
        color: #1a73e8;
        font-weight: 800;
        margin-bottom: 25px;
    }
    .footer-brand {
        text-align: center;
        margin-top: 40px;
        font-size: 15px;
        color: #5f6368;
        font-weight: 600;
        letter-spacing: 1px;
    }
    /* Tugmalar dizayni */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        height: 45px;
        background-color: #1a73e8;
        color: white;
    }
    .stButton>button:hover {
        background-color: #1557b0;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Ma'lumotlar bazasini yaratish
def init_db():
    conn = sqlite3.connect("construction_v2.db")
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
    
    # Prorab Abdulla boshlang'ich hisobi
    c.execute("SELECT * FROM users WHERE username = 'abdulla'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role, project_id) VALUES ('abdulla', '1234', 'admin', NULL)")
    conn.commit()
    conn.close()

init_db()

def get_data(query, params=()):
    conn = sqlite3.connect("construction_v2.db")
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute_query(query, params=()):
    conn = sqlite3.connect("construction_v2.db")
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None

# =========================================================
# 1. ZAMONAVIY LOGIN SAHIFASI
# =========================================================
if not st.session_state['logged_in']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        st.markdown("""
            <div class='login-container'>
                <h2 class='login-title'>🏗️ Qurilish Nazorati</h2>
            </div>
        """, unsafe_allow_html=True)
        
        # Asosiy login formasi
        with st.form("login_form"):
            st.markdown("### 🔐 Tizimga kirish")
            input_user = st.text_input("Foydalanuvchi nomi (Login)")
            input_pass = st.text_input("Maxfiy parol", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            btn = st.form_submit_button("Tizimga kirish 🚀")
            
            if btn:
                user_data = get_data("SELECT * FROM users WHERE username = ? AND password = ?", (input_user, input_pass))
                if not user_data.empty:
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = user_data.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("❌ Login yoki parol xato kiritildi!")
                    
        st.markdown("<div class='footer-brand'>👷‍♂️ Prorab: Abdulla — Boshqaruv Tizimi</div>", unsafe_allow_html=True)

# =========================================================
# 2. TIZIM ICHKI QISMI (ROLE BO'YICHA)
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
    # A) PRORAB ABDULLA UCHUN BOSHQARUV PANELI
    # ---------------------------------------------------------
    if role == 'admin':
        st.sidebar.subheader("⚙️ Prorab Paneli")
        
        with st.sidebar.expander("➕ Yangi uy qo'shish"):
            new_house = st.text_input("Uy nomi (Masalan: 1-uy - Alisher aka):")
            if st.button("Uyni bazaga qo'shish"):
                if new_house:
                    execute_query("INSERT INTO projects (project_name) VALUES (?)", (new_house,))
                    st.success("Uy qo'shildi!")
                    st.rerun()

        projects = get_data("SELECT * FROM projects")
        
        if not projects.empty:
            proj_dict = {row['project_name']: row['id'] for _, row in projects.iterrows()}
            selected_p = st.sidebar.selectbox("🏠 Qaysi uyni boshqarasiz?", list(proj_dict.keys()))
            active_p_id = proj_dict[selected_p]
            
            with st.sidebar.expander("🗑️ Uyni o'chirish"):
                if st.button("Tanlangan uyni o'chirish"):
                    execute_query("DELETE FROM projects WHERE id = ?", (active_p_id,))
                    execute_query("DELETE FROM users WHERE project_id = ?", (active_p_id,))
                    st.success("O'chirildi!")
                    st.rerun()

            st.title(f"🏠 Tanlangan Obyekt: {selected_p}")
            st.caption("Prorab Abdulla — Barcha hisob-kitoblar markazi")
            
            # Asosiy bo'limlar (Tablar)
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📊 Uy Egasi Smetasi", 
                "👷 Ustalar Smetasi", 
                "💰 Uy Egasi Pullari", 
                "💵 Ustalar Ish Haqlari", 
                "📄 PDF Hisobot"
            ])
            
            # 1. Uy egasi smetasi
            with tab1:
                st.subheader("🏠 Uy Egasi Smetasi (Narxlar va Hajm)")
                with st.expander("➕ Yangi ish va narx qo'shish"):
                    with st.form("ow_add"):
                        jn = st.text_input("Ish nomi (Masalan: Suvoq)")
                        un = st.selectbox("O'lchov birligi", ["kv.m", "kub.m", "metr", "dona", "komplekt"])
                        qt = st.number_input("Hajmi", min_value=0.0, step=0.1)
                        pr = st.number_input("Uy egasiga 1 birlik narxi", min_value=0.0, step=1000.0)
                        if st.form_submit_button("Qo'shish") and jn:
                            execute_query("INSERT INTO owner_works (project_id, job_name, unit, quantity, price_per_unit, total_price) VALUES (?, ?, ?, ?, ?, ?)",
                                          (active_p_id, jn, un, qt, pr, qt*pr))
                            st.rerun()
                
                df_ow = get_data("SELECT id, job_name, unit, quantity, price_per_unit, total_price FROM owner_works WHERE project_id = ?", (active_p_id,))
                if not df_ow.empty:
                    d_view = df_ow[['job_name', 'unit', 'quantity', 'price_per_unit', 'total_price']].copy()
                    d_view.columns = ["Ish nomi", "Birlik", "Hajmi", "1 Birlik narxi", "Jami qiymat"]
                    d_view.index = range(1, len(d_view) + 1)
                    st.dataframe(d_view, use_container_width=True)
                    
                    with st.expander("🗑️ Qatorni o'chirish"):
                        r_num = st.number_input("O'chiriladigan qator raqami:", min_value=1, max_value=len(df_ow), step=1, key="del_ow_pr")
                        if st.button("O'chirish", key="btn_del_ow"):
                            t_id = df_ow.iloc[r_num - 1]['id']
                            execute_query("DELETE FROM owner_works WHERE id = ?", (t_id,))
                            st.rerun()
                    st.metric("Uy egasi smetasining umumiy qiymati:", f"{df_ow['total_price'].sum():,.2f}")
                else:
                    st.info("Hozircha ma'lumot yo'q.")

            # 2. Ustalar smetasi
            with tab2:
                st.subheader("👷 Ustalar Smetasi (Ish Haqi va Hajm)")
                with st.expander("➕ Usta uchun ish qo'shish"):
                    with st.form("ww_add"):
                        jn = st.text_input("Ish nomi")
                        un = st.selectbox("Birlik", ["kv.m", "kub.m", "metr", "dona", "komplekt"], key="u_b")
                        qt = st.number_input("Hajmi", min_value=0.0, step=0.1, key="u_h")
                        pr = st.number_input("Ustaga 1 birlik ish haqi", min_value=0.0, step=1000.0, key="u_n")
                        if st.form_submit_button("Qo'shish") and jn:
                            execute_query("INSERT INTO worker_works (project_id, job_name, unit, quantity, price_per_unit, total_price) VALUES (?, ?, ?, ?, ?, ?)",
                                          (active_p_id, jn, un, qt, pr, qt*pr))
                            st.rerun()
                
                df_ww = get_data("SELECT id, job_name, unit, quantity, price_per_unit, total_price FROM worker_works WHERE project_id = ?", (active_p_id,))
                if not df_ww.empty:
                    d_view = df_ww[['job_name', 'unit', 'quantity', 'price_per_unit', 'total_price']].copy()
                    d_view.columns = ["Ish nomi", "Birlik", "Hajmi", "1 Birlik ish haqi", "Jami ish haqi"]
                    d_view.index = range(1, len(d_view) + 1)
                    st.dataframe(d_view, use_container_width=True)
                    
                    with st.expander("🗑️ Qatorni o'chirish"):
                        r_num = st.number_input("O'chiriladigan qator raqami:", min_value=1, max_value=len(df_ww), step=1, key="del_ww_pr")
                        if st.button("O'chirish", key="btn_del_ww"):
                            t_id = df_ww.iloc[r_num - 1]['id']
                            execute_query("DELETE FROM worker_works WHERE id = ?", (t_id,))
                            st.rerun()
                    st.metric("Ustalarning umumiy ish haqi qiymati:", f"{df_ww['total_price'].sum():,.2f}")
                else:
                    st.info("Hozircha ma'lumot yo'q.")

            # 3. Uy egasidan olingan pullar
            with tab3:
                st.subheader("💰 Uy Egasidan Olingan Mablag'lar")
                with st.expander("➕ Pul olishni yozish"):
                    with st.form("op_add"):
                        dt = st.date_input("Sana")
                        am = st.number_input("Summa", min_value=0.0, step=10000.0)
                        nt = st.text_input("Izoh")
                        if st.form_submit_button("Saqlash") and am > 0:
                            execute_query("INSERT INTO owner_payments (project_id, date, amount, note) VALUES (?, ?, ?, ?)",
                                          (active_p_id, str(dt), am, nt))
                            st.rerun()
                
                df_op = get_data("SELECT id, date, amount, note FROM owner_payments WHERE project_id = ?", (active_p_id,))
                if not df_op.empty:
                    d_view = df_op[['date', 'amount', 'note']].copy()
                    d_view.columns = ["Sana", "Olingan summa", "Izoh"]
                    d_view.index = range(1, len(d_view) + 1)
                    st.dataframe(d_view, use_container_width=True)
                    
                    with st.expander("🗑️ To'lovni o'chirish"):
                        r_num = st.number_input("O'chiriladigan qator raqami:", min_value=1, max_value=len(df_op), step=1, key="del_op_pr")
                        if st.button("O'chirish", key="btn_del_op"):
                            t_id = df_op.iloc[r_num - 1]['id']
                            execute_query("DELETE FROM owner_payments WHERE id = ?", (t_id,))
                            st.rerun()
                    st.metric("Uy egasidan olingan jami pul:", f"{df_op['amount'].sum():,.2f}")
                else:
                    st.info("To'lovlar kiritilmagan.")

            # 4. Ustalarga berilgan pullar
            with tab4:
                st.subheader("💵 Ustalarga Berilgan Ish Haqlari")
                with st.expander("➕ Ustaga pul berish"):
                    with st.form("wp_add"):
                        wn = st.text_input("Usta ismi")
                        dt = st.date_input("Sana")
                        am = st.number_input("Summa", min_value=0.0, step=5000.0)
                        nt = st.text_input("Izoh")
                        if st.form_submit_button("Saqlash") and am > 0:
                            execute_query("INSERT INTO worker_payments (project_id, worker_name, date, amount, note) VALUES (?, ?, ?, ?, ?)",
                                          (active_p_id, wn, str(dt), am, nt))
                            st.rerun()
                
                df_wp = get_data("SELECT id, worker_name, date, amount, note FROM worker_payments WHERE project_id = ?", (active_p_id,))
                if not df_wp.empty:
                    d_view = df_wp[['worker_name', 'date', 'amount', 'note']].copy()
                    d_view.columns = ["Usta nomi", "Sana", "Berilgan summa", "Izoh"]
                    d_view.index = range(1, len(d_view) + 1)
                    st.dataframe(d_view, use_container_width=True)
                    
                    with st.expander("🗑️ To'lovni o'chirish"):
                        r_num = st.number_input("O'chiriladigan qator raqami:", min_value=1, max_value=len(df_wp), step=1, key="del_wp_pr")
                        if st.button("O'chirish", key="btn_del_wp"):
                            t_id = df_wp.iloc[r_num - 1]['id']
                            execute_query("DELETE FROM worker_payments WHERE id = ?", (t_id,))
                            st.rerun()
                    st.metric("Ustalarga berilgan jami pul:", f"{df_wp['amount'].sum():,.2f}")
                else:
                    st.info("Ustalar to'lovlari kiritilmagan.")

            # 5. PDF
            with tab5:
                st.subheader("📄 PDF Hisobot Yaratish")
                def generate_pdf():
                    buffer = io.BytesIO()
                    doc = SimpleDocTemplate(buffer, pagesize=A4)
                    elements = []
                    styles = getSampleStyleSheet()
                    elements.append(Paragraph(f"<b>Obyekt Hisoboti: {selected_p}</b>", styles['Title']))
                    elements.append(Paragraph("<b>Prorab: Abdulla</b>", styles['Normal']))
                    elements.append(Spacer(1, 12))
                    
                    w_data = get_data("SELECT job_name, unit, quantity, price_per_unit, total_price FROM owner_works WHERE project_id = ?", (active_p_id,))
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
                st.download_button("📥 PDF Hisobotni Yuklab Olish", generate_pdf(), file_name=f"{selected_p}_hisobot.pdf", mime="application/pdf")

            # Login/Parol yaratish bo'limi
            st.markdown("---")
            st.subheader(f"🔑 '{selected_p}' uchun Login va Parol berish")
            col_l1, col_l2 = st.columns(2)
            
            with col_l1:
                with st.form("u_form_1"):
                    st.markdown("##### 🏠 Uy Egasi uchun")
                    o_log = st.text_input("Login", key="ol")
                    o_pas = st.text_input("Parol", type="password", key="op")
                    if st.form_submit_button("Uy egasiga login berish"):
                        if o_log and o_pas:
                            try:
                                execute_query("INSERT INTO users (username, password, role, project_id) VALUES (?, ?, 'uy_egasi', ?)", (o_log, o_pas, active_p_id))
                                st.success("Muvaffaqiyatli yaratildi!")
                            except:
                                st.error("Bu login band!")
                                
            with col_l2:
                with st.form("u_form_2"):
                    st.markdown("##### 👷 Usta uchun")
                    w_log = st.text_input("Login", key="wl")
                    w_pas = st.text_input("Parol", type="password", key="wp")
                    if st.form_submit_button("Ustaga login berish"):
                        if w_log and w_pas:
                            try:
                                execute_query("INSERT INTO users (username, password, role, project_id) VALUES (?, ?, 'usta', ?)", (w_log, w_pas, active_p_id))
                                st.success("Muvaffaqiyatli yaratildi!")
                            except:
                                st.error("Bu login band!")

            # Berilgan foydalanuvchilar ro'yxati
            with st.expander("👥 Bu uyga biriktirilgan foydalanuvchilar ro'yxati"):
                u_chk = get_data("SELECT id, username AS 'Login', role AS 'Rol' FROM users WHERE project_id = ?", (active_p_id,))
                if not u_chk.empty:
                    u_chk.index = range(1, len(u_chk) + 1)
                    st.dataframe(u_chk, use_container_width=True)
                    u_del_id = st.number_input("O'chiriladigan User ID si:", min_value=1, step=1)
                    if st.button("Foydalanuvchini o'chirish"):
                        execute_query("DELETE FROM users WHERE id = ?", (u_del_id,))
                        st.success("O'chirildi!")
                        st.rerun()
                else:
                    st.info("Hozircha foydalanuvchilar yo'q.")
        else:
            st.warning("Hali uylar qo'shilmagan. Chap menyudan uy qo'shing.")

    # ---------------------------------------------------------
    # B) UY EGASI PANELI
    # ---------------------------------------------------------
    elif role == 'uy_egasi':
        p_id = user['project_id']
        p_info = get_data("SELECT project_name FROM projects WHERE id = ?", (p_id,))
        p_title = p_info.iloc[0]['project_name'] if not p_info.empty else "Uyingiz"
        
        st.title(f"🏡 {p_title} — Uy Egasi Paneli")
        st.info("Bu yerda uyingizning smetasi va o'zingiz bergan pullar tarixi ko'rsatilgan.")
        
        t1, t2 = st.tabs(["📊 Uy Smetasi", "💰 Men Bergan Pullar"])
        
        with t1:
            st.subheader("Bajarilayotgan Ishlar va Narxlar")
            df_ow = get_data("SELECT job_name, unit, quantity, price_per_unit, total_price FROM owner_works WHERE project_id = ?", (p_id,))
            if not df_ow.empty:
                df_ow.columns = ["Ish nomi", "Birlik", "Hajmi", "1 Birlik narxi", "Jami qiymat"]
                df_ow.index = range(1, len(df_ow) + 1)
                st.dataframe(df_ow, use_container_width=True)
                st.metric("Uyingizning Umumiy Summasi:", f"{df_ow['Jami qiymat'].sum():,.2f}")
            else:
                st.info("Hozircha smeta kiritilmagan.")
                
        with t2:
            st.subheader("Prorabga Bergan Pullaringiz")
            df_op = get_data("SELECT date, amount, note FROM owner_payments WHERE project_id = ?", (p_id,))
            if not df_op.empty:
                df_op.columns = ["Sana", "Berilgan summa", "Izoh"]
                df_op.index = range(1, len(df_op) + 1)
                st.dataframe(df_op, use_container_width=True)
                given = df_op['Berilgan summa'].sum()
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
        p_title = p_info.iloc[0]['project_name'] if not p_info.empty else "Ob'ekt"
        
        st.title(f"👷 {p_title} — Usta Paneli")
        st.info("Bu yerda ob'ektdagi ish hajmlari va sizga berilgan ish haqi ko'rsatilgan.")
        
        t1, t2 = st.tabs(["📋 Bajariladigan Ish Hajmi", "💵 Olingan Ish Haqlari"])
        
        with t1:
            st.subheader("Ishlar va Ish Haqlari Hajmi")
            df_ww = get_data("SELECT job_name, unit, quantity, price_per_unit, total_price FROM worker_works WHERE project_id = ?", (p_id,))
            if not df_ww.empty:
                df_ww.columns = ["Ish nomi", "Birlik", "Hajmi", "1 Birlik ish haqi", "Jami ish haqi"]
                df_ww.index = range(1, len(df_ww) + 1)
                st.dataframe(df_ww, use_container_width=True)
                st.metric("Sizning umumiy ish haqigingiz:", f"{df_ww['Jami ish haqi'].sum():,.2f}")
            else:
                st.info("Hozircha ishlar kiritilmagan.")
                
        with t2:
            st.subheader("Sizga Berilgan Pullar Tarixi")
            df_wp = get_data("SELECT worker_name, date, amount, note FROM worker_payments WHERE project_id = ?", (p_id,))
            if not df_wp.empty:
                df_wp.columns = ["Usta nomi", "Sana", "Olingan summa", "Izoh"]
                df_wp.index = range(1, len(df_wp) + 1)
                st.dataframe(df_wp, use_container_width=True)
                st.metric("Siz olgan jami pul:", f"{df_wp['Olingan summa'].sum():,.2f}")
            else:
                st.info("Sizga hali pul berilmagan.")

    st.markdown("---")
    st.markdown("<div class='footer-brand'>👷‍♂️ Prorab: Abdulla — Qurilish Boshqaruvi Tizimi</div>", unsafe_allow_html=True)
