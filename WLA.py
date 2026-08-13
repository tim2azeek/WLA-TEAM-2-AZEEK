import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. KONFIGURASI HALAMAN STREAMLIT
# ==========================================
st.set_page_config(
    page_title="DSS Analisis Beban Kerja & Tenaga Kerja",
    page_icon="📊",
    layout="wide"
)

# Custom CSS styling
st.markdown("""
    <style>
    .main-header {
        font-size: 24px;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #F3F4F6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #3B82F6;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-header'>Sistem Pendukung Keputusan Analisis Beban Kerja & Optimasi Kebutuhan Tenaga Kerja</div>", unsafe_allow_html=True)
st.caption("Metode: Time Study & Workload Analysis (WLA) | Powered by Streamlit")

# ==========================================
# 2. SIDEBAR - PARAMETER & INPUT DATA
# ==========================================
st.sidebar.header("⚙️ Parameter Operasional")

# Parameter Waktu Kerja
jam_kerja_shift = st.sidebar.number_input("Jam Kerja Per Shift (Jam)", min_value=1, max_value=12, value=8)
waktu_istirahat = st.sidebar.number_input("Waktu Istirahat (Menit)", min_value=0, max_value=120, value=60)

# Jam Kerja Efektif Tersedia (Menit)
jam_kerja_efektif = (jam_kerja_shift * 60) - waktu_istirahat
st.sidebar.info(f"⏱️ **Jam Kerja Efektif Tersedia:** {jam_kerja_efektif} menit/shift")

# Parameter Threshold WLA (%)
st.sidebar.subheader("🎯 Threshold WLA (%)")
threshold_underload = st.sidebar.number_input("Batas Maksimal Underload (%)", value=85.0)
threshold_overload = st.sidebar.number_input("Batas Minimal Overload (%)", value=110.0)

# Mode Input Data
st.sidebar.subheader("📂 Sumber Data")
data_source = st.sidebar.radio("Pilih Sumber Data:", ["Gunakan Data Dummy (Default)", "Unggah File CSV/Excel"])

# ==========================================
# 3. LOAD DATASET
# ==========================================
if data_source == "Gunakan Data Dummy (Default)":
    # Data contoh untuk simulasi
    df_input = pd.DataFrame({
        "Operator": ["Operator A", "Operator B", "Operator C", "Operator D", "Operator E"],
        "Stasiun_Kerja": ["Pemotongan", "Perakitan 1", "Perakitan 2", "Pengecekan (QC)", "Pengemasan"],
        "Waktu_Siklus_Menit": [3.2, 4.5, 2.8, 1.5, 2.0],
        "Rating_Factor": [1.10, 1.05, 1.00, 0.95, 1.00],  # Faktor penyesuaian (Westing House / Performance Rating)
        "Allowance_Percent": [15.0, 12.0, 15.0, 10.0, 12.0], # Kelonggaran (%)
        "Target_Output_Unit": [150, 150, 150, 150, 150]
    })
else:
    uploaded_file = st.sidebar.file_uploader("Unggah File (CSV atau XLSX)", type=["csv", "xlsx"])
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            df_input = pd.read_csv(uploaded_file)
        else:
            df_input = pd.read_excel(uploaded_file)
    else:
        st.warning("Silakan unggah file dataset terlebih dahulu. Menampilkan data template sementara:")
        df_input = pd.DataFrame({
            "Operator": ["Op 1"], "Stasiun_Kerja": ["Stasiun 1"],
            "Waktu_Siklus_Menit": [2.0], "Rating_Factor": [1.0],
            "Allowance_Percent": [10.0], "Target_Output_Unit": [100]
        })

# ==========================================
# 4. KALKULASI TIME STUDY & WLA (BACKEND)
# ==========================================
# 1. Waktu Normal = Waktu Siklus * Rating Factor
df_input["Waktu_Normal_Menit"] = df_input["Waktu_Siklus_Menit"] * df_input["Rating_Factor"]

# 2. Waktu Baku = Waktu Normal * (1 + % Allowance)
df_input["Waktu_Baku_Menit"] = df_input["Waktu_Normal_Menit"] * (1 + (df_input["Allowance_Percent"] / 100))

# 3. Total Waktu Kerja Efektif = Waktu Baku * Target Output
df_input["Total_Waktu_Kerja_Menit"] = df_input["Waktu_Baku_Menit"] * df_input["Target_Output_Unit"]

# 4. % Workload Analysis (% WLA)
df_input["Percent_WLA"] = (df_input["Total_Waktu_Kerja_Menit"] / jam_kerja_efektif) * 100

# 5. Kategori Beban Kerja
def kategorisasi_wla(val):
    if val < threshold_underload:
        return "Underload"
    elif val > threshold_overload:
        return "Overload"
    else:
        return "Normal"

df_input["Kategori_WLA"] = df_input["Percent_WLA"].apply(kategorisasi_wla)

# ==========================================
# 5. TAMPILAN DASHBOARD (FRONTEND)
# ==========================================

# TAB NAVIGATION
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Data Input & Time Study", 
    "📊 Visualisasi Beban Kerja", 
    "⚖️ Analisis Kebutuhan Staff", 
    "🎯 Rekomendasi DSS"
])

# ------------------------------------------
# TAB 1: DATA INPUT & TIME STUDY
# ------------------------------------------
with tab1:
    st.subheader("Tabel Perhitungan Time Study dan Jam Kerja Efektif")
    st.dataframe(df_input.style.format({
        "Waktu_Siklus_Menit": "{:.2f}",
        "Waktu_Normal_Menit": "{:.2f}",
        "Waktu_Baku_Menit": "{:.2f}",
        "Total_Waktu_Kerja_Menit": "{:.2f}",
        "Percent_WLA": "{:.2f}%"
    }), use_container_width=True)
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total Operator Dieskisting", f"{len(df_input)} Orang")
    col_b.metric("Rata-rata % WLA Tim", f"{df_input['Percent_WLA'].mean():.2f}%")
    col_c.metric("Total Waktu Kerja Diperlukan", f"{df_input['Total_Waktu_Kerja_Menit'].sum():.2f} Menit")

# ------------------------------------------
# TAB 2: VISUALISASI BEBAN KERJA (TUJUAN 1 & 2)
# ------------------------------------------
with tab2:
    st.subheader("Visualisasi Kondisi Beban Kerja per Operator")
    
    # Color Map
    color_map = {"Underload": "#FBBF24", "Normal": "#10B981", "Overload": "#EF4444"}
    
    # Bar Chart % WLA per Operator
    fig_bar = px.bar(
        df_input,
        x="Operator",
        y="Percent_WLA",
        color="Kategori_WLA",
        color_discrete_map=color_map,
        text=df_input["Percent_WLA"].apply(lambda x: f"{x:.1f}%"),
        title="Persentase Beban Kerja (% WLA) per Operator",
        hover_data=["Stasiun_Kerja", "Total_Waktu_Kerja_Menit"]
    )
    fig_bar.add_hline(y=threshold_underload, line_dash="dash", line_color="orange", annotation_text="Batas Underload")
    fig_bar.add_hline(y=threshold_overload, line_dash="dash", line_color="red", annotation_text="Batas Overload")
    fig_bar.update_layout(yaxis_title="% WLA", xaxis_title="Operator")
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # Pie Chart Distribusi Kategori
    col_pie1, col_pie2 = st.columns(2)
    with col_pie1:
        fig_pie = px.pie(
            df_input,
            names="Kategori_WLA",
            title="Proporsi Kategori Beban Kerja",
            color="Kategori_WLA",
            color_discrete_map=color_map
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col_pie2:
        st.markdown("### Ringkasan Status Operator")
        n_over = len(df_input[df_input["Kategori_WLA"] == "Overload"])
        n_norm = len(df_input[df_input["Kategori_WLA"] == "Normal"])
        n_under = len(df_input[df_input["Kategori_WLA"] == "Underload"])
        
        st.error(f"🔴 **Overload:** {n_over} Operator")
        st.success(f"🟢 **Normal:** {n_norm} Operator")
        st.warning(f"🟡 **Underload:** {n_under} Operator")

# ------------------------------------------
# TAB 3: OPTIMASI KEBUTUHAN STAFF (TUJUAN 3)
# ------------------------------------------
with tab3:
    st.subheader("Penentuan Kebutuhan Tenaga Kerja Optimal")
    
    total_waktu_butuh = df_input["Total_Waktu_Kerja_Menit"].sum()
    staff_eksisting = len(df_input)
    
    # Kalkulasi Teoritis Jumlah Staff = Total Waktu Butuh / Jam Kerja Efektif
    staff_teoritis = total_waktu_butuh / jam_kerja_efektif
    staff_optimal = int(np.ceil(staff_teoritis)) # Pembulatan ke atas
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Jumlah Staff Eksisting", f"{staff_eksisting} Orang")
    col2.metric("Kebutuhan Staff (Teoritis)", f"{staff_teoritis:.2f} Orang")
    col3.metric("Kebutuhan Staff Optimal (Pembulatan)", f"{staff_optimal} Orang")
    
    st.markdown("---")
    st.markdown("### Detail Kebutuhan Staff per Stasiun Kerja")
    
    df_stasiun = df_input.groupby("Stasiun_Kerja").agg({
        "Total_Waktu_Kerja_Menit": "sum",
        "Operator": "count"
    }).reset_index()
    
    df_stasiun.rename(columns={"Operator": "Staff_Eksisting"}, inplace=True)
    df_stasiun["Staff_Ideal_Teoritis"] = df_stasiun["Total_Waktu_Kerja_Menit"] / jam_kerja_efektif
    df_stasiun["Staff_Ideal_Pembulatan"] = df_stasiun["Staff_Ideal_Teoritis"].apply(lambda x: int(np.ceil(x)))
    df_stasiun["Selisih_Staff"] = df_stasiun["Staff_Ideal_Pembulatan"] - df_stasiun["Staff_Eksisting"]
    
    st.dataframe(df_stasiun.style.format({
        "Total_Waktu_Kerja_Menit": "{:.2f}",
        "Staff_Ideal_Teoritis": "{:.2f}"
    }), use_container_width=True)

# ------------------------------------------
# TAB 4: REKOMENDASI DSS (TUJUAN 4)
# ------------------------------------------
with tab4:
    st.subheader("🎯 Rekomendasi Perencanaan & Pengalokasian Tenaga Kerja")
    
    selisih_total = staff_optimal - staff_eksisting
    has_overload = len(df_input[df_input["Kategori_WLA"] == "Overload"]) > 0
    has_underload = len(df_input[df_input["Kategori_WLA"] == "Underload"]) > 0
    
    # SKENARIO REKOMENDASI DSS (LOGIKA 2-STEP)
    if has_overload and has_underload and selisih_total == 0:
        st.info("💡 **Rekomendasi Utama: REDISTRIBUSI BEBAN KERJA (REBALANCING)**")
        st.write("""
        * **Status Kapasitas:** Total jumlah tenaga kerja saat ini **CUKUP** secara kapasitas kuantitatif.
        * **Permasalahan:** Terjadi ketimpangan alokasi tugas (*Workload Imbalance*). Terdapat operator yang *Overload* dan operator lain yang *Underload*.
        * **Aksi Strategis:**
          1. Lakukan pengalihan sebagian elemen pekerjaan dari stasiun kerja/operator *Overload* ke operator *Underload*.
          2. Terapkan rotasi kerja (*job rotation*) berkala untuk mengurangi kelelahan fisik berturut-turut pada stasiun tinggi beban.
          3. Tidak diperlukan penambahan atau pengurangan tenaga kerja baru (*Headcount Tetap*).
        """)
        
    elif selisih_total > 0:
        st.error(f"⚠️ **Rekomendasi Utama: PENAMBAHAN TENAGA KERJA (UNDERSTAFFED)**")
        st.write(f"""
        * **Status Kapasitas:** Total beban kerja melebihi kapasitas jam kerja efektif seluruh tim.
        * **Permasalahan:** Terjadi *Understaffing*. Penyeimbangan tugas internal tidak lagi cukup untuk menekan % WLA ke rentang normal.
        * **Aksi Strategis:**
          1. Diperlukan **penambahan {selisih_total} orang tenaga kerja baru** pada stasiun kerja yang mengalami *Overload* tinggi.
          2. Sebagai solusi jangka pendek, dapat diberlakukan skema **jam kerja lembur (overtime)** terbatas.
        """)
        
    elif selisih_total < 0:
        st.warning(f"⚠️ **Rekomendasi Utama: EFISIENSI / EFISIENSI ALOKASI (OVERSTAFFED)**")
        st.write(f"""
        * **Status Kapasitas:** Kapasitas tenaga kerja saat ini berlebih dibanding total beban target produksi.
        * **Permasalahan:** Terjadi *Overstaffing* yang memicu tingginya waktu menganggur (*idle time*) dan inefisiensi biaya operasional.
        * **Aksi Strategis:**
          1. Dapat dilakukan **pengurangan/dialokasikan {abs(selisih_total)} orang staff** ke lini/departemen lain yang membutuhkan.
          2. Menilai ulang target kapasitas produksi harian untuk meningkatkan pemanfaatan tenaga kerja.
        """)
    else:
        st.success("✅ **Rekomendasi Utama: PERTAHANKAN STRUKTUR ALOKASI EKSISTING**")
        st.write("""
        * **Status Kapasitas:** Seluruh operator berada pada rentang beban kerja normal dan seimbang.
        * **Aksi Strategis:** Pertahankan standar waktu baku dan lakukan pemantauan (*monitoring*) berkala melalui dashboard ini.
        """)

    st.markdown("---")
    st.caption("🔍 *Dashboard ini dikembangkan untuk mendukung pengambil keputusan (Decision Maker) dalam perencanaan tenaga kerja yang berkelanjutan.*")