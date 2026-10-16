import streamlit as st
import pandas as pd
import sqlite3
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io

# Sahifa sozlamalari
st.set_page_config(page_title="Qurilish Obyektlarini Boshqarish Tizimi", layout="wide")

# Ma'lumotlar bazasini yaratish
def init_db():
    conn = sqlite3.connect("construction_multi.db")
    c = conn.cursor()
    
    # Obyektlar (Uylar) jadvali
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT,
                    owner_code TEXT,
                    worker_code TEXT
                )''')
    
    # Smeta (Har bir obyekt ID raqamiga bog'langan)
    c.execute('''CREATE TABLE IF NOT EXISTS works (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    job_name TEXT,
                    unit TEXT,
                    quantity REAL,
                    price_per_unit REAL,
                    total_price REAL
                )''')
    
    # Uy egasining to'lovlari
    c.execute('''CREATE TABLE IF NOT EXISTS owner_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    date TEXT,
                    amount REAL,
                    note TEXT
                )''')
    
    # Ustalarga berilgan pullar
    c.execute('''CREATE TABLE IF NOT EXISTS worker_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    worker_name TEXT,
                    date TEXT,
                    amount REAL,
                    note TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

def get_data(query, params=()):
    conn = sqlite3.connect("construction_multi.db")
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute_query(query, params=()):
    conn = sqlite3.connect("construction_multi.db")
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

# Yon panel: Avtorizatsiya va Obyektni tanlash
st.sidebar.title("🔑 Tizimga Kirish")

projects_df = get_data("SELECT * FROM projects")

role = st.sidebar.radio("Rolingizni tanlang:", ["Prorab (To'liq huquq)", "Uy egasi / Usta (Faqat ko'rish)"])

is_admin = False
selected_project_id = None

if role == "Prorab (To'liq huquq)":
    prorab_password = st.sidebar.text_input("Prorab parolini kiriting:", type="password")
    
    # 📌 Prorab parolini shu yerdan o'zgartirishingiz mumkin
    PRORAB_PAROL = "Ab0534443"
    
    if prorab_password == PRORAB_PAROL:
        st.sidebar.success("Xush kelibsiz, Prorab!")
        is_admin = True
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("🏠 Obyektlarni Boshqarish")
        
        with st.sidebar.expander("➕ Yangi uy qo'shish"):
            new_p_name = st.text_input("Uy nomi (Masalan: 1-uy - Alisher akasiniki)")
            new_o_code = st.text_input("Uy egasi uchun maxsus parol")
            new_w_code = st.text_input("Ustalar uchun maxsus parol")
            if st.button("Obyektni yaratish"):
                if new_p_name:
                    execute_query("INSERT INTO projects (project_name, owner_code, worker_code) VALUES (?, ?, ?)",
                                  (new_p_name, new_o_code, new_w_code))
                    st.sidebar.success("Yangi uy muvaffaqiyatli qo'shildi!")
                    st.rerun()
        
        if not projects_df.empty:
            project_dict = {row['project_name']: row['id'] for _, row in projects_df.iterrows()}
            selected_p_name = st.sidebar.selectbox("Ishlayotgan uyni tanlang:", list(project_dict.keys()))
            selected_project_id = project_dict[selected_p_name]
        else:
            st.sidebar.warning("Hozircha obyektlar yo'q. Avval uy qo'shing!")
            
    else:
        st.sidebar.error("Parol noto'g'ri!")

else:
    # Uy egasi yoki usta rejimi
    if not projects_df.empty:
        project_dict = {row['project_name']: row['id'] for _, row in projects_df.iterrows()}
        selected_p_name = st.sidebar.selectbox("O'z uyingizni tanlang:", list(project_dict.keys()))
        selected_project_id = project_dict[selected_p_name]
        
        entered_code = st.sidebar.text_input("Shaxsiy kirish parolingizni kiriting:", type="password")
        
        curr_project = projects_df[projects_df['id'] == selected_project_id].iloc[0]
        if entered_code and (entered_code == curr_project['owner_code'] or entered_code == curr_project['worker_code']):
            st.sidebar.success("Ruxsat berildi (Faqat ko'rish rejimi)")
            is_admin = False
        else:
            if entered_code:
                st.sidebar.error("Parol xato!")
            selected_project_id = None
    else:
        st.sidebar.info("Hozircha obyektlar mavjud emas.")

