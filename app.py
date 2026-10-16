import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os
import html
import io
import datetime

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

DB_PATH = "construction_clean.db"

st.set_page_config(
    page_title="Qurilish SMETA | Prorab Abdulla",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- PREMIUM INTERFEYS --------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root { --navy:#101828; --blue:#2563eb; --gold:#eabf65; --bg:#f4f7fb; --muted:#667085; }
.stApp { background:var(--bg); font-family:'Inter',sans-serif; color:#182230; }
[data-testid="stHeader"] { background:rgba(244,247,251,.92); }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#101828 0%,#172b49 100%); }
[data-testid="stSidebar"] * { color:#edf2fa !important; }
.block-container { max-width:1500px; padding-top:1.6rem; padding-bottom:2.5rem; }
.main-header {
  font-size:27px; font-weight:800; letter-spacing:-.7px; color:#101828;
  padding:18px 22px; margin:0 0 20px; background:white;
  border:1px solid #e5eaf2; border-left:5px solid #eabf65;
  border-radius:14px; box-shadow:0 5px 20px rgba(16,24,40,.04);
}
.hero {
  padding:28px; border-radius:20px; color:white;
  background:linear-gradient(120deg,#101828,#1d4274);
  border:1px solid #28486f; margin-bottom:20px;
}
.hero h1 { color:white !important; font-size:30px; margin:5px 0; }
.hero p { color:#d0d9e8; margin-bottom:0; }
h1,h2,h3 { color:#101828; font-weight:750 !important; }
[data-testid="stMetric"] {
  background:white; padding:18px 20px; border:1px solid #e4eaf2;
  border-radius:15px; box-shadow:0 5px 18px rgba(16,24,40,.045);
}
[data-testid="stMetricLabel"] { color:#667085; font-size:13px; font-weight:600; }
[data-testid="stMetricValue"] { color:#175cd3; font-weight:800; font-size:25px; }
[data-testid="stTabs"] [role="tablist"] { gap:6px; border-bottom:1px solid #dfe6ef; flex-wrap:wrap; }
[data-testid="stTabs"] button[role="tab"] {
  background:#eaf0f8; border-radius:9px 9px 0 0; padding:11px 13px;
  font-weight:650; color:#344054;
}
[data-testid="stTabs"] button[aria-selected="true"] { background:#175cd3; color:white !important; }
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
  background:linear-gradient(135deg,#2563eb,#1746a2); color:white !important;
  border:0; border-radius:10px; min-height:42px; font-weight:700;
  box-shadow:0 4px 10px rgba(37,99,235,.15); transition:all .2s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
  background:linear-gradient(135deg,#1746a2,#123578); transform:translateY(-1px);
}
[data-testid="stDataFrame"], [data-testid="stTable"] {
  background:white; border:1px solid #e4eaf2; border-radius:12px; overflow:hidden;
}
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input, [data-testid="stSelectbox"] div[data-baseweb="select"] {
  border-radius:9px;
}
[data-testid="stForm"] {
  background:white; padding:18px; border:1px solid #e4eaf2;
  border-radius:14px; box-shadow:0 4px 15px rgba(16,24,40,.035);
}
.footer-brand { text-align:center; margin-top:40px; padding:18px; font-size:13px;
  color:#667085; font-weight:600; border-top:1px solid #e0e7f0; }
.login-wrap { background:white; padding:28px; border:1px solid #e4eaf2;
  border-radius:20px; box-shadow:0 18px 50px rgba(16,24,40,.08); }
.small-note { color:#667085; font-size:12px; }
@media(max-width:768px) {
  .block-container { padding:1rem .7rem 2rem; }
  .main-header { font-size:21px; padding:14px; }
  .hero { padding:20px; }
  .hero h1 { font-size:24px; }
  [data-testid="stMetric"] { padding:12px; }
  [data-testid="stMetricValue"] { font-size:19px; }
}
</style>
""", unsafe_allow_html=True)


# -------------------- DATABASE --------------------
def db_connect():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_db():
    with db_connect() as conn:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            project_id INTEGER
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS owner_works (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER, job_name TEXT, unit TEXT,
            quantity REAL, price_per_unit REAL, total_price REAL
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS worker_works (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER, job_name TEXT, unit TEXT,
            quantity REAL, price_per_unit REAL, total_price REAL
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS owner_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER, date TEXT, amount REAL, note TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS worker_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER, worker_name TEXT, date TEXT,
            amount REAL, note TEXT
        )""")

        # Eski bazadagi oddiy parollarni ham ishlatishga moslash:
        # standart admin faqat yangi bazada yaratiladi.
        c.execute("SELECT id FROM users WHERE username = ?", ("abdulla",))
        if not c.fetchone():
            c.execute(
                "INSERT INTO users (username,password,role,project_id) VALUES (?,?,?,NULL)",
                ("abdulla", hash_password("1234"), "admin")
            )
        conn.commit()

    # Eski bazadagi parol oddiy matn bo'lsa, login tekshiruvi uni ham qabul qiladi.


def get_data(query, params=()):
    with db_connect() as conn:
        return pd.read_sql_query(query, conn, params=params)


def execute_query(query, params=()):
    with db_connect() as conn:
        conn.execute(query, params)
        conn.commit()


def authenticate(username, password):
    users = get_data("SELECT * FROM users WHERE username = ?", (username,))
    if users.empty:
        return None
    row = users.iloc[0].to_dict()
    stored = str(row.get("password", ""))
    # SHA-256 xesh yoki eski bazadagi avvalgi oddiy parol
    if stored == hash_password(password) or stored == password:
        # Eski oddiy parolni keyingi safar uchun xeshlangan holatga o'tkazish
        if stored == password:
            execute_query("UPDATE users SET password=? WHERE id=?",
                          (hash_password(password), row["id"]))
        return row
    return None


init_db()


# -------------------- SESSION --------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None


# -------------------- COMMON HELPERS --------------------
def money(value):
    try:
        return f"{float(value):,.0f}".replace(",", " ") + " so'm"
    except (TypeError, ValueError):
        return "0 so'm"


def safe_filename(text):
    allowed = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(text))
    return allowed.strip("_") or "hisobot"


def show_delete_table(df, table, label, key_prefix, display_columns, display_names):
    if df.empty:
        st.info("Hozircha ma'lumot kiritilmagan.")
        return
    view = df[display_columns].copy()
    view.columns = display_names
    view.index = range(1, len(view) + 1)
    st.dataframe(view, use_container_width=True, hide_index=False)
    ids = df["id"].tolist()
    selected = st.selectbox(
        "O'chirish uchun yozuvni tanlang",
        options=ids,
        format_func=lambda x: f"ID {x} — {str(df.loc[df['id'] == x].iloc[0][display_columns[0]])}",
        key=f"{key_prefix}_select"
    )
    if st.button("🗑️ Tanlangan yozuvni o'chirish", key=f"{key_prefix}_delete"):
        execute_query(f"DELETE FROM {table} WHERE id = ?", (int(selected),))
        st.success("Yozuv o'chirildi.")
        st.rerun()


def generate_custom_pdf(project_name, project_id, is_owner=True):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=28, leftMargin=28,
        topMargin=30, bottomMargin=30
    )
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Heading1"], fontName="Helvetica-Bold",
        fontSize=16, alignment=1, textColor=colors.HexColor("#12345a"),
        spaceAfter=8
    )
    normal = ParagraphStyle(
        "CustomNormal", parent=styles["Normal"], fontName="Helvetica",
        fontSize=9, leading=13, textColor=colors.HexColor("#333333")
    )
    bold = ParagraphStyle(
        "CustomBold", parent=normal, fontName="Helvetica-Bold"
    )
    elements.append(Paragraph("QURILISH PRO — SMETA HISOBOTI", title_style))
    elements.append(Paragraph(
        "Bajariladigan ishlar, hajmlar va moliyaviy hisob-kitob",
        ParagraphStyle("sub", parent=normal, alignment=1, textColor=colors.HexColor("#667085"))
    ))
    elements.append(Spacer(1, 12))
    elements.append(Table([[""]], colWidths=[539], rowHeights=[3],
                          style=[("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#2563eb"))]))
    elements.append(Spacer(1, 12))

    now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    info = [
        [Paragraph("<b>Prorab:</b> Abdulla", normal),
         Paragraph(f"<b>Hisobot sanasi:</b> {now}", normal)],
        [Paragraph(f"<b>Obyekt:</b> {html.escape(str(project_name))}", normal),
         Paragraph(f"<b>Hisobot turi:</b> {'Uy egasi smetasi' if is_owner else 'Ustalar ish haqi'}", normal)]
    ]
    info_table = Table(info, colWidths=[270, 269])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4f7fb")),
        ("BOX", (0, 0), (-1, -1), .5, colors.HexColor("#d9e2ef")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 16))

    table_name = "owner_works" if is_owner else "worker_works"
    data = get_data(
        f"SELECT job_name,unit,quantity,price_per_unit,total_price FROM {table_name} WHERE project_id=? ORDER BY id",
        (project_id,)
    )
    rows = [["№", "Ish nomi", "Birlik", "Hajmi", "Birlik narxi", "Jami qiymat"]]
    total = 0.0
    for i, r in data.iterrows():
        amount = float(r["total_price"] or 0)
        total += amount
        rows.append([
            str(i + 1), Paragraph(html.escape(str(r["job_name"]), quote=False), normal),
            str(r["unit"]), f"{float(r['quantity'] or 0):,.2f}",
            f"{float(r['price_per_unit'] or 0):,.0f}".replace(",", " "),
            f"{amount:,.0f}".replace(",", " ")
        ])
    if data.empty:
        rows.append(["1", "Ma'lumot kiritilmagan", "-", "0", "0", "0"])

    table = Table(rows, colWidths=[28, 190, 48, 58, 100, 115], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1746a2")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (1, 1), (1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#d0d7e2")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f8fc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 16))

    total_label = "UY EGASI SMETASINING JAMI" if is_owner else "USTALAR ISH HAQINING JAMI"
    elements.append(Paragraph(
        f"<b>{total_label}: {money(total)}</b>",
        ParagraphStyle("total", parent=bold, fontSize=12, textColor=colors.HexColor("#175cd3"))
    ))
    elements.append(Spacer(1, 32))
    signatures = [
        [Paragraph("<b>Prorab:</b> Abdulla", normal),
         Paragraph("<b>Buyurtmachi / usta:</b>", normal)],
        [Paragraph("Imzo: ________________", normal),
         Paragraph("Imzo: ________________", normal)],
        [Paragraph(f"Sana: {datetime.datetime.now():%d.%m.%Y}", normal),
         Paragraph(f"Sana: {datetime.datetime.now():%d.%m.%Y}", normal)]
    ]
    sign_table = Table(signatures, colWidths=[270, 269])
    sign_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(sign_table)
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


# -------------------- LOGIN --------------------
if not st.session_state.logged_in:
    left, center, right = st.columns([1, 1.05, 1])
    with center:
        st.markdown("""
        <div style="text-align:center;padding:30px 8px 16px">
          <div style="display:inline-block;background:linear-gradient(135deg,#101828,#234776);
          padding:20px 24px;border-radius:22px;font-size:42px;box-shadow:0 12px 30px #10182825">🏗️</div>
          <h1 style="font-size:30px;margin:16px 0 4px;color:#101828">QURILISH PRO</h1>
          <p style="color:#667085;font-size:14px">Obyektlar va moliyaviy hisob boshqaruvi</p>
          <div style="width:60px;height:4px;background:#eabf65;border-radius:4px;margin:18px auto"></div>
        </div>
        """, unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("### 🔐 Tizimga kirish")
            st.caption("Davom etish uchun login va parolingizni kiriting.")
            with st.form("login_form"):
                username = st.text_input("Login", placeholder="Loginni kiriting")
                password = st.text_input("Parol", type="password", placeholder="Parolni kiriting")
                submitted = st.form_submit_button("Kirish  →", use_container_width=True)
            if submitted:
                user = authenticate(username.strip(), password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_info = user
                    st.rerun()
                else:
                    st.error("Login yoki parol noto'g'ri.")
        st.markdown("<div class='footer-brand'>👷 Prorab Abdulla · Qurilish Smeta</div>", unsafe_allow_html=True)


# -------------------- APPLICATION --------------------
else:
    user = st.session_state.user_info
    role = user["role"]
    st.sidebar.markdown("## 🏗️ QURILISH SMETA")
    st.sidebar.caption("OBYEKTLARNI BOSHQARISH")
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### 👤 {str(user['username']).capitalize()}")
    st.sidebar.markdown(f"Rol: **{str(role).upper()}**")
    if st.sidebar.button("🚪 Tizimdan chiqish", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.rerun()
    st.sidebar.markdown("---")
    st.sidebar.caption("Prorab Abdulla · 2026")

    # ==================== ADMIN ====================
    if role == "admin":
        st.markdown("""
        <div class="hero">
          <div style="font-size:12px;letter-spacing:2px;font-weight:700;color:#eabf65">BOSHQARUV PANELI</div>
          <h1>Assalomu alaykum, Prorab Abdulla 👷</h1>
          <p>Qurilish obyektlari, smetalar va to'lovlarni bitta joydan boshqaring.</p>
        </div>
        """, unsafe_allow_html=True)

        projects = get_data("SELECT id,project_name FROM projects ORDER BY id DESC")
        if not projects.empty:
            p_map = {f"{r['project_name']}  ·  ID {r['id']}": int(r["id"])
                     for _, r in projects.iterrows()}
            selected_label = st.selectbox("📂 Ishlayotgan obyektni tanlang", list(p_map.keys()))
            active_pid = p_map[selected_label]
            sel_p = str(projects.loc[projects["id"] == active_pid, "project_name"].iloc[0])
        else:
            active_pid = None
            sel_p = ""

        with st.expander("➕ Yangi qurilish obyektini qo'shish", expanded=projects.empty):
            with st.form("add_project_form", clear_on_submit=True):
                new_project = st.text_input("Obyekt nomi", placeholder="Masalan: Yunusoboddagi uy")
                add_project = st.form_submit_button("Obyektni yaratish")
            if add_project:
                if new_project.strip():
                    execute_query("INSERT INTO projects (project_name) VALUES (?)", (new_project.strip(),))
                    st.success("Obyekt yaratildi.")
                    st.rerun()
                else:
                    st.warning("Obyekt nomini kiriting.")

        # Umumiy ko'rsatkichlar
        owner_total = float(get_data("SELECT COALESCE(SUM(total_price),0) AS v FROM owner_works")["v"].iloc[0])
        worker_total = float(get_data("SELECT COALESCE(SUM(total_price),0) AS v FROM worker_works")["v"].iloc[0])
        owner_paid = float(get_data("SELECT COALESCE(SUM(amount),0) AS v FROM owner_payments")["v"].iloc[0])
        worker_paid = float(get_data("SELECT COALESCE(SUM(amount),0) AS v FROM worker_payments")["v"].iloc[0])
        project_count = int(get_data("SELECT COUNT(*) AS v FROM projects")["v"].iloc[0])

        st.markdown("### 📊 Umumiy ko'rsatkichlar")
        a, b, c, d, e = st.columns(5)
        a.metric("🏠 Obyektlar", f"{project_count} ta")
        b.metric("📋 Buyurtmachi smetasi", money(owner_total))
        c.metric("💰 Olingan pullar", money(owner_paid))
        d.metric("👷 Ustalar ish haqi", money(worker_total))
        e.metric("💵 Ustalarga berilgan", money(worker_paid))

        if active_pid is None:
            st.info("Boshlash uchun yuqoridan yangi obyekt qo'shing.")
        else:
            st.markdown(f"<div class='main-header'>🏠 {html.escape(sel_p)} — obyekt boshqaruvi</div>",
                        unsafe_allow_html=True)
            tabs = st.tabs([
                "🏠 Uy egasi smetasi", "👷 Ustalar smetasi", "💰 Uy egasi pullari",
                "💵 Ustalarga to'lov", "🔑 Loginlar", "📄 PDF hisobot"
            ])

            # OWNER ESTIMATE
            with tabs[0]:
                st.markdown("### Uy egasi uchun smeta")
                with st.form("owner_work_form", clear_on_submit=True):
                    c1, c2 = st.columns([2, 1])
                    job = c1.text_input("Ish nomi", placeholder="Masalan: Fundament betoni")
                    unit = c2.selectbox("O'lchov birligi", ["kv.m", "kub.m", "metr", "dona", "komplekt"])
                    c3, c4 = st.columns(2)
                    qty = c3.number_input("Hajmi", min_value=0.0, step=0.1, format="%.2f")
                    price = c4.number_input("Birlik narxi (so'm)", min_value=0.0, step=1000.0)
                    submitted = st.form_submit_button("➕ Smetaga qo'shish", use_container_width=True)
                if submitted:
                    if job.strip():
                        execute_query("""INSERT INTO owner_works
                            (project_id,job_name,unit,quantity,price_per_unit,total_price)
                            VALUES (?,?,?,?,?,?)""",
                            (active_pid, job.strip(), unit, qty, price, qty * price))
                        st.success("Smetaga qo'shildi.")
                        st.rerun()
                    else:
                        st.warning("Ish nomini kiriting.")
                df = get_data("SELECT id,job_name,unit,quantity,price_per_unit,total_price FROM owner_works WHERE project_id=? ORDER BY id",
                              (active_pid,))
                if not df.empty:
                    st.dataframe(df.rename(columns={
                        "job_name":"Ish nomi", "unit":"Birlik", "quantity":"Hajmi",
                        "price_per_unit":"Birlik narxi", "total_price":"Jami qiymat"
                    }).drop(columns=["id"]).assign(
                        **{"Birlik narxi": lambda x: x["Birlik narxi"].map(money),
                           "Jami qiymat": lambda x: x["Jami qiymat"].map(money)}
                    ), use_container_width=True, hide_index=True)
                    st.metric("Uy egasi smetasining jami", money(df["total_price"].sum()))
                    show_delete_table(df, "owner_works", "ish", "owner_work", ["job_name","unit","quantity","price_per_unit","total_price"],
                                      ["Ish nomi","Birlik","Hajmi","Birlik narxi","Jami qiymat"])
                else:
                    st.info("Hali smeta kiritilmagan.")

            # WORKER ESTIMATE
            with tabs[1]:
                st.markdown("### Ustalar uchun ish haqi smetasi")
                with st.form("worker_work_form", clear_on_submit=True):
                    c1, c2 = st.columns([2, 1])
                    job = c1.text_input("Ish nomi", key="worker_job", placeholder="Masalan: G'isht terish")
                    unit = c2.selectbox("O'lchov birligi", ["kv.m", "kub.m", "metr", "dona", "komplekt"], key="worker_unit")
                    c3, c4 = st.columns(2)
                    qty = c3.number_input("Hajmi", min_value=0.0, step=0.1, format="%.2f", key="worker_qty")
                    price = c4.number_input("Birlik ish haqi (so'm)", min_value=0.0, step=1000.0, key="worker_price")
                    submitted = st.form_submit_button("➕ Ish haqi smetasiga qo'shish", use_container_width=True)
                if submitted:
                    if job.strip():
                        execute_query("""INSERT INTO worker_works
                            (project_id,job_name,unit,quantity,price_per_unit,total_price)
                            VALUES (?,?,?,?,?,?)""",
                            (active_pid, job.strip(), unit, qty, price, qty * price))
                        st.success("Ish haqi smetasiga qo'shildi.")
                        st.rerun()
                    else:
                        st.warning("Ish nomini kiriting.")
                df = get_data("SELECT id,job_name,unit,quantity,price_per_unit,total_price FROM worker_works WHERE project_id=? ORDER BY id",
                              (active_pid,))
                if not df.empty:
                    view = df.drop(columns=["id"]).rename(columns={
                        "job_name":"Ish nomi","unit":"Birlik","quantity":"Hajmi",
                        "price_per_unit":"Birlik ish haqi","total_price":"Jami ish haqi"})
                    view["Birlik ish haqi"] = view["Birlik ish haqi"].map(money)
                    view["Jami ish haqi"] = view["Jami ish haqi"].map(money)
                    st.dataframe(view, use_container_width=True, hide_index=True)
                    st.metric("Ustalar ish haqining jami", money(df["total_price"].sum()))
                    show_delete_table(df, "worker_works", "ish", "worker_work",
                                      ["job_name","unit","quantity","price_per_unit","total_price"],
                                      ["Ish nomi","Birlik","Hajmi","Birlik ish haqi","Jami ish haqi"])
                else:
                    st.info("Hali ustalar smetasi kiritilmagan.")

            # OWNER PAYMENTS
            with tabs[2]:
                st.markdown("### Uy egasidan olingan pullar")
                with st.form("owner_payment_form", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    date = c1.date_input("To'lov sanasi", value=datetime.date.today())
                    amount = c2.number_input("Summa (so'm)", min_value=0.0, step=10000.0)
                    note = st.text_input("Izoh", placeholder="Masalan: Fundament uchun")
                    submitted = st.form_submit_button("💾 To'lovni saqlash", use_container_width=True)
                if submitted:
                    if amount > 0:
                        execute_query("INSERT INTO owner_payments (project_id,date,amount,note) VALUES (?,?,?,?)",
                                      (active_pid, str(date), amount, note.strip()))
                        st.success("To'lov saqlandi.")
                        st.rerun()
                    else:
                        st.warning("Summani noldan katta kiriting.")
                df = get_data("SELECT id,date,amount,note FROM owner_payments WHERE project_id=? ORDER BY date DESC,id DESC",
                              (active_pid,))
                if not df.empty:
                    view = df.drop(columns=["id"]).rename(columns={"date":"Sana","amount":"Summa","note":"Izoh"})
                    view["Summa"] = view["Summa"].map(money)
                    st.dataframe(view, use_container_width=True, hide_index=True)
                    total_paid = float(df["amount"].sum())
                    estimate = float(get_data("SELECT COALESCE(SUM(total_price),0) v FROM owner_works WHERE project_id=?",
                                              (active_pid,))["v"].iloc[0])
                    x, y = st.columns(2)
                    x.metric("Jami olingan pul", money(total_paid))
                    y.metric("Smeta bo'yicha qoldiq", money(estimate - total_paid))
                    show_delete_table(df, "owner_payments", "to'lov", "owner_payment",
                                      ["date","amount","note"], ["Sana","Summa","Izoh"])
                else:
                    st.info("Hozircha to'lovlar kiritilmagan.")

            # WORKER PAYMENTS
            with tabs[3]:
                st.markdown("### Ustalarga berilgan pullar")
                with st.form("worker_payment_form", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    worker_name = c1.text_input("Usta nomi", placeholder="Ustaning ismi")
                    date = c2.date_input("To'lov sanasi", value=datetime.date.today(), key="worker_payment_date")
                    c3, c4 = st.columns(2)
                    amount = c3.number_input("Summa (so'm)", min_value=0.0, step=5000.0, key="worker_payment_amount")
                    note = c4.text_input("Izoh", key="worker_payment_note")
                    submitted = st.form_submit_button("💾 To'lovni saqlash", use_container_width=True)
                if submitted:
                    if amount > 0:
                        execute_query("""INSERT INTO worker_payments
                            (project_id,worker_name,date,amount,note) VALUES (?,?,?,?,?)""",
                            (active_pid, worker_name.strip(), str(date), amount, note.strip()))
                        st.success("Ustaga to'lov saqlandi.")
                        st.rerun()
                    else:
                        st.warning("Summani noldan katta kiriting.")
                df = get_data("SELECT id,worker_name,date,amount,note FROM worker_payments WHERE project_id=? ORDER BY date DESC,id DESC",
                              (active_pid,))
                if not df.empty:
                    view = df.drop(columns=["id"]).rename(columns={
                        "worker_name":"Usta nomi","date":"Sana","amount":"Summa","note":"Izoh"})
                    view["Summa"] = view["Summa"].map(money)
                    st.dataframe(view, use_container_width=True, hide_index=True)
                    st.metric("Jami ustalarga berilgan", money(df["amount"].sum()))
                    show_delete_table(df, "worker_payments", "to'lov", "worker_payment",
                                      ["worker_name","date","amount","note"],
                                      ["Usta nomi","Sana","Summa","Izoh"])
                else:
                    st.info("Hozircha ustalarga to'lov kiritilmagan.")

            # USERS
            with tabs[4]:
                st.markdown("### Obyekt foydalanuvchilarini boshqarish")
                l1, l2 = st.columns(2)
                with l1:
                    with st.form("owner_login_form", clear_on_submit=True):
                        st.markdown("#### 🏠 Uy egasi uchun")
                        username = st.text_input("Yangi login", key="owner_username")
                        password = st.text_input("Yangi parol", type="password", key="owner_password")
                        submit = st.form_submit_button("Uy egasi loginini yaratish", use_container_width=True)
                    if submit:
                        if username.strip() and password:
                            try:
                                execute_query("INSERT INTO users (username,password,role,project_id) VALUES (?,?,?,?)",
                                              (username.strip(), hash_password(password), "uy_egasi", active_pid))
                                st.success("Uy egasi foydalanuvchisi yaratildi.")
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.error("Bu login band. Boshqa login tanlang.")
                        else:
                            st.warning("Login va parolni kiriting.")
                with l2:
                    with st.form("worker_login_form", clear_on_submit=True):
                        st.markdown("#### 👷 Usta uchun")
                        username = st.text_input("Yangi login", key="worker_username")
                        password = st.text_input("Yangi parol", type="password", key="worker_password")
                        submit = st.form_submit_button("Usta loginini yaratish", use_container_width=True)
                    if submit:
                        if username.strip() and password:
                            try:
                                execute_query("INSERT INTO users (username,password,role,project_id) VALUES (?,?,?,?)",
                                              (username.strip(), hash_password(password), "usta", active_pid))
                                st.success("Usta foydalanuvchisi yaratildi.")
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.error("Bu login band. Boshqa login tanlang.")
                        else:
                            st.warning("Login va parolni kiriting.")
                st.markdown("#### 👥 Shu obyektga biriktirilgan loginlar")
                users_df = get_data("SELECT id,username,role FROM users WHERE project_id=? ORDER BY id",
                                    (active_pid,))
                if not users_df.empty:
                    view = users_df.rename(columns={"id":"ID","username":"Login","role":"Rol"})
                    st.dataframe(view, use_container_width=True, hide_index=True)
                    selected_user = st.selectbox(
                        "O'chirish uchun foydalanuvchi",
                        users_df["id"].tolist(),
                        format_func=lambda x: f"{users_df.loc[users_df['id']==x,'username'].iloc[0]} (ID {x})"
                    )
                    if st.button("🗑️ Foydalanuvchini o'chirish", key="delete_user"):
                        execute_query("DELETE FROM users WHERE id=? AND role != 'admin'", (int(selected_user),))
                        st.success("Foydalanuvchi o'chirildi (administrator o'chirilmaydi).")
                        st.rerun()
                else:
                    st.info("Bu obyekt uchun hali alohida login yaratilmagan.")

            # PDF
            with tabs[5]:
                st.markdown("### 📄 Professional PDF hisobot")
                st.write("Kerakli hisobot turini tanlab, PDF faylni yuklab oling.")
                pdf_type = st.radio("Hisobot turi", ["Uy egasi smetasi", "Ustalar ish haqi"], horizontal=True)
                is_owner = pdf_type == "Uy egasi smetasi"
                pdf_bytes = generate_custom_pdf(sel_p, active_pid, is_owner=is_owner)
                st.download_button(
                    "📥 PDF hisobotni yuklab olish",
                    data=pdf_bytes,
                    file_name=f"{safe_filename(sel_p)}_{'Uy_Egasi' if is_owner else 'Ustalar'}_Smeta.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

        st.markdown("---")
        st.markdown("<div class='footer-brand'>🏗️ QURILISH PRO · Prorab Abdulla · Obyektlar nazorati</div>",
                    unsafe_allow_html=True)

    # ==================== OWNER PANEL ====================
    elif role == "uy_egasi":
        p_id = user.get("project_id")
        info = get_data("SELECT project_name FROM projects WHERE id=?", (p_id,))
        p_name = str(info.iloc[0]["project_name"]) if not info.empty else "Uyingiz"
        st.markdown(f"<div class='main-header'>🏡 {html.escape(p_name)} — Uy egasi paneli</div>",
                    unsafe_allow_html=True)
        t1, t2 = st.tabs(["📊 Smeta", "💰 To'lovlarim"])
        with t1:
            df = get_data("SELECT job_name,unit,quantity,price_per_unit,total_price FROM owner_works WHERE project_id=? ORDER BY id",
                          (p_id,))
            if df.empty:
                st.info("Hozircha smeta kiritilmagan.")
            else:
                view = df.rename(columns={"job_name":"Ish nomi","unit":"Birlik","quantity":"Hajmi",
                                          "price_per_unit":"Birlik narxi","total_price":"Jami qiymat"})
                view["Birlik narxi"] = view["Birlik narxi"].map(money)
                view["Jami qiymat"] = view["Jami qiymat"].map(money)
                st.dataframe(view, use_container_width=True, hide_index=True)
                st.metric("Uyingizning umumiy smetasi", money(df["total_price"].sum()))
        with t2:
            df = get_data("SELECT date,amount,note FROM owner_payments WHERE project_id=? ORDER BY date DESC",
                          (p_id,))
            total_paid = float(df["amount"].sum()) if not df.empty else 0
            total_estimate = float(get_data("SELECT COALESCE(SUM(total_price),0) v FROM owner_works WHERE project_id=?",
                                            (p_id,))["v"].iloc[0])
            a, b = st.columns(2)
            a.metric("Jami bergan pulingiz", money(total_paid))
            b.metric("Smeta bo'yicha qoldiq", money(total_estimate - total_paid))
            if df.empty:
                st.info("To'lovlar tarixi hali yo'q.")
            else:
                view = df.rename(columns={"date":"Sana","amount":"Berilgan summa","note":"Izoh"})
                view["Berilgan summa"] = view["Berilgan summa"].map(money)
                st.dataframe(view, use_container_width=True, hide_index=True)

        st.markdown("<div class='footer-brand'>🏗️ Qurilish PRO · Uy egasi paneli</div>",
                    unsafe_allow_html=True)

    # ==================== WORKER PANEL ====================
    elif role == "usta":
        p_id = user.get("project_id")
        info = get_data("SELECT project_name FROM projects WHERE id=?", (p_id,))
        p_name = str(info.iloc[0]["project_name"]) if not info.empty else "Obyekt"
        st.markdown(f"<div class='main-header'>👷 {html.escape(p_name)} — Usta paneli</div>",
                    unsafe_allow_html=True)
        t1, t2 = st.tabs(["📋 Ish hajmlari va ish haqi", "💵 Olingan pullar"])
        with t1:
            df = get_data("SELECT job_name,unit,quantity,price_per_unit,total_price FROM worker_works WHERE project_id=? ORDER BY id",
                          (p_id,))
            if df.empty:
                st.info("Hozircha ishlar kiritilmagan.")
            else:
                view = df.rename(columns={"job_name":"Ish nomi","unit":"Birlik","quantity":"Hajmi",
                                          "price_per_unit":"Birlik ish haqi","total_price":"Jami ish haqi"})
                view["Birlik ish haqi"] = view["Birlik ish haqi"].map(money)
                view["Jami ish haqi"] = view["Jami ish haqi"].map(money)
                st.dataframe(view, use_container_width=True, hide_index=True)
                st.metric("Umumiy ish haqingiz", money(df["total_price"].sum()))
        with t2:
            df = get_data("SELECT worker_name,date,amount,note FROM worker_payments WHERE project_id=? ORDER BY date DESC",
                          (p_id,))
            if df.empty:
                st.info("Sizga hali to'lov kiritilmagan.")
            else:
                view = df.rename(columns={"worker_name":"Usta nomi","date":"Sana","amount":"Olingan summa","note":"Izoh"})
                view["Olingan summa"] = view["Olingan summa"].map(money)
                st.dataframe(view, use_container_width=True, hide_index=True)
                st.metric("Siz olgan jami pul", money(df["amount"].sum()))
        st.markdown("<div class='footer-brand'>🏗️ Qurilish PRO · Usta paneli</div>",
                    unsafe_allow_html=True)

    else:
        st.error("Foydalanuvchi roli tanilmadi. Administrator bilan bog'laning.")
