import streamlit as st
import pandas as pd
import json
import os

# --- SAHIFA SOZLAMALARI ---
st.set_page_config(
    page_title="Prorab Abdulla - Qurilish Nazorati",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DIZAYN (CUSTOM CSS) ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #007bff;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #0056b3;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    .header-style {
        color: #1e3d59;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- MA'LUMOTLAR BAZASI (JSON FAYL) ---
DB_FILE = "qurilish_data.json"

def load_data():
    if not os.path.exists(DB_FILE):
        # Boshlang'ich namuna ma'lumotlar
        initial_data = {
            "admin": {"username": "abdullaprorap", "password": "123"},
            "xonadonlar": {
                "1-xonadon (Toshkent, Chilonzor)": {
                    "usta_login": "usta1",
                    "usta_password": "111",
                    "avans": 5000000,
                    "ishlar": {
                        "Beton quyish": {"mintaqa": "Karkas", "birlik": "m³", "hajm": 12.0, "narx": 250000},
                        "Pishgan g'isht terish": {"mintaqa": "Karkas", "birlik": "dona", "hajm": 5000.0, "narx": 1500},
                        "Rodband suvoq": {"mintaqa": "Ichki ta'mir", "birlik": "m²", "hajm": 150.0, "narx": 35000},
                        "Elektrika ishlari": {"mintaqa": "Ichki ta'mir", "birlik": "tochka", "hajm": 25.0, "narx": 50000}
                    }
                }
            }
        }
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=4)
        return initial_data
    
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- BARCHA ISHLAR KATALOGI ---
DEFAULT_WORKS = [
    # Noldan qurish (Karkas)
    ("Beton quyish", "m³", "Karkas"),
    ("Padushka quyish", "m³", "Karkas"),
    ("Rigel / Kolonna", "m³", "Karkas"),
    ("Seysmopoyas (Sesma)", "m³", "Karkas"),
    ("Peremichka", "m³", "Karkas"),
    ("Pishgan g'isht terish", "dona", "Karkas"),
    ("Plita o'rnatish", "dona", "Karkas"),
    ("Plita obvyazka", "m", "Karkas"),
    ("Seredeshnik", "m", "Karkas"),
    ("Lumboz", "m²", "Karkas"),
    ("Tom yevro (Krovlya)", "m²", "Karkas"),
    ("Slef o'rnatish", "m", "Karkas"),
    ("Transheya kovlash", "m³", "Karkas"),
    ("Gazoblok terish", "dona", "Karkas"),
    ("Shlakoblok terish", "dona", "Karkas"),
    ("Styajka quyish", "m²", "Karkas"),
    ("Monolit quyish", "m²", "Karkas"),
    ("Tsement suvoq", "m²", "Karkas"),
    
    # Ichki ta'mirlash
    ("Rodband suvoq", "m²", "Ichki ta'mir"),
    ("Shpaklyovka (Tyag/Glan)", "m²", "Ichki ta'mir"),
    ("Laminat yotqizish", "m²", "Ichki ta'mir"),
    ("Plintus o'rnatish", "m", "Ichki ta'mir"),
    ("Gipsokarton montaj", "m²", "Ichki ta'mir"),
    ("Emulsiya sepish/bo'yash", "m²", "Ichki ta'mir"),
    ("Oboy yopishtirish", "m²", "Ichki ta'mir"),
    ("PVX panel", "m²", "Ichki ta'mir"),
    ("Bambuk panel", "m²", "Ichki ta'mir"),
    ("Akfa eshik/rom o'rnatish", "dona", "Ichki ta'mir"),
    ("Santexnika ishlari", "tochka", "Ichki ta'mir"),
    ("Elektrika ishlari", "tochka", "Ichki ta'mir"),
    ("Lepka yopishtirish", "m", "Ichki ta'mir"),
    ("Rels/Parniz o'rnatish", "m", "Ichki ta'mir"),
    ("Kafel/Kafelmangal", "m²", "Ichki ta'mir"),
    ("Tyoply pol yotqizish", "m²", "Ichki ta'mir"),
    ("Malyarka ishlari", "m²", "Ichki ta'mir"),
    ("Eshik o'rnatish (Yog'och/MDX)", "dona", "Ichki ta'mir")
]

