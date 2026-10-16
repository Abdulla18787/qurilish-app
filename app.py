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

st.markdown("""
    <style>
    .login-header { text-align: center; color: #1E88E5; font-weight: bold; }
    .footer-brand { text-align: center; margin-top: 30px; font-size: 16px; color: #757575; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# Baza yaratish
def init_db():
    conn = sqlite3.connect("construction_pro.db")
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
    c.execute('''CREATE TABLE IF NOT EXISTS works (
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

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None

# =========================================================
# 1. LOGIN INTERFEYSI
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
            if st.form_submit_button("Kirish 🚀"):
                user_data = get_data("SELECT * FROM users WHERE username = ? AND password = ?", (input_user, input_pass))
                if not user_data.empty:
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = user_data.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Login yoki parol xato!")
        st.markdown("<div class='footer-brand'>👷‍♂️ Prorab: Abdulla</div>", unsafe_allow_html=True)

# =========================================================
# 2. ASOSIY TIZIM INTERFEYSI
# =========================================================
else:
    user = st.session_state['user_info']
    role = user['role']
    
    st.sidebar.title(f"👤 {user['username'].capitalize()}")
    st.sidebar.caption(f"Sizning rolingiz: {role.upper()}")
    if st.sidebar.button("🚪 Tizimdan chiqish"):
        st.session_state['logged_in'] = False
        st.session_state['user_info'] = None
        st.rerun()
    st.sidebar.markdown("---")

    # ---------------------------------------------------------
    # A) PRORAB ABDULLA NOGOROHI
    # ---------------------------------------------------------
    if role == 'admin':
        st.sidebar.subheader("⚙️ Prorab Boshqaruvi")
        
        # 1. Uy qo'shish / o'chirish
        with st.sidebar.expander("🏠 Uylar ro'yxati"):
            new_p_name = st.text_input("Yangi uy nomi:")
            if st.button("Uy qo'shish"):
                if new_p_name:
                    execute_query("INSERT INTO projects (project_name) VALUES (?)", (new_p_name,))
                    st.success("Uy qo'shildi!")
                    st.rerun()
            projects_list = get_data("SELECT * FROM projects")
            if not projects_list.empty:
                del_p_id = st.selectbox("O'chirmoqchi bo'lgan uyni tanlang:", projects_list['id'].tolist(), format_func=lambda x: projects_list[projects_list['id']==x]['project_name'].values[0])
                if st.button("Uyni o'chirish 🗑️"):
                    execute_query("DELETE FROM projects WHERE id = ?", (del_p_id,))
                    execute_query("DELETE FROM users WHERE project_id = ?", (del_p_id,))
                    st.rerun()

        # 2. Login/Parol berish
        with st.sidebar.expander("🔑 Uy egasi va Usta uchun Login/Parol"):
            projects_list = get_data("SELECT * FROM projects")
            if not projects_list.empty:
                u_type = st.selectbox("Kim uchun login ochasiz?", ["uy_egasi", "usta"])
                u_project = st.selectbox("Qaysi uyga biriktirasiz?", projects_list['id'].tolist(), format_func=lambda x: projects_list[projects_list['id']==x]['project_name'].values[0])
                u_login = st.text_input("Login yaratish:")
                u_pass = st.text_input("Parol yaratish:")
                if st.button("Saqlash va Berish"):
                    if u_login and u_pass:
                        try:
                            execute_query("INSERT INTO users (username, password, role, project_id) VALUES (?, ?, ?, ?)", (u_login, u_pass, u_type, u_project))
                            st.success("Muvaffaqiyatli saqlandi!")
                            st.rerun()
                        except:
                            st.error("Bu login allaqachon bor!")

        # 3. Foydalanuvchilar ro'yxati
        with st.sidebar.expander("👥 Berilgan Login/Parollar"):
            users_df = get_data("SELECT id, username AS 'Login', password AS 'Parol', role AS 'Rol' FROM users WHERE role != 'admin'")
            users_df.index = range(1, len(users_df) + 1)
            st.dataframe(users_df, use_container_width=True)
            if not users_df.empty:
                del_user_id = st.number_input("O'chiriladigan User ID:", min_value=1, step=1)
                if st.button("O'chirish"):
                    execute_query("DELETE FROM users WHERE id = ?", (del_user_id,))
                    st.rerun()

        # Prorab uchun Obyektni tanlash
        all_projects = get_data("SELECT * FROM projects")
        if not all_projects.empty:
            proj_dict = {row['project_name']: row['id'] for _, row in all_projects.iterrows()}
            selected_proj_name = st.selectbox("📂 Qaysi uyni tekshirasiz/yozasiz?", list(proj_dict.keys()))
            active_project_id = proj_dict[selected_proj_name]
            
            p_name = selected_proj_name
            st.title(f"🏠 Obyekt: {p_name}")
            st.caption("Prorab Abdulla boshqaruv paneli")

            t1, t2, t3, t4 = st.tabs(["📊 Smeta (Ishlar)", "💰 Uy Egasidan Olingan Pullar", "👷 Ustalarga Berilgan Pullar", "📄 PDF Hisobot"])
            
            # 1. Smeta
            with t1:
                st.subheader("Bosh Smeta")
                with st.expander("➕ Yangi ish qo'shish"):
                    with st.form("w_form"):
                        jn = st.text_input("Ish nomi (Masalan: G'isht terish)")
                        un = st.selectbox("Birlik", ["kv.m", "kub.m", "metr", "dona", "komplekt"])
                        qty = st.number_input("Hajmi", min_value=0.0, step=0.1)
                        pr = st.number_input("1 Birlik narxi", min_value=0.0, step=1000.0)
                        if st.form_submit_button("Qo'shish") and jn:
                            execute_query("INSERT INTO works (project_id, job_name, unit, quantity, price_per_unit, total_price) VALUES (?, ?, ?, ?, ?, ?)", (active_project_id, jn, un, qty, pr, qty*pr))
                            st.rerun()
                
                raw_w = get_data("SELECT id, job_name, unit, quantity, price_per_unit, total_price FROM works WHERE project_id = ?", (active_project_id,))
                if not raw_w.empty:
                    display_w = raw_w[['job_name', 'unit', 'quantity', 'price_per_unit', 'total_price']].copy()
                    display_w.columns = ["Ish nomi", "O'lchov birligi", "Hajmi", "1 Birlik narxi", "Jami qiymati"]
                    display_w.index = range(1, len(display_w) + 1)
                    st.dataframe(display_w, use_container_width=True)
                    
                    with st.expander("🗑️ Qatorni o'chirish"):
                        row_to_del = st.number_input("O'chirmoqchi bo'lgan qator raqamini kiriting (1, 2, 3...):", min_value=1, max_value=len(raw_w), step=1)
                        if st.button("Ishni o'chirish"):
                            target_db_id = raw_w.iloc[row_to_del - 1]['id']
                            execute_query("DELETE FROM works WHERE id = ?", (target_db_id,))
                            st.success("O'chirildi!")
                            st.rerun()
                    st.metric("Obyektning umumiy qiymati:", f"{raw_w['total_price'].sum():,.2f}")
                else:
                    st.info("Hozircha smetaga ishlar kiritilmagan.")

            # 2. Uy Egasi Pullari
            with t2:
                st.subheader("Uy Egasidan Olingan Pullar")
                with st.expander("➕ Pul olishni yozish"):
                    with st.form("op_form"):
                        dt = st.date_input("Sana")
                        am = st.number_input("Olingan summa", min_value=0.0, step=10000.0)
                        nt = st.text_input("Izoh")
                        if st.form_submit_button("Saqlash") and am > 0:
                            execute_query("INSERT INTO owner_payments (project_id, date, amount, note) VALUES (?, ?, ?, ?)", (active_project_id, str(dt), am, nt))
                            st.rerun()
                
                raw_op = get_data("SELECT id, date, amount, note FROM owner_payments WHERE project_id = ?", (active_project_id,))
                if not raw_op.empty:
                    display_op = raw_op[['date', 'amount', 'note']].copy()
                    display_op.columns = ["Sana", "Olingan summa", "Izoh"]
                    display_op.index = range(1, len(display_op) + 1)
                    st.dataframe(display_op, use_container_width=True)
                    
                    with st.expander("🗑️ To'lovni o'chirish"):
                        op_row_del = st.number_input("O'chiriladigan to'lov qatori raqami (1, 2, 3...):", min_value=1, max_value=len(raw_op), step=1, key="op_del_k")
                        if st.button("To'lovni o'chirish"):
                            target_op_id = raw_op.iloc[op_row_del - 1]['id']
                            execute_query("DELETE FROM owner_payments WHERE id = ?", (target_op_id,))
                            st.success("O'chirildi!")
                            st.rerun()
                    st.metric("Uy egasidan olingan jami pul:", f"{raw_op['amount'].sum():,.2f}")
                else:
                    st.info("To'lovlar kiritilmagan.")

            # 3. Ustalar Pullari
            with t3:
                st.subheader("Ustalarga Berilgan Ish Haqlari")
                with st.expander("➕ Ustaga pul berish"):
                    with st.form("wp_form"):
                        wn = st.text_input("Usta / Brigada nomi")
                        dt = st.date_input("Sana")
                        am = st.number_input("Berilgan summa", min_value=0.0, step=5000.0)
                        nt = st.text_input("Izoh")
                        if st.form_submit_button("Saqlash") and am > 0:
                            execute_query("INSERT INTO worker_payments (project_id, worker_name, date, amount, note) VALUES (?, ?, ?, ?, ?)", (active_project_id, wn, str(dt), am, nt))
                            st.rerun()
                
                raw_wp = get_data("SELECT id, worker_name, date, amount, note FROM worker_payments WHERE project_id = ?", (active_project_id,))
                if not raw_wp.empty:
                    display_wp = raw_wp[['worker_name', 'date', 'amount', 'note']].copy()
                    display_wp.columns = ["Usta nomi", "Sana", "Berilgan summa", "Izoh"]
                    display_wp.index = range(1, len(display_wp) + 1)
                    st.dataframe(display_wp, use_container_width=True)
                    
                    with st.expander("🗑️ Ustaning to'lovini o'chirish"):
                        wp_row_del = st.number_input("O'chiriladigan qator raqami (1, 2, 3...):", min_value=1, max_value=len(raw_wp), step=1, key="wp_del_k")
                        if st.button("Ustaning to'lovini o'chirish"):
                            target_wp_id = raw_wp.iloc[wp_row_del - 1]['id']
                            execute_query("DELETE FROM worker_payments WHERE id = ?", (target_wp_id,))
                            st.success("O'chirildi!")
                            st.rerun()
                    st.metric("Ustalarga berilgan jami pul:", f"{raw_wp['amount'].sum():,.2f}")
                else:
                    st.info("Ustalar to'lovi kiritilmagan.")

            # 4. PDF
            with t4:
                st.subheader("PDF Hisobot Yaratish")
                def generate_pdf():
                    buffer = io.BytesIO()
                    doc = SimpleDocTemplate(buffer, pagesize=A4)
                    elements = []
                    styles = getSampleStyleSheet()
                    elements.append(Paragraph(f"<b>Obyekt Hisoboti: {p_name}</b>", styles['Title']))
                    elements.append(Paragraph("<b>Prorab: Abdulla</b>", styles['Normal']))
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
                st.download_button("📥 PDF Hisobotni Yuklab Olish", generate_pdf(), file_name=f"{p_name}_hisobot.pdf", mime="application/pdf")

        else:
            st.warning("Hali hech qanday uy qo'shilmagan! Chap menyudan uy qo'shing.")

    # ---------------------------------------------------------
    # B) UY EGASI OYNASI
    # ---------------------------------------------------------
    elif role == 'uy_egasi':
        active_project_id = user['project_id']
        proj_info = get_data("SELECT project_name FROM projects WHERE id = ?", (active_project_id,))
        p_name = proj_info.iloc[0]['project_name'] if not proj_info.empty else "Sizning uyingiz"
        
        st.title(f"🏡 {p_name} — Uy Egasi Paneli")
        st.info("Xush kelibsiz! Bu yerda uyingizning smetasi va siz bergan pullar tarixi ko'rsatilgan.")
        
        t1, t2 = st.tabs(["📊 Uy Smeta Hisobi", "💰 Men Bergan Pullar"])
        
        with t1:
            st.subheader("Bajarilayotgan Ishlar va Narxlar")
            raw_w = get_data("SELECT job_name, unit, quantity, price_per_unit, total_price FROM works WHERE project_id = ?", (active_project_id,))
            if not raw_w.empty:
                raw_w.columns = ["Ish nomi", "O'lchov birligi", "Hajmi", "1 Birlik narxi", "Jami qiymati"]
                raw_w.index = range(1, len(raw_w) + 1)
                st.dataframe(raw_w, use_container_width=True)
                st.metric("Uyingizning Umumiy Qurilish Summasi:", f"{raw_w['Jami qiymati'].sum():,.2f}")
            else:
                st.info("Hozircha smeta kiritilmagan.")
                
        with t2:
            st.subheader("Prorabga Bergan Pullaringiz Tarixi")
            raw_op = get_data("SELECT date, amount, note FROM owner_payments WHERE project_id = ?", (active_project_id,))
            if not raw_op.empty:
                raw_op.columns = ["Sana", "Berilgan summa", "Izoh"]
                raw_op.index = range(1, len(raw_op) + 1)
                st.dataframe(raw_op, use_container_width=True)
                given = raw_op['Berilgan summa'].sum()
                w_df_all = get_data("SELECT total_price FROM works WHERE project_id = ?", (active_project_id,))
                tot = w_df_all['total_price'].sum() if not w_df_all.empty else 0
                col1, col2 = st.columns(2)
                col1.metric("Siz bergan jami pul:", f"{given:,.2f}")
                col2.metric("Qolgan qarzdorlik:", f"{tot - given:,.2f}")
            else:
                st.info("To'lovlar tarixi yo'q.")

    # ---------------------------------------------------------
    # C) USTA OYNASI
    # ---------------------------------------------------------
    elif role == 'usta':
        active_project_id = user['project_id']
        proj_info = get_data("SELECT project_name FROM projects WHERE id = ?", (active_project_id,))
        p_name = proj_info.iloc[0]['project_name'] if not proj_info.empty else "Ob'ekt"
        
        st.title(f"👷 {p_name} — Usta Paneli")
        st.info("Xush kelibsiz! Bu yerda ob'ektdagi ish hajmlari va sizga berilgan ish haqi ko'rsatilgan.")
        
        t1, t2 = st.tabs(["📋 Bajariladigan Ishlar Hajmi", "💵 Olingan Ish Haqlari Tarixi"])
        
        with t1:
            st.subheader("Ob'ektdagi Ishlar Hajmi ($m^2, m^3, m$)")
            raw_w = get_data("SELECT job_name, unit, quantity FROM works WHERE project_id = ?", (active_project_id,))
            if not raw_w.empty:
                raw_w.columns = ["Ish nomi", "O'lchov birligi", "Hajmi"]
                raw_w.index = range(1, len(raw_w) + 1)
                st.dataframe(raw_w, use_container_width=True)
            else:
                st.info("Hozircha ishlar ro'yxati yo'q.")
                
        with t2:
            st.subheader("Sizga Berilgan Ish Haqlari Tarixi")
            raw_wp = get_data("SELECT worker_name, date, amount, note FROM worker_payments WHERE project_id = ?", (active_project_id,))
            if not raw_wp.empty:
                raw_wp.columns = ["Usta nomi", "Sana", "Olingan summa", "Izoh"]
                raw_wp.index = range(1, len(raw_wp) + 1)
                st.dataframe(raw_wp, use_container_width=True)
                st.metric("Sizga berilgan jami pul:", f"{raw_wp['Olingan summa'].sum():,.2f}")
            else:
                st.info("Sizga hali pul berilmagan.")

    st.markdown("---")
    st.markdown("<div class='footer-brand'>👷‍♂️ Prorab: Abdulla — Qurilish Boshqaruvi Tizimi</div>", unsafe_allow_html=True)
