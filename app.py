import streamlit as st
import sqlite3
import hashlib
import hmac
import secrets
import pandas as pd
from datetime import datetime, date
from contextlib import contextmanager
from pathlib import Path

# ============================================================
# PRORAB ABDULLA | Qurilish smetasi va moliya boshqaruvi
# Python 3.10+ | Streamlit | SQLite
# ============================================================

APP_TITLE = "Prorab Abdulla"
DB_PATH = Path("prorab_abdulla.db")
CURRENCY = "so'm"

st.set_page_config(
    page_title=f"{APP_TITLE} | Boshqaruv tizimi",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------- DESIGN ----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: Inter, sans-serif; }
.stApp { background: #f4f7fb; }
.block-container { padding-top: 1.5rem; padding-bottom: 2.5rem; max-width: 1500px; }
[data-testid="stSidebar"] { background: #101d35; }
[data-testid="stSidebar"] * { color: #edf3ff !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #cbd5e1 !important; }
.brand { display:flex; align-items:center; gap:12px; padding: 8px 0 22px; }
.brand-icon { background:linear-gradient(135deg,#2563eb,#0ea5e9); width:46px;height:46px;
 border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:24px; }
.brand-title { font-size:19px;font-weight:800;color:white;letter-spacing:-.4px; }
.brand-sub { color:#94a3b8;font-size:11px;margin-top:2px; }
.page-eyebrow { color:#64748b;font-size:12px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase; }
.page-title { color:#13213a;font-size:30px;font-weight:800;letter-spacing:-1px;margin:2px 0 5px; }
.page-desc { color:#64748b;font-size:14px;margin-bottom:20px; }
.metric-card { background:white;border:1px solid #e7edf5;border-radius:16px;padding:18px 20px;
 box-shadow:0 4px 18px rgba(15,23,42,.035);min-height:120px; }
.metric-label { color:#64748b;font-size:12px;font-weight:600;margin-bottom:9px; }
.metric-value { color:#13213a;font-size:25px;font-weight:800;letter-spacing:-.7px; }
.metric-note { color:#94a3b8;font-size:11px;margin-top:5px; }
.panel { background:white;border:1px solid #e7edf5;border-radius:16px;padding:20px;
 box-shadow:0 4px 18px rgba(15,23,42,.03); }
.section-title { color:#17243b;font-size:17px;font-weight:750;margin-bottom:3px; }
.muted { color:#64748b;font-size:13px; }
div.stButton > button { border-radius:10px;font-weight:650;min-height:42px; }
div[data-testid="stForm"] { background:white;border:1px solid #e7edf5;border-radius:14px;padding:18px; }
.stTextInput input,.stNumberInput input,.stDateInput input,.stSelectbox div[data-baseweb="select"] {
 border-radius:9px;
}
[data-testid="stDataFrame"] { border:1px solid #e7edf5;border-radius:12px;overflow:hidden; }
hr { border-color:#e7edf5; }
.login-wrap { max-width:480px;margin:7vh auto;background:white;padding:34px;border-radius:22px;
 border:1px solid #e7edf5;box-shadow:0 15px 50px rgba(15,23,42,.08); }
.small-tag { display:inline-block;padding:5px 9px;border-radius:20px;background:#eff6ff;color:#1d4ed8;
 font-size:11px;font-weight:700; }
</style>
""", unsafe_allow_html=True)

# ------------------------- DATABASE --------------------------
@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    finally:
        conn.close()

def hash_password(password: str, salt: bytes = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260_000)
    return salt.hex() + "$" + digest.hex()

def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 260_000)
        return hmac.compare_digest(actual.hex(), digest_hex)
    except Exception:
        return False

def init_db():
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','usta')),
            project_id INTEGER,
            full_name TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            address TEXT DEFAULT '',
            note TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS works (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            unit TEXT NOT NULL,
            quantity REAL NOT NULL DEFAULT 0,
            unit_price INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            kind TEXT NOT NULL CHECK(kind IN ('Kirim','Chiqim')),
            amount INTEGER NOT NULL,
            note TEXT NOT NULL,
            txn_date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        """)
        admin = conn.execute("SELECT id FROM users WHERE username='admin'").fetchone()
        if not admin:
            conn.execute(
                "INSERT INTO users(username,password_hash,role,project_id,full_name,created_at) VALUES(?,?,?,?,?,?)",
                ("admin", hash_password("Admin123!"), "admin", None, "Administrator", datetime.now().isoformat(timespec="seconds"))
            )
        count = conn.execute("SELECT COUNT(*) AS n FROM projects").fetchone()["n"]
        if count == 0:
            cur = conn.execute(
                "INSERT INTO projects(name,address,note,created_at) VALUES(?,?,?,?)",
                ("1-Obyekt | Chilonzor rezidensiya", "Toshkent shahri, Chilonzor", "Boshlang'ich obyekt", datetime.now().isoformat(timespec="seconds"))
            )
            pid = cur.lastrowid
            conn.executemany(
                """INSERT INTO works(project_id,category,name,unit,quantity,unit_price,created_at)
                   VALUES(?,?,?,?,?,?,?)""",
                [
                    (pid, "Karkas", "Beton quyish (Fundament)", "m³", 45, 150000, datetime.now().isoformat(timespec="seconds")),
                    (pid, "Devor", "Pishgan g'isht terish", "dona", 12000, 300, datetime.now().isoformat(timespec="seconds")),
                ]
            )
            conn.execute(
                "INSERT INTO users(username,password_hash,role,project_id,full_name,created_at) VALUES(?,?,?,?,?,?)",
                ("usta1", hash_password("Usta111!"), "usta", pid, "Usta 1", datetime.now().isoformat(timespec="seconds"))
            )

init_db()

WORK_CATALOG = [
    ("Beton quyish", "m³", "Karkas"), ("Padushka quyish", "m³", "Karkas"),
    ("Rigel / Kolonna", "m³", "Karkas"), ("Seysmopoyas", "m³", "Karkas"),
    ("Pishgan g'isht terish", "dona", "Devor"), ("Gazoblok terish", "dona", "Devor"),
    ("Styajka quyish", "m²", "Ichki ta'mir"), ("Monolit quyish", "m²", "Karkas"),
    ("Tsement suvoq", "m²", "Ichki ta'mir"), ("Tom yopish (Krovlya)", "m²", "Tom"),
    ("Gips suvoq", "m²", "Ichki ta'mir"), ("Shpaklyovka", "m²", "Ichki ta'mir"),
    ("Laminat yotqizish", "m²", "Pol"), ("Gipsokarton montaj", "m²", "Ichki ta'mir"),
    ("Oboy yopishtirish", "m²", "Ichki ta'mir"), ("Kafel terish", "m²", "Ichki ta'mir"),
    ("Santexnika ishlari", "nuqta", "Muhandislik"), ("Elektrika ishlari", "nuqta", "Muhandislik"),
]

def money(value):
    return f"{float(value or 0):,.0f}".replace(",", " ") + " so'm"

def get_projects():
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM projects ORDER BY id DESC"
        ).fetchall()

        return [dict(row) for row in rows]

def get_project_totals(project_id):
    with db() as conn:
        work_total = conn.execute(
            "SELECT COALESCE(SUM(quantity*unit_price),0) AS v FROM works WHERE project_id=?",
            (project_id,)
        ).fetchone()["v"]
        income = conn.execute(
            "SELECT COALESCE(SUM(amount),0) AS v FROM transactions WHERE project_id=? AND kind='Kirim'",
            (project_id,)
        ).fetchone()["v"]
        expense = conn.execute(
            "SELECT COALESCE(SUM(amount),0) AS v FROM transactions WHERE project_id=? AND kind='Chiqim'",
            (project_id,)
        ).fetchone()["v"]
    return float(work_total), int(income), int(expense)

def page_header(eyebrow, title, desc):
    st.markdown(
        f"<div class='page-eyebrow'>{eyebrow}</div><div class='page-title'>{title}</div>"
        f"<div class='page-desc'>{desc}</div>", unsafe_allow_html=True
    )

def metric(label, value, note, icon):
    st.markdown(
        f"""<div class="metric-card"><div style="display:flex;justify-content:space-between;align-items:center">
        <div class="metric-label">{label}</div><div style="font-size:21px">{icon}</div></div>
        <div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>""",
        unsafe_allow_html=True
    )

def load_works(project_id):
    with db() as conn:
        return conn.execute("SELECT * FROM works WHERE project_id=? ORDER BY id DESC", (project_id,)).fetchall()

def load_transactions(project_id):
    with db() as conn:
        return conn.execute("SELECT * FROM transactions WHERE project_id=? ORDER BY txn_date DESC,id DESC", (project_id,)).fetchall()

# ------------------------- AUTH ------------------------------
if "user" not in st.session_state:
    st.session_state.user = None

def login_screen():
    st.markdown("<div class='login-wrap'>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;font-size:42px'>🏗️</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;color:#13213a;margin-bottom:4px'>Prorab Abdulla</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#64748b;margin-bottom:25px'>Qurilish va smeta boshqaruv tizimi</p>", unsafe_allow_html=True)
    with st.form("login_form"):
        username = st.text_input("Login", placeholder="Loginni kiriting")
        password = st.text_input("Parol", type="password", placeholder="Parolni kiriting")
        submitted = st.form_submit_button("Tizimga kirish", use_container_width=True, type="primary")
    if submitted:
        with db() as conn:
            user = conn.execute("SELECT * FROM users WHERE username=? AND active=1", (username.strip(),)).fetchone()
        if user and verify_password(password, user["password_hash"]):
            st.session_state.user = dict(user)
            st.rerun()
        else:
            st.error("Login yoki parol noto'g'ri.")
    st.markdown("<hr><p style='font-size:12px;color:#94a3b8;text-align:center'>Xavfsiz kirish • Qurilish nazorati • Moliyaviy hisobot</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    with st.expander("Birinchi kirish uchun ma'lumot"):
        st.warning("Admin: login `admin`, parol `Admin123!`. Birinchi kirishda parolni albatta almashtiring. Namuna usta: `usta1` / `Usta111!`.")

if st.session_state.user is None:
    login_screen()
    st.stop()

user = st.session_state.user
is_admin = user["role"] == "admin"

# ------------------------- SIDEBAR ---------------------------
with st.sidebar:
    st.markdown("""<div class="brand"><div class="brand-icon">🏗️</div>
    <div><div class="brand-title">PRORAB ABDULLA</div><div class="brand-sub">QURILISH BOSHQARUV TIZIMI</div></div></div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f"**{user['full_name']}**")
    st.caption("Administrator" if is_admin else "Usta kabineti")
    st.markdown("---")
    if is_admin:
        nav = st.radio("ASOSIY MENYU", ["Umumiy panel", "Obyektlar", "Smeta va ishlar", "Kirim / Chiqim", "Foydalanuvchilar", "Hisobotlar", "Sozlamalar"], label_visibility="visible")
    else:
        nav = st.radio("ASOSIY MENYU", ["Mening obyektim", "Smeta va ishlar", "Kirim / Chiqim", "Hisobotlar"], label_visibility="visible")
    st.markdown("---")
    st.caption(f"Bugun: {date.today().strftime('%d.%m.%Y')}")
    if st.button("🚪 Tizimdan chiqish", use_container_width=True):
        st.session_state.user = None
        st.rerun()

# ------------------------- PROJECT CONTEXT -------------------
projects = get_projects()
if not is_admin:
    projects = [p for p in projects if p["id"] == user["project_id"]]
if not projects:
    st.warning("Sizga biriktirilgan obyekt topilmadi. Administrator bilan bog'laning.")
    st.stop()

project_names = {p["id"]: p["name"] for p in projects}
if is_admin:
    default_pid = st.session_state.get("selected_project_id", projects[0]["id"])
    valid_ids = [p["id"] for p in projects]
    if default_pid not in valid_ids:
        default_pid = projects[0]["id"]
    chosen_name = st.selectbox("📍 Ishlanayotgan obyekt", [p["name"] for p in projects],
                               index=[p["id"] for p in projects].index(default_pid), key="project_picker")
    project = next(p for p in projects if p["name"] == chosen_name)
    st.session_state.selected_project_id = project["id"]
else:
    project = projects[0]
pid = project["id"]
work_total, income_total, expense_total = get_project_totals(pid)
balance = income_total - expense_total
remaining = work_total - income_total

# ------------------------- PAGES -----------------------------
if nav in ("Umumiy panel", "Mening obyektim"):
    page_header("BOSHQARUV MARKAZI", "Xush kelibsiz!", "Obyektlar, smeta va moliyaviy holatni bitta joydan nazorat qiling.")
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric("Jami smeta", money(work_total), "Kiritilgan ishlar qiymati", "📋")
    with c2: metric("Jami kirim", money(income_total), "Qabul qilingan mablag'", "💰")
    with c3: metric("Jami chiqim", money(expense_total), "Qayd etilgan xarajatlar", "💸")
    with c4: metric("Pul balansi", money(balance), "Kirim minus chiqim", "⚖️")
    st.write("")
    left, right = st.columns([1.35, 1])
    with left:
        st.markdown("<div class='panel'><div class='section-title'>📊 Obyekt moliyaviy holati</div><div class='muted'>Joriy obyekt bo'yicha asosiy ko'rsatkichlar</div>", unsafe_allow_html=True)
        df_chart = pd.DataFrame({"Ko'rsatkich": ["Kirim", "Chiqim", "Qolgan smeta"], "Summa": [income_total, expense_total, max(work_total-income_total,0)]})
        st.bar_chart(df_chart.set_index("Ko'rsatkich"), height=260)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='panel'><div class='section-title'>🏠 Obyekt ma'lumotlari</div>", unsafe_allow_html=True)
        st.markdown(f"**Nomi:** {project['name']}")
        st.markdown(f"**Manzil:** {project['address'] or 'Kiritilmagan'}")
        st.markdown(f"**Izoh:** {project['note'] or 'Yo‘q'}")
        st.markdown(f"**Smeta qoldig‘i:** {money(remaining)}")
        st.markdown("</div>", unsafe_allow_html=True)
    st.write("")
    st.markdown("#### 🕘 Oxirgi moliyaviy operatsiyalar")
    tx = load_transactions(pid)[:6]
    if tx:
        st.dataframe(pd.DataFrame([{"Sana": x["txn_date"], "Turi": x["kind"], "Izoh": x["note"], "Summa": money(x["amount"])} for x in tx]), use_container_width=True, hide_index=True)
    else:
        st.info("Hozircha moliyaviy operatsiyalar kiritilmagan.")

elif nav == "Obyektlar":
    page_header("LOYIHALARNI BOSHQARISH", "Obyektlar", "Qurilish obyektlarini qo'shing va har birini alohida nazorat qiling.")
    with st.expander("➕ Yangi obyekt qo'shish", expanded=False):
        with st.form("new_project"):
            name = st.text_input("Obyekt nomi *", placeholder="Masalan: 12-uy Yunusobod")
            address = st.text_input("Manzil", placeholder="Toshkent shahri...")
            note = st.text_area("Izoh", height=70)
            if st.form_submit_button("Obyektni saqlash", type="primary"):
                if not name.strip():
                    st.error("Obyekt nomini kiriting.")
                else:
                    try:
                        with db() as conn:
                            conn.execute("INSERT INTO projects(name,address,note,created_at) VALUES(?,?,?,?)",
                                         (name.strip(), address.strip(), note.strip(), datetime.now().isoformat(timespec="seconds")))
                        st.success("Obyekt muvaffaqiyatli qo'shildi.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Bunday nomdagi obyekt mavjud.")
    for p in get_projects():
        w, inc, exp = get_project_totals(p["id"])
        with st.container(border=True):
            a, b, c, d = st.columns([3, 1.4, 1.4, 1])
            a.markdown(f"**🏠 {p['name']}**")
            a.caption(p["address"] or "Manzil kiritilmagan")
            b.metric("Smeta", money(w))
            c.metric("Kirim", money(inc))
            d.metric("Chiqim", money(exp))
            with st.expander("Obyektni tahrirlash / o'chirish"):
                with st.form(f"edit_project_{p['id']}"):
                    new_name = st.text_input("Obyekt nomi", value=p["name"])
                    new_address = st.text_input("Manzil", value=p["address"] or "")
                    new_note = st.text_area("Izoh", value=p["note"] or "")
                    save = st.form_submit_button("O'zgarishlarni saqlash")
                if save:
                    try:
                        with db() as conn:
                            conn.execute("UPDATE projects SET name=?,address=?,note=? WHERE id=?",
                                         (new_name.strip(), new_address.strip(), new_note.strip(), p["id"]))
                        st.success("O'zgarishlar saqlandi."); st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Bu obyekt nomi band.")
                if st.button("Obyektni va unga tegishli yozuvlarni o'chirish", key=f"delete_project_{p['id']}", type="secondary"):
                    if len(get_projects()) == 1:
                        st.error("Oxirgi obyektni o'chirib bo'lmaydi.")
                    else:
                        with db() as conn:
                            conn.execute("DELETE FROM projects WHERE id=?", (p["id"],))
                            conn.execute("UPDATE users SET project_id=NULL WHERE project_id=?", (p["id"],))
                        st.warning("Obyekt o'chirildi."); st.rerun()

elif nav == "Smeta va ishlar":
    page_header("ISH HAJMI VA NARXLAR", "Smeta va bajarilgan ishlar", "Har bir ish turi, o'lchov birligi, hajmi va narxini boshqaring.")
    works = load_works(pid)
    total_qty = sum(float(x["quantity"]) for x in works)
    st.markdown(f"<div class='small-tag'>Jami {len(works)} ta ish turi</div> &nbsp; <span class='muted'>Smeta qiymati: <b>{money(work_total)}</b></span>", unsafe_allow_html=True)
    if is_admin:
        with st.expander("➕ Smetaga yangi ish qo'shish", expanded=False):
            with st.form("add_work"):
                catalog_labels = [f"{x[0]} · {x[1]} · {x[2]}" for x in WORK_CATALOG]
                selected = st.selectbox("Tayyor ish katalogi", catalog_labels)
                custom = st.checkbox("Ish nomini o'zim kiritaman")
                custom_name = st.text_input("Yangi ish nomi") if custom else ""
                category = st.text_input("Kategoriya", value=WORK_CATALOG[catalog_labels.index(selected)][2])
                unit = st.text_input("O'lchov birligi", value=WORK_CATALOG[catalog_labels.index(selected)][1])
                q1, q2 = st.columns(2)
                qty = q1.number_input("Ish hajmi", min_value=0.0, step=1.0, format="%.2f")
                price = q2.number_input("Birlik narxi (so'm)", min_value=0, step=1000)
                if st.form_submit_button("Smetaga qo'shish", type="primary"):
                    work_name = custom_name.strip() if custom else WORK_CATALOG[catalog_labels.index(selected)][0]
                    if not work_name or qty <= 0 or price <= 0:
                        st.error("Ish nomi, hajmi va narxi to'g'ri kiritilishi kerak.")
                    else:
                        with db() as conn:
                            conn.execute("""INSERT INTO works(project_id,category,name,unit,quantity,unit_price,created_at)
                                            VALUES(?,?,?,?,?,?,?)""",
                                         (pid, category.strip(), work_name, unit.strip(), qty, price, datetime.now().isoformat(timespec="seconds")))
                        st.success("Ish smetaga qo'shildi."); st.rerun()
    if works:
        rows = [{"№": i, "Kategoriya": x["category"], "Ish nomi": x["name"], "Birlik": x["unit"],
                 "Hajm": x["quantity"], "Birlik narxi": x["unit_price"], "Jami": x["quantity"]*x["unit_price"]}
                for i, x in enumerate(works, 1)]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                     column_config={"Hajm": st.column_config.NumberColumn(format="%.2f"),
                                    "Birlik narxi": st.column_config.NumberColumn(format="%d so'm"),
                                    "Jami": st.column_config.NumberColumn(format="%d so'm")})
        st.markdown(f"### Umumiy smeta: {money(work_total)}")
        if is_admin:
            with st.expander("✏️ Ishni tahrirlash yoki o'chirish"):
                choices = {f"{x['name']} | {x['quantity']} {x['unit']}": x for x in works}
                selected_label = st.selectbox("Ishni tanlang", list(choices))
                chosen = choices[selected_label]
                with st.form("edit_work"):
                    ename = st.text_input("Ish nomi", value=chosen["name"])
                    ecat = st.text_input("Kategoriya", value=chosen["category"])
                    eunit = st.text_input("Birlik", value=chosen["unit"])
                    ec1, ec2 = st.columns(2)
                    eqty = ec1.number_input("Hajm", min_value=0.0, value=float(chosen["quantity"]), step=1.0)
                    eprice = ec2.number_input("Birlik narxi", min_value=0, value=int(chosen["unit_price"]), step=1000)
                    update = st.form_submit_button("Saqlash")
                if update:
                    if not ename.strip() or eqty <= 0 or eprice <= 0:
                        st.error("Maydonlarni to'g'ri to'ldiring.")
                    else:
                        with db() as conn:
                            conn.execute("UPDATE works SET name=?,category=?,unit=?,quantity=?,unit_price=? WHERE id=?",
                                         (ename.strip(), ecat.strip(), eunit.strip(), eqty, eprice, chosen["id"]))
                        st.success("Ish yangilandi."); st.rerun()
                if st.button("Tanlangan ishni o'chirish", key="delete_work"):
                    with db() as conn:
                        conn.execute("DELETE FROM works WHERE id=?", (chosen["id"],))
                    st.warning("Ish o'chirildi."); st.rerun()
    else:
        st.info("Bu obyektga hali smeta ishlari kiritilmagan.")

elif nav == "Kirim / Chiqim":
    page_header("MOLIYAVIY NAZORAT", "Kirim va chiqimlar", "Pul harakatlarini sana va izoh bilan qayd eting. Kirim va chiqim alohida yuritiladi.")
    if is_admin:
        with st.expander("➕ Yangi moliyaviy operatsiya", expanded=True):
            with st.form("new_transaction"):
                t1, t2 = st.columns(2)
                kind = t1.selectbox("Operatsiya turi", ["Kirim", "Chiqim"])
                amount = t2.number_input("Summa (so'm)", min_value=0, step=100000)
                note = st.text_input("Izoh / Kimdan yoki kimga", placeholder="Masalan: Buyurtmachidan avans")
                txn_date = st.date_input("Sana", value=date.today())
                if st.form_submit_button("Operatsiyani saqlash", type="primary"):
                    if amount <= 0 or not note.strip():
                        st.error("Summa va izohni to'ldiring.")
                    else:
                        with db() as conn:
                            conn.execute("""INSERT INTO transactions(project_id,kind,amount,note,txn_date,created_at)
                                            VALUES(?,?,?,?,?,?)""",
                                         (pid, kind, int(amount), note.strip(), txn_date.isoformat(), datetime.now().isoformat(timespec="seconds")))
                        st.success("Operatsiya saqlandi."); st.rerun()
    else:
        st.info("Usta kabinetida moliyaviy yozuvlar ko'rish uchun ochiq. Yangi yozuvlarni administrator kiritadi.")
    c1, c2, c3 = st.columns(3)
    with c1: metric("Jami kirim", money(income_total), "Qabul qilingan mablag'", "🟢")
    with c2: metric("Jami chiqim", money(expense_total), "Sarflangan mablag'", "🔴")
    with c3: metric("Pul balansi", money(balance), "Kirim - chiqim", "⚖️")
    tx = load_transactions(pid)
    if tx:
        st.markdown("#### Operatsiyalar tarixi")
        df = pd.DataFrame([{"ID": x["id"], "Sana": x["txn_date"], "Turi": x["kind"], "Izoh": x["note"], "Summa (so'm)": x["amount"]} for x in tx])
        st.dataframe(df, use_container_width=True, hide_index=True)
        if is_admin:
            with st.expander("Operatsiyani o'chirish"):
                tx_map = {f"#{x['id']} · {x['txn_date']} · {x['kind']} · {money(x['amount'])}": x for x in tx}
                selected_tx = st.selectbox("O'chiriladigan yozuv", list(tx_map))
                if st.button("Tanlangan operatsiyani o'chirish"):
                    with db() as conn:
                        conn.execute("DELETE FROM transactions WHERE id=?", (tx_map[selected_tx]["id"],))
                    st.warning("Operatsiya o'chirildi."); st.rerun()
    else:
        st.info("Hozircha operatsiyalar yo'q.")

elif nav == "Foydalanuvchilar":
    page_header("KIRISH HUQUQLARI", "Foydalanuvchilar", "Administrator va obyekt ustalarining loginlarini boshqaring.")
    if is_admin:
        with st.expander("➕ Yangi usta hisobini yaratish", expanded=True):
            with st.form("new_user"):
                full_name = st.text_input("Ustaning ism-familiyasi")
                uname = st.text_input("Login")
                pword = st.text_input("Vaqtinchalik parol", type="password")
                project_choice = st.selectbox("Biriktiriladigan obyekt", projects, format_func=lambda x: x["name"])
                if st.form_submit_button("Foydalanuvchini yaratish", type="primary"):
                    if not full_name.strip() or not uname.strip() or len(pword) < 8:
                        st.error("Barcha maydonlarni to'ldiring. Parol kamida 8 belgidan iborat bo'lsin.")
                    else:
                        try:
                            with db() as conn:
                                conn.execute("INSERT INTO users(username,password_hash,role,project_id,full_name,created_at) VALUES(?,?,?,?,?,?)",
                                             (uname.strip(), hash_password(pword), "usta", project_choice["id"], full_name.strip(), datetime.now().isoformat(timespec="seconds")))
                            st.success("Usta hisobi yaratildi."); st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Bu login allaqachon ishlatilmoqda.")
        with db() as conn:
            users = conn.execute("""SELECT users.*, projects.name AS project_name FROM users
                                    LEFT JOIN projects ON users.project_id=projects.id ORDER BY users.id""").fetchall()
        st.dataframe(pd.DataFrame([{"Ism": x["full_name"], "Login": x["username"], "Rol": x["role"],
                                    "Obyekt": x["project_name"] or "-", "Holat": "Faol" if x["active"] else "Faol emas"} for x in users]),
                     use_container_width=True, hide_index=True)
        with st.expander("Usta parolini yangilash yoki hisobini bloklash"):
            staff = [x for x in users if x["role"] == "usta"]
            if staff:
                staff_map = {f"{x['full_name']} ({x['username']})": x for x in staff}
                chosen_staff = st.selectbox("Ustani tanlang", list(staff_map))
                staff_user = staff_map[chosen_staff]
                new_pass = st.text_input("Yangi parol (kamida 8 belgi)", type="password")
                if st.button("Parolni yangilash"):
                    if len(new_pass) < 8:
                        st.error("Parol kamida 8 belgidan iborat bo'lishi kerak.")
                    else:
                        with db() as conn:
                            conn.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(new_pass), staff_user["id"]))
                        st.success("Parol yangilandi."); st.rerun()
                if st.button("Faollik holatini almashtirish"):
                    with db() as conn:
                        conn.execute("UPDATE users SET active=? WHERE id=?", (0 if staff_user["active"] else 1, staff_user["id"]))
                    st.success("Foydalanuvchi holati yangilandi."); st.rerun()

elif nav == "Hisobotlar":
    page_header("TAHLIL VA EKSPORT", "Hisobotlar", "Smeta va moliyaviy yozuvlarni Excel dasturida ochiladigan CSV formatida yuklab oling.")
    works = load_works(pid)
    tx = load_transactions(pid)
    st.markdown("#### Smeta hisoboti")
    if works:
        wdf = pd.DataFrame([{"Kategoriya": x["category"], "Ish nomi": x["name"], "Birlik": x["unit"],
                             "Hajm": x["quantity"], "Birlik narxi": x["unit_price"],
                             "Jami summa": x["quantity"]*x["unit_price"]} for x in works])
        st.dataframe(wdf, use_container_width=True, hide_index=True)
        st.download_button("⬇️ Smeta hisobotini yuklab olish (CSV)",
                           wdf.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"smeta_{pid}_{date.today().isoformat()}.csv", mime="text/csv")
    else:
        st.info("Smeta ma'lumotlari yo'q.")
    st.markdown("#### Kirim / chiqim hisoboti")
    if tx:
        tdf = pd.DataFrame([{"Sana": x["txn_date"], "Turi": x["kind"], "Izoh": x["note"], "Summa": x["amount"]} for x in tx])
        st.dataframe(tdf, use_container_width=True, hide_index=True)
        st.download_button("⬇️ Moliyaviy hisobotni yuklab olish (CSV)",
                           tdf.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"moliyaviy_hisobot_{pid}_{date.today().isoformat()}.csv",
                           mime="text/csv")
    else:
        st.info("Moliyaviy yozuvlar yo'q.")
    st.markdown("#### Yakuniy ko'rsatkichlar")
    st.write(f"- Jami smeta: **{money(work_total)}**")
    st.write(f"- Jami kirim: **{money(income_total)}**")
    st.write(f"- Jami chiqim: **{money(expense_total)}**")
    st.write(f"- Pul balansi: **{money(balance)}**")
    st.write(f"- Smeta va kirim farqi: **{money(remaining)}**")

elif nav == "Sozlamalar":
    page_header("TIZIM XAVFSIZLIGI", "Sozlamalar", "Hisobingiz parolini yangilang va ma'lumotlar bazasi bo'yicha tavsiyalarni ko'ring.")
    with st.form("change_password"):
        old = st.text_input("Joriy parol", type="password")
        new = st.text_input("Yangi parol", type="password")
        confirm = st.text_input("Yangi parolni takrorlang", type="password")
        if st.form_submit_button("Parolni yangilash", type="primary"):
            with db() as conn:
                row = conn.execute("SELECT password_hash FROM users WHERE id=?", (user["id"],)).fetchone()
                if not verify_password(old, row["password_hash"]):
                    st.error("Joriy parol noto'g'ri.")
                elif len(new) < 8:
                    st.error("Yangi parol kamida 8 belgidan iborat bo'lsin.")
                elif new != confirm:
                    st.error("Yangi parollar bir xil emas.")
                else:
                    conn.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(new), user["id"]))
                    st.success("Parol muvaffaqiyatli yangilandi.")
    st.markdown("#### Ma'lumotlar xavfsizligi")
    st.info("Dastur ma'lumotlari `prorab_abdulla.db` SQLite faylida saqlanadi. Uni muntazam zaxiralang. Bepul hostinglarda disk doimiy saqlanishi kafolatlanmasligi mumkin.")
    st.warning("Hostingga joylashdan oldin standart admin va namuna usta parollarini almashtiring, namuna ma'lumotlarini o'chiring va HTTPS yoqilganini tekshiring.")

st.markdown("---")
st.markdown("<div style='text-align:center;color:#94a3b8;font-size:11px'>PRORAB ABDULLA · Qurilish va moliya boshqaruv tizimi</div>", unsafe_allow_html=True)