# --- SESSION STATE ---
if 'user' not in st.session_state:
    st.session_state.user = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'assigned_house' not in st.session_state:
    st.session_state.assigned_house = None

db_data = load_data()

# --- AUTENTIFIKATSIYA KIRD / CHIQ ---
def login(username, password):
    # Admin tekshirish
    if username == db_data["admin"]["username"] and password == db_data["admin"]["password"]:
        st.session_state.user = username
        st.session_state.role = "admin"
        st.session_state.assigned_house = "ALL"
        st.success("Xush kelibsiz, Prorab Abdulla!")
        st.rerun()
        return

    # Ustalarni tekshirish
    for house_name, house_info in db_data["xonadonlar"].items():
        if house_info.get("usta_login") == username and house_info.get("usta_password") == password:
            st.session_state.user = username
            st.session_state.role = "usta"
            st.session_state.assigned_house = house_name
            st.success(f"Xush kelibsiz! Tizimga kirdingiz: {house_name}")
            st.rerun()
            return
            
    st.error("Login yoki parol noto'g'ri!")

def logout():
    st.session_state.user = None
    st.session_state.role = None
    st.session_state.assigned_house = None
    st.rerun()

# ==========================================
# 1. LOGIN INTERFEYSI
# ==========================================
if st.session_state.user is None:
    st.markdown("<h1 style='text-align: center; color: #1e3d59;'>🏗️ PRORAB ABDULLA</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #555;'>Qurilish va Ta'mirlash Ishlarini Boshqarish Tizimi</h4>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔑 Tizimga kirish")
        username_input = st.text_input("Login")
        password_input = st.text_input("Parol", type="password")
        
        if st.button("Kirish"):
            login(username_input, password_input)
            
    st.stop()

# ==========================================
# SIDEBAR (PROFIL VA CHIQISH)
# ==========================================
st.sidebar.title("📌 Foydalanuvchi Profili")
if st.session_state.role == "admin":
    st.sidebar.success("👤 **Prorab Abdulla** (Admin)")
else:
    st.sidebar.info(f"👷 Usta: **{st.session_state.user}**")
    st.sidebar.write(f"🏠 **Obyekt:** {st.session_state.assigned_house}")

if st.sidebar.button("🚪 Chiqish"):
    logout()