# Asosiy oyna
st.title("🏗️ Noldan Topshirishgacha Qurilish Hisobi")

if selected_project_id is not None:
    current_project_name = projects_df[projects_df['id'] == selected_project_id]['project_name'].values[0]
    st.subheader(f"📁 Tanlangan obyekt: {current_project_name}")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Bosh Smeta (Ishlar)", "💰 Uy Egasining To'lovlari", "👷 Ustalar Hisobi", "📄 PDF Hisobot"])
    
    # --- 1-BO'LIM: SMETA ---
    with tab1:
        st.header("1. Ish Hajmlari va Qiymati")
        
        if is_admin:
            with st.expander("➕ Yangi ish qo'shish"):
                with st.form("add_work"):
                    job_name = st.text_input("Ish nomi (Masalan: G'isht terish, Suvoq)")
                    unit = st.selectbox("Birlik", ["kv.m", "kub.m", "metr", "dona", "komplekt"])
                    quantity = st.number_input("Hajmi", min_value=0.0, step=0.1)
                    price = st.number_input("1 birlik narxi", min_value=0.0, step=1000.0)
                    submit = st.form_submit_button("Qo'shish")
                    
                    if submit and job_name:
                        total = quantity * price
                        execute_query("INSERT INTO works (project_id, job_name, unit, quantity, price_per_unit, total_price) VALUES (?, ?, ?, ?, ?, ?)",
                                      (selected_project_id, job_name, unit, quantity, price, total))
                        st.success("Ish qo'shildi!")
                        st.rerun()

        df_works = get_data("SELECT * FROM works WHERE project_id = ?", (selected_project_id,))
        if not df_works.empty:
            st.dataframe(df_works, use_container_width=True)
            
            if is_admin:
                with st.expander("🗑️ Ishni o'chirish"):
                    w_del_id = st.number_input("O'chiriladigan ish ID raqami:", min_value=1, step=1, key="del_w")
                    if st.button("O'chirish"):
                        execute_query("DELETE FROM works WHERE id = ? AND project_id = ?", (w_del_id, selected_project_id))
                        st.success("O'chirildi!")
                        st.rerun()

            total_cost = df_works["total_price"].sum()
            st.metric(label="Umumiy Obyekt Qiymati:", value=f"{total_cost:,.2f}")
        else:
            st.info("Bu obyekt uchun hali ishlar kiritilmagan.")

    # --- 2-BO'LIM: UY EGASI TO'LOVLARI ---
    with tab2:
        st.header("2. Uy Egasidan Olingan Mablag'lar")
        
        if is_admin:
            with st.expander("➕ To'lovni kiritish"):
                with st.form("add_op"):
                    p_date = st.date_input("Sana")
                    p_amount = st.number_input("Summa", min_value=0.0, step=10000.0)
                    p_note = st.text_input("Izoh (Masalan: Material uchun avans)")
                    sub_op = st.form_submit_button("Saqlash")
                    
                    if sub_op and p_amount > 0:
                        execute_query("INSERT INTO owner_payments (project_id, date, amount, note) VALUES (?, ?, ?, ?)",
                                      (selected_project_id, str(p_date), p_amount, p_note))
                        st.success("Saqlandi!")
                        st.rerun()

        df_owner = get_data("SELECT * FROM owner_payments WHERE project_id = ?", (selected_project_id,))
        if not df_owner.empty:
            st.dataframe(df_owner, use_container_width=True)
            
            if is_admin:
                with st.expander("🗑️ To'lovni o'chirish"):
                    op_del_id = st.number_input("O'chiriladigan to'lov ID raqami:", min_value=1, step=1, key="del_op")
                    if st.button("To'lovni o'chirish"):
                        execute_query("DELETE FROM owner_payments WHERE id = ? AND project_id = ?", (op_del_id, selected_project_id))
                        st.success("O'chirildi!")
                        st.rerun()

            total_given = df_owner["amount"].sum()
            df_w_cost = get_data("SELECT SUM(total_price) as sum FROM works WHERE project_id = ?", (selected_project_id,))
            total_cost = df_w_cost['sum'].iloc[0] if not df_w_cost.empty and df_w_cost['sum'].iloc[0] is not None else 0
            rem_balance = total_cost - total_given
            
            col1, col2 = st.columns(2)
            col1.metric("Uy egasi bergan jami pul:", f"{total_given:,.2f}")
            col2.metric("Qolgan qarzdorlik:", f"{rem_balance:,.2f}")
        else:
            st.info("To'lovlar tarixi mavjud emas.")

    # --- 3-BO'LIM: USTALAR HISOBI ---
    with tab3:
        st.header("3. Ustalar va Berilgan Ish Haqlari")
        
        if is_admin:
            with st.expander("➕ Ustaga berilgan pulni yozish"):
                with st.form("add_wp"):
                    w_name = st.text_input("Usta / Brigada nomi (Masalan: Baxtiyor usta)")
                    w_date = st.date_input("Sana")
                    w_amount = st.number_input("Berilgan summa", min_value=0.0, step=5000.0)
                    w_note = st.text_input("Izoh")
                    sub_wp = st.form_submit_button("Saqlash")
                    
                    if sub_wp and w_name and w_amount > 0:
                        execute_query("INSERT INTO worker_payments (project_id, worker_name, date, amount, note) VALUES (?, ?, ?, ?, ?)",
                                      (selected_project_id, w_name, str(w_date), w_amount, w_note))
                        st.success("Saqlandi!")
                        st.rerun()

        df_worker = get_data("SELECT * FROM worker_payments WHERE project_id = ?", (selected_project_id,))
        if not df_worker.empty:
            st.dataframe(df_worker, use_container_width=True)
            
            if is_admin:
                with st.expander("🗑️ Ustaga to'lovni o'chirish"):
                    wp_del_id = st.number_input("O'chiriladigan to'lov ID raqami:", min_value=1, step=1, key="del_wp")
                    if st.button("Ustaning to'lovini o'chirish"):
                        execute_query("DELETE FROM worker_payments WHERE id = ? AND project_id = ?", (wp_del_id, selected_project_id))
                        st.success("O'chirildi!")
                        st.rerun()

            st.metric("Ustalarga berilgan jami pul:", f"{df_worker['amount'].sum():,.2f}")
        else:
            st.info("Ustalar to'lovlari qayd etilmagan.")

    # --- 4-BO'LIM: PDF HISOBOT ---
    with tab4:
        st.header("4. PDF Hisobotni Yuklab Olish")
        
        def generate_pdf():
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            
            title = Paragraph(f"<b>Obyekt hisoboti: {current_project_name}</b>", styles['Title'])
            elements.append(title)
            elements.append(Spacer(1, 12))
            
            works = get_data("SELECT job_name, unit, quantity, price_per_unit, total_price FROM works WHERE project_id = ?", (selected_project_id,))
            if not works.empty:
                data = [["Ish nomi", "Birlik", "Hajm", "Narx", "Jami"]]
                for _, row in works.iterrows():
                    data.append([str(row['job_name']), str(row['unit']), str(row['quantity']), str(row['price_per_unit']), str(row['total_price'])])
                
                t = Table(data)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.grey),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0,0), (-1,0), 12),
                    ('GRID', (0,0), (-1,-1), 1, colors.black)
                ]))
                elements.append(t)
            
            doc.build(elements)
            buffer.seek(0)
            return buffer

        pdf_data = generate_pdf()
        st.download_button(
            label="📥 PDF Hisobotni Yuklab Olish",
            data=pdf_data,
            file_name=f"hisobot_{selected_project_id}.pdf",
            mime="application/pdf"
        )
else:
    st.warning("Iltimos, chap tarafdagi menyudan uyni tanlang yoki maxsus parolni kiriting.")
