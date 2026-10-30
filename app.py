import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# --- SAHIFA SOZLAMALARI ---
st.set_page_config(
    page_title="Prorab Abdulla - Excel Smeta Tizimi",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DIZAYN (EXCEL USLUBIDAGI JADVAL STILI) ---
st.markdown("""
    <style>
    .main {
        background-color: #f4f6f9;
    }
    .big-metric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        text-align: center;
        border-left: 5px solid #007bff;
    }
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        height: 2.8em;
        background-color: #007bff;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #0056b3;
    }
    </style>
""", unsafe_allow_html=True)

# --- MA'LUMOTLAR BAZASI ---
DATA_FILE = "qurilish_data.json"

def load_data():
    data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            data = {}

    if "admin" not in data:
        data["admin"] = {"username": "abdullaprorap", "password": "123"}

    if "xonadonlar" not in data or not data["xonadonlar"]:
        data["xonadonlar"] = {
            "1-Obyekt (Toshkent, Chilonzor rezidensiya)": {
                "usta_login": "usta1",
                "usta_password": "111",
                "avanslar": [],
                "ishlar": {
                    "Beton quyish (Fundament)": {"mintaqa": "Karkas", "birlik": "m³", "hajm": 45.0, "narx": 150000},
                    "Pishgan g'isht terish": {"mintaqa": "Devor", "birlik": "dona", "hajm": 12000.0, "narx": 300}
                }
            }
        }
        save_data(data)

    return data

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Saqlashda xatolik: {e}")

# --- ISHLAR KATALOGI ---
DEFAULT_WORKS = [
    ("Beton quyish", "m³", "Karkas"),
    ("Padushka quyish", "m³", "Karkas"),
    ("Rigel / Kolonna", "m³", "Karkas"),
    ("Seysmopoyas (Sesma)", "m³", "Karkas"),
    ("Pishgan g'isht terish", "dona", "Karkas"),
    ("Gazoblok terish", "dona", "Karkas"),
    ("Styajka quyish", "m²", "Karkas"),
    ("Monolit quyish", "m²", "Karkas"),
    ("Tsement suvoq", "m²", "Karkas"),
    ("Tom yevro (Krovlya)", "m²", "Karkas"),
    ("Rodband suvoq", "m²", "Ichki ta'mir"),
    ("Shpaklyovka", "m²", "Ichki ta'mir"),
    ("Laminat yotqizish", "m²", "Ichki ta'mir"),
    ("Gipsokarton montaj", "m²", "Ichki ta'mir"),
    ("Oboy yopishtirish", "m²", "Ichki ta'mir"),
    ("Kafel/Kafelmangal", "m²", "Ichki ta'mir"),
    ("Santexnika ishlari", "tochka", "Ichki ta'mir"),
    ("Elektrika ishlari", "tochka", "Ichki ta'mir")
]

if 'user' not in st.session_state:
    st.session_state.user = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'assigned_house' not in st.session_state:
    st.session_state.assigned_house = None

db_data = load_data()

def login(username, password):
    if username == db_data["admin"]["username"] and password == db_data["admin"]["password"]:
        st.session_state.user = username
        st.session_state.role = "admin"
        st.session_state.assigned_house = "ALL"
        st.success("Xush kelibsiz, Prorab Abdulla!")
        st.rerun()
        return

    for house_name, house_info in db_data["xonadonlar"].items():
        if house_info.get("usta_login") == username and house_info.get("usta_password") == password:
            st.session_state.user = username
            st.session_state.role = "usta"
            st.session_state.assigned_house = house_name
            st.success(f"Xush kelibsiz! Obyekt: {house_name}")
            st.rerun()
            return
            
    st.error("Login yoki parol noto'g'ri!")

def logout():
    st.session_state.user = None
    st.session_state.role = None
    st.session_state.assigned_house = None
    st.rerun()

# --- LOGIN OYNASI ---
if st.session_state.user is None:
    st.markdown("<h1 style='text-align: center; color: #1e3d59;'>🏗️ PRORAB ABDULLA</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #555;'>Qurilish va Ta'mirlash Moliya va Smeta Tizimi</h4>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔑 Tizimga kirish")
        username_input = st.text_input("Login")
        password_input = st.text_input("Parol", type="password")
        
        if st.button("Kirish"):
            login(username_input, password_input)
            
    st.stop()

# --- SIDEBAR ---
st.sidebar.title("📌 Boshqaruv Paneli")
if st.session_state.role == "admin":
    st.sidebar.success("👤 **Prorab Abdulla** (Admin)")
else:
    st.sidebar.info(f"👷 Usta: **{st.session_state.user}**")
    st.sidebar.write(f"🏠 **Obyekt:** {st.session_state.assigned_house}")

if st.sidebar.button("🚪 Chiqish"):
    logout()

# ==========================================
# ADMIN & USTA EXCEL USLUBIDAGI ASOSIY INTERFEYS
# ==========================================
current_house = st.session_state.assigned_house

if st.session_state.role == "admin":
    xonadonlar = list(db_data["xonadonlar"].keys())
    if not xonadonlar:
        st.warning("Hozircha obyektlar yo'q. Yangi obyekt qo'shing.")
        selected_house = None
    else:
        selected_house = st.selectbox("📌 Boshqariladigan Obyektni Tanlang:", xonadonlar)
else:
    selected_house = current_house

if selected_house:
    house_data = db_data["xonadonlar"][selected_house]
    
    st.title(f"📊 Obyekt Moliya va Smeta Hisoboti: {selected_house}")
    
    ishlar = house_data.get("ishlar", {})
    avanslar_list = house_data.get("avanslar", [])
    
    # Hisob-kitoblar
    total_ish_sum = sum(i["hajm"] * i["narx"] for i in ishlar.values())
    total_avans_sum = sum(a["summa"] for a in avanslar_list)
    qolgan_qarz = total_ish_sum - total_avans_sum

    # --- KATTA-KATTA FINANSVIY METrikalar (EXCEL KABI KO'RINISH) ---
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("💰 Jami Bajarilgan Ishlar (Smeta)", f"{total_ish_sum:,.0f} so'm")
    col_m2.metric("💵 Jami Olingan / Berilgan Pullar", f"{total_avans_sum:,.0f} so'm")
    col_m3.metric("⚖️ Obyekt Balansi (Qoldiq Qarz)", f"{qolgan_qarz:,.0f} so'm")
    
    st.write("---")

    # Excel formatidagi jadval ko'rinishidagi tablar
    tab_jadval, tab_moliya, tab_sozlama = st.tabs(["📋 Ishlar Smetasi (Excel Jadval)", "💵 Pul va Avanslar Kitobi", "⚙️ Obyekt Sozlamalari"])

    with tab_jadval:
        st.subheader("🛠️ Obyektning Barcha Ishlar Jadvali")
        
        if st.session_state.role == "admin":
            with st.form("excel_add_work"):
                st.write("**➕ Jadvalga Yangi Ish Qo'shish**")
                c1, c2, c3 = st.columns([3, 1.5, 1.5])
                
                work_options = [f"{w[0]} ({w[1]})" for w in DEFAULT_WORKS]
                sel_w_str = c1.selectbox("Ish Turi", work_options)
                sel_tuple = next(w for w in DEFAULT_WORKS if f"{w[0]} ({w[1]})" == sel_w_str)
                
                h_val = c2.number_input("Hajmi", min_value=0.0, step=1.0)
                n_val = c3.number_input("Birlik Narxi (so'm)", min_value=0, step=1000)
                
                if st.form_submit_button("Jadvalga Qo'shish"):
                    if h_val > 0 and n_val > 0:
                        if "ishlar" not in house_data:
                            house_data["ishlar"] = {}
                        house_data["ishlar"][sel_tuple[0]] = {
                            "mintaqa": sel_tuple[2],
                            "birlik": sel_tuple[1],
                            "hajm": h_val,
                            "narx": n_val
                        }
                        save_data(db_data)
                        st.success("Muvaffaqiyatli qo'shildi!")
                        st.rerun()
                    else:
                        st.error("Hajm va narxni kiriting!")

        # Excel jadval ko'rinishi
        if not ishlar:
            st.info("Hozircha bu obyektda bajarilgan ishlar kiritilmagan.")
        else:
            table_rows = []
            for idx, (w_name, w_info) in enumerate(ishlar.items(), 1):
                h = w_info.get("hajm", 0)
                p = w_info.get("narx", 0)
                jami = h * p
                table_rows.append({
                    "№": idx,
                    "Kategoriya": w_info.get("mintaqa", "-"),
                    "Ish Nomi": w_name,
                    "O'lchov Birligi": w_info.get("birlik", "-"),
                    "Bajarilgan Hajm": f"{h:,.1f}",
                    "Birlik Narxi (so'm)": f"{p:,.0f}",
                    "Jami Summa (so'm)": f"{jami:,.0f}"
                })
            
            df_excel = pd.DataFrame(table_rows)
            st.dataframe(df_excel, use_container_width=True, hide_index=True)

            if st.session_state.role == "admin" and ishlar:
                del_w = st.selectbox("Jadvaldan o'chiriladigan ishni tanlang:", list(ishlar.keys()))
                if st.button("Tanlangan Ishni O'chirish"):
                    del house_data["ishlar"][del_w]
                    save_data(db_data)
                    st.warning("Ish o'chirildi!")
                    st.rerun()

    with tab_moliya:
        st.subheader("💵 Olingan Pullar va Avanslar Hisob-Kitobi")
        
        if st.session_state.role == "admin":
            with st.form("excel_add_avans"):
                st.write("**➕ Yangi Pul Qabul qilish / Avans kiritish**")
                ac1, ac2 = st.columns([2, 2])
                sum_v = ac1.number_input("Summa (so'm)", min_value=0.0, step=100000.0)
                izoh_v = ac2.text_input("Pulning Maqsadi / Kimdan olindi", placeholder="Masalan: Uy egasidan naqd pul avans")
                
                if st.form_submit_button("Pulni Hisobga Qo'shish"):
                    if sum_v > 0 and izoh_v.strip():
                        if "avanslar" not in house_data:
                            house_data["avanslar"] = []
                        house_data["avanslar"].append({
                            "sana": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "izoh": izoh_v.strip(),
                            "summa": sum_v
                        })
                        save_data(db_data)
                        st.success("Pul muvaffaqiyatli saqlandi!")
                        st.rerun()
                    else:
                        st.error("Summa va izohni to'ldiring!")

        if not avanslar_list:
            st.info("Hozircha hech qanday pul yoki avans tarixi kiritilmagan.")
        else:
            avans_rows = []
            for idx, a in enumerate(avanslar_list, 1):
                avans_rows.append({
                    "№": idx,
                    "Sana va Vaqt": a.get("sana", "-"),
                    "Izoh / Maqsad": a.get("izoh", "-"),
                    "Olingan Summa (so'm)": f"{a.get('summa', 0):,.0f}"
                })
            df_avans_excel = pd.DataFrame(avans_rows)
            st.dataframe(df_avans_excel, use_container_width=True, hide_index=True)

            if st.session_state.role == "admin":
                del_a_idx = st.selectbox("O'chiriladigan qator raqamini tanlang:", range(1, len(avanslar_list) + 1))
                if st.button("Tanlangan Pul yozuvini O'chirish"):
                    del house_data["avanslar"][del_a_idx - 1]
                    save_data(db_data)
                    st.warning("Pul yozuvi o'chirildi!")
                    st.rerun()

    with tab_sozlama:
        if st.session_state.role == "admin":
            st.subheader("⚙️ Obyekt va Usta Parollarini Boshqarish")
            with st.form("update_house_creds"):
                u_log = st.text_input("Usta Logini", value=house_data.get("usta_login", ""))
                u_pas = st.text_input("Usta Paroli", value=house_data.get("usta_password", ""))
                if st.form_submit_button("Ma'lumotlarni Yangilash"):
                    house_data["usta_login"] = u_log
                    house_data["usta_password"] = u_pas
                    save_data(db_data)
                    st.success("Yangilandi!")
                    st.rerun()
        else:
            st.info("Siz faqat o'zingizga biriktirilgan obyekt ma'lumotlarini ko'ra olasiz.")

# Admin uchun yangi obyekt qo'shish bo'limi
if st.session_state.role == "admin":
    st.write("---")
    with st.expander("➕ Yangi Katta Obyekt (Xonadon) Qo'shish"):
        with st.form("add_new_big_house"):
            hn = st.text_input("Obyekt Nomi (Masalan: 12-uy Yunusobod)")
            ul = st.text_input("Usta Uchun Login")
            up = st.text_input("Usta Uchun Parol", type="password")
            if st.form_submit_button("Obyektni Ochish"):
                if hn and ul and up:
                    if hn in db_data["xonadonlar"]:
                        st.error("Bunday obyekt allaqachon mavjud!")
                    else:
                        db_data["xonadonlar"][hn] = {
                            "usta_login": ul,
                            "usta_password": up,
                            "avanslar": [],
                            "ishlar": {}
                        }
                        save_data(db_data)
                        st.success("Yangi obyekt ochildi!")
                        st.rerun()
                else:
                    st.error("Barcha maydonlarni to'ldiring!")