# ==========================================
# 2. USTA PANELI (FAQAT KO'RISH)
# ==========================================
if st.session_state.role == "usta":
    house_name = st.session_state.assigned_house
    house_data = db_data["xonadonlar"].get(house_name, {})
    
    st.title(f"🏠 Smeta: {house_name}")
    st.info("🔒 Siz faqat o'zingizga tegishli xonadon smetasini ko'ra olasiz. O'zgartirish huquqi Prorab Abdullada.")

    ishlar = house_data.get("ishlar", {})
    
    if not ishlar:
        st.warning("Ushbu xonadonga hali ishlar biriktirilmagan.")
    else:
        table_data = []
        total_sum = 0
        
        for ish_nomi, info in ishlar.items():
            hajm = info.get("hajm", 0)
            narx = info.get("narx", 0)
            jami = hajm * narx
            total_sum += jami
            
            table_data.append({
                "Kategoriya": info.get("mintaqa", "-"),
                "Ish turi / Nomi": ish_nomi,
                "Birlik": info.get("birlik", "-"),
                "Bajarilgan Hajm": f"{hajm:,.1f}",
                "Birlik Narxi (so'm)": f"{narx:,.0f}",
                "Jami Summa (so'm)": f"{jami:,.0f}"
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        avans = house_data.get("avans", 0)
        qolgan_summa = total_sum - avans

        st.write("---")
        m1, m2, m3 = st.columns(3)
        m1.metric("💰 Umumiy Bajarilgan Ishlar", f"{total_sum:,.0f} so'm")
        m2.metric("💵 Berilgan Avans/To'lov", f"{avans:,.0f} so'm")
        m3.metric("⚖️ Qolgan Qarzdorlik", f"{qolgan_summa:,.0f} so'm")

# ==========================================
# 3. PRORAB ABDULLA (ADMIN PANELI)
# ==========================================
if st.session_state.role == "admin":
    st.title("👷‍♂️ Prorab Abdulla - Boshqaruv Paneli")
    
    tab1, tab2 = st.tabs(["📊 Xonadonlar va Smetalar", "➕ Yangi Xonadon Qo'shish"])
    
    # TAB 1: SMETALARNI BOSHQARISH
    with tab1:
        xonadonlar = list(db_data["xonadonlar"].keys())
        
        if not xonadonlar:
            st.warning("Hozircha hech qanday xonadon mavjud emas. Yangi xonadon qo'shing.")
        else:
            selected_house = st.selectbox("📌 Xonadonni (Obyektni) tanlang:", xonadonlar)
            
            if selected_house:
                house_info = db_data["xonadonlar"][selected_house]
                
                # Usta va Login ma'lumotlari
                with st.expander("🔑 Usta Kirish Ma'lumotlari (Tahrirlash)", expanded=False):
                    c1, c2 = st.columns(2)
                    new_u_login = c1.text_input("Usta Logini", value=house_info.get("usta_login", ""))
                    new_u_pass = c2.text_input("Usta Paroli", value=house_info.get("usta_password", ""))
                    if st.button("Usta Parolini Yangilash"):
                        db_data["xonadonlar"][selected_house]["usta_login"] = new_u_login
                        db_data["xonadonlar"][selected_house]["usta_password"] = new_u_pass
                        save_data(db_data)
                        st.success("Login va parol yangilandi!")

                st.write("---")
                st.subheader(f"🛠️ {selected_house} - Ishlar va Smetani Kirish")
                
                # ISH QO'SHISH FORMASI
                with st.form("add_work_form"):
                    st.write("**➕ Yangi Ish va Hajm Kirish**")
                    col_w1, col_w2, col_w3 = st.columns([3, 1.5, 1.5])
                    
                    work_options = [f"{w[0]} ({w[1]})" for w in DEFAULT_WORKS]
                    selected_work_str = col_w1.selectbox("Ish Turi", work_options)
                    
                    selected_work_tuple = next(w for w in DEFAULT_WORKS if f"{w[0]} ({w[1]})" == selected_work_str)
                    
                    hajm_val = col_w2.number_input("Hajmi (kv, m, dona, tochka)", min_value=0.0, step=0.5)
                    narx_val = col_w3.number_input("Birlik Narxi (so'm)", min_value=0, step=5000)
                    
                    submit_work = st.form_submit_button("Smetaga Qo'shish / Yangilash")
                    
                    if submit_work:
                        if hajm_val > 0 and narx_val > 0:
                            if "ishlar" not in db_data["xonadonlar"][selected_house]:
                                db_data["xonadonlar"][selected_house]["ishlar"] = {}
                                
                            db_data["xonadonlar"][selected_house]["ishlar"][selected_work_tuple[0]] = {
                                "mintaqa": selected_work_tuple[2],
                                "birlik": selected_work_tuple[1],
                                "hajm": hajm_val,
                                "narx": narx_val
                            }
                            save_data(db_data)
                            st.success(f"{selected_work_tuple[0]} smetaga qo'shildi!")
                            st.rerun()
                        else:
                            st.error("Hajm va Narx 0 dan katta bo'lishi kerak!")

                # JADVALNI KO'RSATISH
                ishlar = house_info.get("ishlar", {})
                if ishlar:
                    st.write("### 📋 Joriy Smeta Jadvali")
                    
                    total_sum = 0
                    table_rows = []
                    
                    for w_name, w_data in list(ishlar.items()):
                        tot = w_data["hajm"] * w_data["narx"]
                        total_sum += tot
                        table_rows.append({
                            "Ish Nomi": w_name,
                            "Kategoriya": w_data["mintaqa"],
                            "Birlik": w_data["birlik"],
                            "Hajm": w_data["hajm"],
                            "Narx (so'm)": w_data["narx"],
                            "Jami (so'm)": tot
                        })
                    
                    df_admin = pd.DataFrame(table_rows)
                    st.dataframe(df_admin, use_container_width=True)

                    # Avans tahrirlash
                    st.write("---")
                    ca1, ca2 = st.columns([2, 2])
                    current_avans = house_info.get("avans", 0)
                    new_avans = ca1.number_input("💵 Uy egasidan olingan Avans/To'lov summasi (so'm):", value=float(current_avans), step=500000.0)
                    
                    if ca2.button("Avansni Saqlash"):
                        db_data["xonadonlar"][selected_house]["avans"] = new_avans
                        save_data(db_data)
                        st.success("Avans summasi saqlandi!")
                        st.rerun()

                    # Moliya statistikasi
                    qolgan = total_sum - new_avans
                    m1, m2, m3 = st.columns(3)
                    m1.metric("💰 Umumiy Smeta Summasi", f"{total_sum:,.0f} so'm")
                    m2.metric("💵 Olingan Avans", f"{new_avans:,.0f} so'm")
                    m3.metric("⚖️ Qolgan Qarzdorlik", f"{qolgan:,.0f} so'm")
                    
                    # Ishni o'chirish
                    st.write("---")
                    st.write("**🗑️ Smetadan biror ishni o'chirish**")
                    del_work = st.selectbox("O'chiriladigan ishni tanlang:", list(ishlar.keys()))
                    if st.button("Ushbu Ishni Smetadan O'chirish"):
                        del db_data["xonadonlar"][selected_house]["ishlar"][del_work]
                        save_data(db_data)
                        st.warning(f"'{del_work}' smetadan o'chirildi!")
                        st.rerun()

                # XONADONNI BUTUNLAY O'CHIRISH
                st.write("---")
                with st.expander("⚠️ Obyektni (Xonadonni) butunlay o'chirish"):
                    st.error("Diqqat! Bu xonadonga tegishli barcha ma'lumotlar va usta logini o'chib ketadi.")
                    if st.button(f"Xonadonni O'chirish ({selected_house})"):
                        del db_data["xonadonlar"][selected_house]
                        save_data(db_data)
                        st.success("Xonadon muvaffaqiyatli o'chirildi!")
                        st.rerun()

    # TAB 2: YANGI XONADON QO'SHISH
    with tab2:
        st.subheader("➕ Yangi Xonadon (Obyekt) va Usta Kirishini Yaratish")
        
        with st.form("add_house_form"):
            h_name = st.text_input("Xonadon Nomi yoki Unikal Manzili (Masalan: 51-xonadon Yunusobod)")
            u_login = st.text_input("Ushbu xonadon ustasi uchun Login")
            u_pass = st.text_input("Ushbu xonadon ustasi uchun Parol")
            
            submit_house = st.form_submit_button("Xonadonni Tizimga Qo'shish")
            
            if submit_house:
                if h_name and u_login and u_pass:
                    if h_name in db_data["xonadonlar"]:
                        st.error("Bunday xonadon nomi allaqachon mavjud!")
                    else:
                        db_data["xonadonlar"][h_name] = {
                            "usta_login": u_login,
                            "usta_password": u_pass,
                            "avans": 0,
                            "ishlar": {}
                        }
                        save_data(db_data)
                        st.success(f"'{h_name}' muvaffaqiyatli yaratildi va usta biriktirildi!")
                        st.rerun()
                else:
                    st.error("Iltimos, barcha maydonlarni to'ldiring!")
