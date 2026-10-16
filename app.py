import streamlit as st
import pandas as pd
import sqlite3
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io

# Sahifa sozlamalari
st.set_page_config(page_title="Qurilish Nazorati | Prorab Abdulla", layout="wide", initial_sidebar_state="collapsed")

# CSS Stillar - Login oynasini chiroyli markazlashtirish uchun
st.markdown("""
    <style>
    .login-header {
        text-align: center;
        color: #1E88E5;
        font-weight: bold;
    }
    .footer-brand {
        text-align: center;
        margin-top: 30px;
        font-size: 16px;
        color: #757575;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Ma'lumotlar bazasini sozlash (SQLite)
def init_db():
    conn = sqlite3.connect("construction_pro.db")
    c = conn.cursor()
    
    # Foydalanuvchilar jadvali (Prorab, Uy egasi, Usta)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    role TEXT,
                    project_id INTEGER
                )''')
    
    # Obyektlar (Proyektlar) jadvali
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT,
                    description TEXT
                )''')
    
    # Smeta (Ishlar jadvali)
    c.execute('''CREATE TABLE IF NOT EXISTS works (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    job_name TEXT,
                    unit TEXT,
                    quantity REAL,
                    price_per_unit REAL,
                    total_price REAL
                )''')
    
    # Uy egasi to'lovlari
    c.execute('''CREATE TABLE IF NOT EXISTS owner_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    date TEXT,
                    amount REAL,
                    note TEXT
                )''')
    
    # Ustalar to'lovlari
    c.execute('''CREATE TABLE IF NOT EXISTS worker_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    worker_name TEXT,
                    date TEXT,
                    amount REAL,
                    note TEXT
                )''')
    
    # Odatiy Prorab (Abdulla) hisobini yaratish (agar mavjud bo'lmasa)
    c.execute("SELECT * FROM users WHERE username = 'abdulla'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role, project_id) VALUES ('abdulla', '1234', 'admin', NULL)")
        
    conn.commit()
    conn.close()

init_db()

def get_data(query, params=()):
    conn = sqlite3.connect("construction_pro.db")
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute_query(query, params=()):
    conn = sqlite3.connect("construction_pro.db")
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

# Session State (Tizimda avtorizatsiyani saqlash)
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None

# =========================================================
# 1. LOGIN INTERFEYSI (Kichik, ixcham oyna)
# =========================================================
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h2 class='login-header'>🏗️ Qurilish Nazorat Tizimi</h2>", unsafe_allow_html=True)
        st.write(" ")
        
        with st.form("login_form"):
            st.subheader("Tizimga kirish")
            input_user = st.text_input("Login")
            input_pass = st.text_input("Parol", type="password")
            btn_login = st.form_submit_button("Kirish 🚀")
            
            if btn_login:
                user_data = get_data("SELECT * FROM users WHERE username = ? AND password = ?", (input_user, input_pass))
                if not user_data.empty:
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = user_data.iloc[0].to_dict()
                    st.success("Tizimga kirdingiz!")
                    st.rerun()
                else:
                    st.error("Login yoki parol noto'g'ri!")
        
        # Tagida brending yozuvi
        st.markdown("<div class='footer-brand'>👷‍♂️ Prorab: Abdulla</div>", unsafe_allow_html=True)

# =========================================================
# 2. ASOSIY TIZIM INTERFEYSI (Login bo'lgandan so'ng)
# =========================================================
else:
    user = st.session_state['user_info']
    is_admin = (user['role'] == 'admin')
    
    # Yon panel (Sidebar)
    st.sidebar.title(f"👤 {user['username'].capitalize()}")
    st.sidebar.caption(f"Rol: {'Prorab (Abdulla)' if is_admin else user['role'].capitalize()}")
    
    if st.sidebar.button("🚪 Tizimdan chiqish"):
        st.session_state['logged_in'] = False
        st.session_state['user_info'] = None
        st.rerun()
        
    st.sidebar.markdown("---")
    
    # Prorab uchun foydalanuvchilar va proyektlarni boshqarish paneli
    if is_admin:
        st.sidebar.subheader("⚙️ Prorab Boshqaruvi")
        
        # 1. Proyekt yaratish / o'chirish
        with st.sidebar.expander("🏠 Proyektlar (Uylar)"):
            new_p_name = st.text_input("Yangi uy nomi:")
            if st.button("Uy qo'shish"):
                if new_p_name:
                    execute_query("INSERT INTO projects (project_name) VALUES (?)", (new_p_name,))
                    st.success("Uy qo'shildi!")
                    st.rerun()
            
            projects_list = get_data("SELECT * FROM projects")
            if not projects_list.empty:
                del_p_id = st.selectbox("O'chirish uchun uyni tanlang:", projects_list['id'].tolist(), format_func=lambda x: projects_list[projects_list['id']==x]['project_name'].values[0])
                if st.button("Uyni o'chirish 🗑️"):
                    execute_query("DELETE FROM projects WHERE id = ?", (del_p_id,))
                    execute_query("DELETE FROM users WHERE project_id = ?", (del_p_id,))
                    st.success("Uy o'chirildi!")
                    st.rerun()

        # 2. Login va Parol yaratish (Uy egasi / Usta uchun)
        with st.sidebar.expander("🔑 Login va Parol berish"):
            if not projects_list.empty:
                u_type = st.selectbox("Foydalanuvchi turi:", ["uy_egasi", "usta"])
                u_project = st.selectbox("Qaysi uyga biriktirilsin:", projects_list['id'].tolist(), format_func=lambda x: projects_list[projects_list['id']==x]['project_name'].values[0])
                u_login = st.text_input("Yangi Login:")
                u_pass = st.text_input("Yangi Parol:")
                if st.button("Login yaratish"):
                    if u_login and u_pass:
                        try:
                            execute_query("INSERT INTO users (username, password, role, project_id) VALUES (?, ?, ?, ?)",
                                          (u_login, u_pass, u_type, u_project))
                            st.success("Foydalanuvchi yaratildi!")
                            st.rerun()
                        except:
                            st.error("Bu login allaqachon mavjud!")
            else:
                st.warning("Avval uy yarating!")

        # 3. Mavjud foydalanuvchilarni o'chirish / boshqarish
        with st.sidebar.expander("👥 Foydalanuvchilar ro'yxati"):
            users_df = get_data("SELECT id, username, password, role, project_id FROM users WHERE role != 'admin'")
            st.dataframe(users_df, use_container_width=True)
            if not users_df.empty:
                del_user_id = st.number_input("O'chirmoqchi bo'lgan user ID si:", min_value=1, step=1)
                if st.button("Foydalanuvchini o'chirish"):
                    execute_query("DELETE FROM users WHERE id = ?", (del_user_id,))
                    st.success("Foydalanuvchi o'chirildi!")
                    st.rerun()

    # Obyektni tanlash mantiqi
    if is_admin:
        all_projects = get_data("SELECT * FROM projects")
        if not all_projects.empty:
            proj_dict = {row['project_name']: row['id'] for _, row in all_projects.iterrows()}
            selected_proj_name = st.selectbox("📂 Ishlamoqchi bo'lgan obyektni tanlang:", list(proj_dict.keys()))
            active_project_id = proj_dict[selected_proj_name]
        else:
            st.warning("Hali hech qanday proyekt qo'shilmagan. Chap tarafdagi panel orqali yangi uy qo'shing.")
            active_project_id = None
    else:
        active_project_id = user['project_id']

    # Obyekt paneli
    if active_project_id:
        proj_info = get_data("SELECT project_name FROM projects WHERE id = ?", (active_project_id,))
        p_name = proj_info.iloc[0]['project_name'] if not proj_info.empty else "Obyekt"
        
        st.title(f"🏠 {p_name}")
        st.caption("Prorab: Abdulla | Smeta va Moliya Boshqaruvi")

        tab1, tab2, tab3, tab4 = st.tabs(["📊 Smeta (Ishlar)", "💰 Uy Egasining To'lovlari", "👷 Ustalar Hisobi", "📄 PDF Hisobot"])

        # --- TAB 1: SMETA ---
        with tab1:
            st.header("1. Ish Hajmlari va Narxlari")
            if is_admin:
                with st.expander("➕ Yangi ish qo'shish"):
                    with st.form("add_w"):
                        j_name = st.text_input("Ish nomi (masalan: G'isht terish)")
                        j_unit = st.selectbox("Birlik", ["kv.m", "kub.m", "metr", "dona", "komplekt"])
                        j_qty = st.number_input("Hajm", min_value=0.0, step=0.1)
                        j_price = st.number_input("Birlik narxi", min_value=0.0, step=1000.0)
                        if st.form_submit_button("Qo'shish") and j_name:
                            execute_query("INSERT INTO works (project_id, job_name, unit, quantity, price_per_unit, total_price) VALUES (?, ?, ?, ?, ?, ?)",
                                          (active_project_id, j_name, j_unit, j_qty, j_price, j_qty*j_price))
                            st.success("Ish qo'shildi!")
                            st.rerun()

            works_df = get_data("SELECT * FROM works WHERE project_id = ?", (active_project_id,))
            if not works_df.empty:
                st.dataframe(works_df, use_container_width=True)
                if is_admin:
                    with st.expander("🗑️ Ishni o'chirish"):
                        w_id = st.number_input("O'chiriladigan ish ID si:", min_value=1, step=1)
                        if st.button("Ishni o'chirish"):
                            execute_query("DELETE FROM works WHERE id = ?", (w_id,))
                            st.rerun()
                st.metric("Umumiy Obyekt Summasi:", f"{works_df['total_price'].sum():,.2f}")
            else:
                st.info("Smetaga ishlar kiritilmagan.")

        # --- TAB 2: UY EGASI ---
        with tab2:
            st.header("2. Uy Egasining To'lovlari")
            if is_admin:
                with st.expander("➕ To'lov qo'shish"):
                    with st.form("add_op"):
                        o_date = st.date_input("Sana")
                        o_amt = st.number_input("Summa", min_value=0.0, step=10000.0)
                        o_note = st.text_input("Izoh")
                        if st.form_submit_button("Saqlash") and o_amt > 0:
                            execute_query("INSERT INTO owner_payments (project_id, date, amount, note) VALUES (?, ?, ?, ?)",
                                          (active_project_id, str(o_date), o_amt, o_note))
                            st.rerun()

            owner_df = get_data("SELECT * FROM owner_payments WHERE project_id = ?", (active_project_id,))
            if not owner_df.empty:
                st.dataframe(owner_df, use_container_width=True)
                if is_admin:
                    with st.expander("🗑️ To'lovni o'chirish"):
                        op_id = st.number_input("O'chiriladigan to'lov ID si:", min_value=1, step=1)
                        if st.button("To'lovni o'chirish"):
                            execute_query("DELETE FROM owner_payments WHERE id = ?", (op_id,))
                            st.rerun()
                total_given = owner_df['amount'].sum()
                total_cost = works_df['total_price'].sum() if 'works_df' in locals() and not works_df.empty else 0
                col1, col2 = st.columns(2)
                col1.metric("Olingan jami pul:", f"{total_given:,.2f}")
                col2.metric("Qolgan qarzdorlik:", f"{total_cost - total_given:,.2f}")
            else:
                st.info("To'lovlar kiritilmagan.")

        # --- TAB 3: USTALAR ---
        with tab3:
            st.header("3. Ustalar Hisob-Kitobi")
            if is_admin:
                with st.expander("➕ Ustaga pul berish"):
                    with st.form("add_wp"):
                        w_name = st.text_input("Usta / Brigada nomi")
                        w_date = st.date_input("Sana")
                        w_amt = st.number_input("Summa", min_value=0.0, step=5000.0)
                        w_note = st.text_input("Izoh")
                        if st.form_submit_button("Saqlash") and w_amt > 0:
                            execute_query("INSERT INTO worker_payments (project_id, worker_name, date, amount, note) VALUES (?, ?, ?, ?, ?)",
                                          (active_project_id, w_name, str(w_date), w_amt, w_note))
                            st.rerun()

            worker_df = get_data("SELECT * FROM worker_payments WHERE project_id = ?", (active_project_id,))
            if not worker_df.empty:
                st.dataframe(worker_df, use_container_width=True)
                if is_admin:
                    with st.expander("🗑️ Ustaning to'lovini o'chirish"):
                        wp_id = st.number_input("To'lov ID si:", min_value=1, step=1)
                        if st.button("O'chirish"):
                            execute_query("DELETE FROM worker_payments WHERE id = ?", (wp_id,))
                            st.rerun()
                st.metric("Ustalarga berilgan jami pul:", f"{worker_df['amount'].sum():,.2f}")
            else:
                st.info("Ustalar to'lovi kiritilmagan.")

        # --- TAB 4: PDF ---
        with tab4:
            st.header("4. PDF Hisobot")
            def generate_pdf():
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4)
                elements = []
                styles = getSampleStyleSheet()
                elements.append(Paragraph(f"<b>Obyekt: {p_name}</b>", styles['Title']))
                elements.append(Paragraph("<b>Prorab: Abdulla</b>", styles['Subtitle']))
                elements.append(Spacer(1, 12))
                
                w_data = get_data("SELECT job_name, unit, quantity, price_per_unit, total_price FROM works WHERE project_id = ?", (active_project_id,))
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

            st.download_button("📥 PDF Yuklab Olish", generate_pdf(), file_name=f"{p_name}_hisobot.pdf", mime="application/pdf")

    # Pastki qismdagi brending
    st.markdown("---")
    st.markdown("<div class='footer-brand'>👷‍♂️ Prorab: Abdulla — Qurilish Boshqaruvi Tizimi</div>", unsafe_allow_html=True)
