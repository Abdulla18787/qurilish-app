import streamlit as st
import pandas as pd
import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

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
    </style>
""", unsafe_allow_html=True)

# --- GOOGLE SHEETS ULANISHI ---
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_gspread_client():
    creds_dict = dict(st.secrets["gcp_service_account"])
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
    credentials = Credentials.from_service_account_info(
        creds_dict,
        scopes=SCOPE
    )
    return gspread.authorize(credentials)

def load_data():
    try:
        gc = get_gspread_client()
        sh = gc.open_by_key(st.secrets["SPREADSHEET_ID"])
        worksheet = sh.sheet1
        
        cell_value = worksheet.acell('A1').value
        if cell_value:
            data = json.loads(cell_value)
        else:
            data = {}
    except Exception as e:
        data = {}

    default_admin = {"username": "abdullaprorap", "password": "123"}
    data["admin"] = default_admin

    if "xonadonlar" not in data:
        data["xonadonlar"] = {
            "1-xonadon (Toshkent, Chilonzor)": {
                "usta_login": "usta1",
                "usta_password": "111",
                "avanslar": [],
                "ishlar": {
                    "Beton quyish": {"mintaqa": "Karkas", "birlik": "m³", "hajm": 15.0, "narx": 15000}
                }
            }
        }
        save_data(data)

    return data

def save_data(data):
    try:
        gc = get_gspread_client()
        sh = gc.open_by_key(st.secrets["SPREADSHEET_ID"])
        worksheet = sh.sheet1
        json_string = json.dumps(data, ensure_ascii=False)
        worksheet.update_acell('A1', json_string)
    except Exception as e:
        st.error(f"Google Sheets'ga saqlashda xatolik: {e}")

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

# --- AUTENTIFIKATSIYA ---
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
# SIDEBAR
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
    
    st.title(f"🏠 Smeta va Hisobot: {house_name}")
    st.info("🔒 Siz faqat o'zingizga tegishli xonadon smetasini ko'ra olasiz. O'zgartirish huquqi Prorab Abdullada.")

    tab_u1, tab_u2 = st.tabs(["📋 Qilingan Ishlar Smetasi", "💵 Avanslar va To'lovlar Tarixi"])

    ishlar = house_data.get("ishlar", {})
    avanslar_list = house_data.get("avanslar", [])
    
    total_ish_sum = sum(i["hajm"] * i["narx"] for i in ishlar.values())
    total_avans_sum = sum(a["summa"] for a in avanslar_list)
    qolgan_summa = total_ish_sum - total_avans_sum

    with tab_u1:
        if not ishlar:
            st.warning("Ushbu xonadonga hali ishlar biriktirilmagan.")
        else:
            table_data = []
            for ish_nomi, info in ishlar.items():
                hajm = info.get("hajm", 0)
                narx = info.get("narx", 0)
                jami = hajm * narx
                
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

    with tab_u2:
        if not avanslar_list:
            st.info("Hozircha hech qanday avans yoki to'lov berilmagan.")
        else:
            avans_rows = []
            for idx, a in enumerate(avanslar_list, 1):
                avans_rows.append({
                    "№": idx,
                    "Sana va Vaqt": a.get("sana", "-"),
                    "Berilish Sababi / Izoh": a.get("izoh", "-"),
                    "Berilgan Summa (so'm)": f"{a.get('summa', 0):,.0f}"
                })
            df_avans = pd.DataFrame(avans_rows)
            st.dataframe(df_avans, use_container_width=True, hide_index=True)

    st.write("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Umumiy Bajarilgan Ishlar", f"{total_ish_sum:,.0f} so'm")
    m2.metric("💵 Barcha Berilgan Avanslar", f"{total_avans_sum:,.0f} so'm")
    m3.metric("⚖️ Qolgan Qarzdorlik", f"{qolgan_summa:,.0f} so'm")


# ==========================================
# 3. PRORAB ABDULLA (ADMIN PANELI)
# ==========================================
if st.session_state.role == "admin":
    st.title("👷‍♂️ Prorab Abdulla - Boshqaruv Paneli")
    
    tab1, tab2 = st.tabs(["📊 Xonadonlar va Smetalar", "➕ Yangi Xonadon Qo'shish"])
    
    with tab1:
        xonadonlar = list(db_data["xonadonlar"].keys())
        
        if not xonadonlar:
            st.warning("Hozircha hech qanday xonadon mavjud emas. Yangi xonadon qo'shing.")
        else:
            selected_house = st.selectbox("📌 Xonadonni (Obyektni) tanlang:", xonadonlar)
            
            if selected_house:
                house_info = db_data["xonadonlar"][selected_house]
                
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
                
                sub_tab1, sub_tab2 = st.tabs(["🛠️ Ishlar va Smeta", "💵 Avanslar Boshqaruvi"])
                
                with sub_tab1:
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

                    ishlar = house_info.get("ishlar", {})
                    if ishlar:
                        st.write("### 📋 Joriy Smeta Jadvali")
                        table_rows = []
                        for w_name, w_data in ishlar.items():
                            tot = w_data["hajm"] * w_data["narx"]
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

                        st.write("**🗑️ Smetadan biror ishni o'chirish**")
                        del_work = st.selectbox("O'chiriladigan ishni tanlang:", list(ishlar.keys()))
                        if st.button("Ushbu Ishni Smetadan O'chirish"):
                            del db_data["xonadonlar"][selected_house]["ishlar"][del_work]
                            save_data(db_data)
                            st.warning(f"'{del_work}' smetadan o'chirildi!")
                            st.rerun()

                with sub_tab2:
                    st.write("### ➕ Yangi Avans / To'lov Berish")
                    with st.form("add_avans_form"):
                        col_a1, col_a2 = st.columns([2, 2])
                        avans_summa = col_a1.number_input("Berilgan Avans Summasi (so'm)", min_value=0.0, step=100000.0)
                        avans_izoh = col_a2.text_input("Nima uchun berildi (Izoh)", placeholder="Masalan: Sement va qum olishga")
                        
                        submit_avans = st.form_submit_button("Avansni Saqlash")
                        if submit_avans:
                            if avans_summa > 0 and avans_izoh.strip():
                                if "avanslar" not in db_data["xonadonlar"][selected_house]:
                                    db_data["xonadonlar"][selected_house]["avanslar"] = []
                                
                                hozirgi_vaqt = datetime.now().strftime("%Y-%m-%d %H:%M")
                                db_data["xonadonlar"][selected_house]["avanslar"].append({
                                    "sana": hozirgi_vaqt,
                                    "izoh": avans_izoh.strip(),
                                    "summa": avans_summa
                                })
                                save_data(db_data)
                                st.success("Yangi avans muvaffaqiyatli saqlandi!")
                                st.rerun()
                            else:
                                st.error("Summa va izohni to'liq kiriting!")

                    avanslar_list = house_info.get("avanslar", [])
                    if avanslar_list:
                        st.write("---")
                        st.write("### 📋 Berilgan Avanslar Tarixi")
                        
                        avans_rows_admin = []
                        for idx, a in enumerate(avanslar_list, 1):
                            avans_rows_admin.append({
                                "ID": idx,
                                "Sana va Vaqt": a.get("sana", "-"),
                                "Izoh / Maqsad": a.get("izoh", "-"),
                                "Summa (so'm)": f"{a.get('summa', 0):,.0f}"
                            })
                        
                        st.dataframe(pd.DataFrame(avans_rows_admin), use_container_width=True, hide_index=True)

                        st.write("**🗑️ Noto'g'ri yozilgan avansni o'chirish**")
                        del_idx = st.selectbox("O'chiriladigan avans tartib raqamini (ID) tanlang:", range(1, len(avanslar_list) + 1))
                        if st.button("Ushbu Avansni O'chirish"):
                            del db_data["xonadonlar"][selected_house]["avanslar"][del_idx - 1]
                            save_data(db_data)
                            st.warning("Avans tarixi o'chirildi!")
                            st.rerun()

                st.write("---")
                ishlar = house_info.get("ishlar", {})
                avanslar_list = house_info.get("avanslar", [])
                
                tot_ish = sum(i["hajm"] * i["narx"] for i in ishlar.values())
                tot_avans = sum(a["summa"] for a in avanslar_list)
                qolgan_qarz = tot_ish - tot_avans

                m1, m2, m3 = st.columns(3)
                m1.metric("💰 Umumiy Smeta Summasi", f"{tot_ish:,.0f} so'm")
                m2.metric("💵 Jami Berilgan Avanslar", f"{tot_avans:,.0f} so'm")
                m3.metric("⚖️ Qolgan Qarzdorlik (Uy egasi berishi kerak)", f"{qolgan_qarz:,.0f} so'm")

                st.write("---")
                with st.expander("⚠️ Obyektni (Xonadonni) butunlay o'chirish"):
                    st.error("Diqqat! Bu xonadonga tegishli barcha ma'lumotlar, avanslar tarixi va usta logini o'chib ketadi.")
                    if st.button(f"Xonadonni O'chirish ({selected_house})"):
                        del db_data["xonadonlar"][selected_house]
                        save_data(db_data)
                        st.success("Xonadon muvaffaqiyatli o'chirildi!")
                        st.rerun()

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
                            "avanslar": [],
                            "ishlar": {}
                        }
                        save_data(db_data)
                        st.success(f"'{h_name}' muvaffaqiyatli yaratildi va usta biriktirildi!")
                        st.rerun()
                else:
                    st.error("Iltimos, barcha maydonlarni to'liq to'ldiring!")
