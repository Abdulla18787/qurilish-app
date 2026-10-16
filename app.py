import streamlit as st
import pandas as pd
import sqlite3
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io

# Sahifa sozlamalari
st.set_page_config(page_title="Qurilish Smeta & Nazorat Tizimi", layout="wide")

# Ma'lumotlar bazasini sozlash (SQLite)
def init_db():
    conn = sqlite3.connect("construction.db")
    c = conn.cursor()
    # Ishlar jadvali (Smeta)
    c.execute('''CREATE TABLE IF NOT EXISTS works (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_name TEXT,
                    unit TEXT,
                    quantity REAL,
                    price_per_unit REAL,
                    total_price REAL
                )''')
    # Uy egasidan olingan to'lovlar
    c.execute('''CREATE TABLE IF NOT EXISTS owner_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    amount REAL,
                    note TEXT
                )''')
    # Ustalarga berilgan to'lovlar
    c.execute('''CREATE TABLE IF NOT EXISTS worker_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    worker_name TEXT,
                    date TEXT,
                    amount REAL,
                    note TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# Baza bilan ishlash funksiyalari
def get_data(table):
    conn = sqlite3.connect("construction.db")
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    conn.close()
    return df

def execute_query(query, params=()):
    conn = sqlite3.connect("construction.db")
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

# Yon panel (Sidebar) - Tizimga kirish
st.sidebar.title("🔑 Tizimga kirish")
role = st.sidebar.radio("Rolingizni tanlang:", ["Uy egasi / Usta (Faqat ko'rish)", "Prorab (Tahrirlash)"])

is_admin = False
if role == "Prorab (Tahrirlash)":
    password = st.sidebar.text_input("Prorab parolini kiriting:", type="password")
    
    # 📌 PAROLNI SHU YERDAN O'ZGARTIRISHINGIZ MUMKIN (Hozirgi parol: 1234)
    PRORAB_PAROL = "Ab0534443" 
    
    if password == PRORAB_PAROL:
        st.sidebar.success("Xush kelibsiz, Prorab!")
        is_admin = True
    else:
        st.sidebar.error("Parol noto'g'ri!")

st.title("🏗️ Noldan Topshirishgacha Qurilish Ob'ekti Hisobi")

# Tablar (Bo'limlar)
tab1, tab2, tab3, tab4 = st.tabs(["📊 Bosh Smeta (Ishlar)", "💰 Uy Egasining To'lovlari", "👷 Ustalar Hisobi", "📄 PDF Hisobot"])

# ---------------------------------------------------------
# TAB 1: SMETA
# ---------------------------------------------------------
with tab1:
    st.header("1. Ish Hajmlari va Qiymati (Smeta)")
    
    if is_admin:
        with st.expander("➕ Yangi ish turini qo'shish"):
            with st.form("add_work"):
                job_name = st.text_input("Ish nomi (Masalan: Gisht terish, Suvoq, Elektriklik)")
                unit = st.selectbox("O'lchov birligi", ["kv.m", "kub.m", "metr", "dona", "komplekt"])
                quantity = st.number_input("Hajmi (Nechchi kv/metr/kub)", min_value=0.0, step=0.1)
                price = st.number_input("1 birlik narxi (so'm yoki USD)", min_value=0.0, step=1000.0)
                submit = st.form_submit_button("Qo'shish")
                
                if submit and job_name:
                    total = quantity * price
                    execute_query("INSERT INTO works (job_name, unit, quantity, price_per_unit, total_price) VALUES (?, ?, ?, ?, ?)",
                                  (job_name, unit, quantity, price, total))
                    st.success("Ish muvaffaqiyatli qo'shildi!")
                    st.rerun()

    df_works = get_data("works")
    if not df_works.empty:
        st.dataframe(df_works, use_container_width=True)
        
        # O'chirish bo'limi (Prorab uchun)
        if is_admin:
            with st.expander("🗑️ Qatorni o'chirish"):
                work_id_to_delete = st.number_input("O'chirmoqchi bo'lgan ish ID raqamini kiriting:", min_value=1, step=1, key="del_work")
                if st.button("Ushbu ishni o'chirish"):
                    execute_query("DELETE FROM works WHERE id = ?", (work_id_to_delete,))
                    st.success(f"ID: {work_id_to_delete} bo'lgan ish o'chirildi!")
                    st.rerun()

        total_project_cost = df_works["total_price"].sum()
        st.metric(label="Umumiy Qurilish Qiymati:", value=f"{total_project_cost:,.2f}")
    else:
        st.info("Hozircha smetaga ishlar kiritilmagan.")

# ---------------------------------------------------------
# TAB 2: UY EGASI TO'LOVLARI
# ---------------------------------------------------------
with tab2:
    st.header("2. Uy Egasidan Olingan Pullar")
    
    if is_admin:
        with st.expander("➕ Pul qabul qilishni yozish"):
            with st.form("add_owner_pay"):
                p_date = st.date_input("Sana")
                p_amount = st.number_input("Olingan summa", min_value=0.0, step=10000.0)
                p_note = st.text_input("Izoh (Masalan: Material uchun, Avans)")
                submit_op = st.form_submit_button("Saqlash")
                
                if submit_op and p_amount > 0:
                    execute_query("INSERT INTO owner_payments (date, amount, note) VALUES (?, ?, ?)",
                                  (str(p_date), p_amount, p_note))
                    st.success("To'lov saqlandi!")
                    st.rerun()

    df_owner = get_data("owner_payments")
    if not df_owner.empty:
        st.dataframe(df_owner, use_container_width=True)
        
        # O'chirish bo'limi (Prorab uchun)
        if is_admin:
            with st.expander("🗑️ To'lovni o'chirish"):
                owner_pay_id = st.number_input("O'chirmoqchi bo'lgan to'lov ID raqamini kiriting:", min_value=1, step=1, key="del_owner")
                if st.button("To'lovni o'chirish"):
                    execute_query("DELETE FROM owner_payments WHERE id = ?", (owner_pay_id,))
                    st.success(f"ID: {owner_pay_id} bo'lgan to'lov o'chirildi!")
                    st.rerun()

        total_given = df_owner["amount"].sum()
        df_works = get_data("works")
        total_cost = df_works["total_price"].sum() if not df_works.empty else 0
        rem_balance = total_cost - total_given
        
        col1, col2 = st.columns(2)
        col1.metric("Uy egasi bergan jami pul:", f"{total_given:,.2f}")
        col2.metric("Qolgan qarzdorlik:", f"{rem_balance:,.2f}")
    else:
        st.info("To'lovlar tarixi mavjud emas.")

# ---------------------------------------------------------
# TAB 3: USTALAR HISOBI
# ---------------------------------------------------------
with tab3:
    st.header("3. Ustalar va Ularga Berilgan Pullar")
    
    if is_admin:
        with st.expander("➕ Ustaga pul berishni qayd etish"):
            with st.form("add_worker_pay"):
                w_name = st.text_input("Usta ismi (Masalan: Ali usta - Suvoqchi)")
                w_date = st.date_input("Sana")
                w_amount = st.number_input("Berilgan summa", min_value=0.0, step=5000.0)
                w_note = st.text_input("Izoh")
                submit_wp = st.form_submit_button("Saqlash")
                
                if submit_wp and w_name and w_amount > 0:
                    execute_query("INSERT INTO worker_payments (worker_name, date, amount, note) VALUES (?, ?, ?, ?)",
                                  (w_name, str(w_date), w_amount, w_note))
                    st.success("Ustaga berilgan pul saqlandi!")
                    st.rerun()

    df_worker = get_data("worker_payments")
    if not df_worker.empty:
        st.dataframe(df_worker, use_container_width=True)
        
        # O'chirish bo'limi (Prorab uchun)
        if is_admin:
            with st.expander("🗑️ Ustaning to'lovini o'chirish"):
                worker_pay_id = st.number_input("O'chirmoqchi bo'lgan to'lov ID raqamini kiriting:", min_value=1, step=1, key="del_worker")
                if st.button("Ustaning to'lovini o'chirish"):
                    execute_query("DELETE FROM worker_payments WHERE id = ?", (worker_pay_id,))
                    st.success(f"ID: {worker_pay_id} bo'lgan to'lov o'chirildi!")
                    st.rerun()

        st.metric("Ustalarga berilgan jami pul:", f"{df_worker['amount'].sum():,.2f}")
    else:
        st.info("Ustalar to'lovlari tarixi hozircha yo'q.")

# ---------------------------------------------------------
# TAB 4: PDF EXPORT
# ---------------------------------------------------------
with tab4:
    st.header("4. PDF Hisobot Yaratish")
    
    def generate_pdf():
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        title = Paragraph("<b>Qurilish Ob'ekti Bo'yicha Hisobot</b>", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Smeta jadvali
        works = get_data("works")
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
        file_name="qurilish_smeta_hisobot.pdf",
        mime="application/pdf"
    )
