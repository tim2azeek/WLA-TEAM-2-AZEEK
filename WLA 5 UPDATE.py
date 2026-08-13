import io
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from fpdf import FPDF

# ==========================================
# 1. KONFIGURASI HALAMAN STREAMLIT
# ==========================================
st.set_page_config(
    page_title="DSS Analisis Beban Kerja Operator Lini",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    "<h2 style='text-align: center; color: #1E3A8A;'>Sistem Pendukung Keputusan"
    " Analisis Beban Kerja & Optimasi Tenaga Kerja</h2>",
    unsafe_allow_html=True,
)
st.caption(
    "<p style='text-align: center;'>Metode: Time Study & Workload Analysis (WLA)"
    " - Single Line Production</p>",
    unsafe_allow_html=True,
)


# ==========================================
# 2. FUNGSI GENERATOR LAPORAN PDF (FPDF2)
# ==========================================
def generate_pdf_report(
    status_rek, staff_eksis, staff_opt, biaya_lembur, df_final
):
  pdf = FPDF()
  pdf.add_page()

  # Header Laporan
  pdf.set_font("Helvetica", "B", 14)
  pdf.cell(
      190, 10, "LAPORAN REKOMENDASI DSS - ANALISIS BEBAN KERJA", ln=True, align="C"
  )
  pdf.set_font("Helvetica", "", 10)
  pdf.cell(
      190,
      8,
      "Sistem Pendukung Keputusan Berbasis WLA & Time Study",
      ln=True,
      align="C",
  )
  pdf.ln(5)

  # Ringkasan Keputusan
  pdf.set_font("Helvetica", "B", 11)
  pdf.cell(190, 8, "1. RINGKASAN REKOMENDASI STRATEGIS", ln=True)
  pdf.set_font("Helvetica", "", 10)
  pdf.multi_cell(190, 6, f"Status Rekomendasi : {status_rek}")
  pdf.cell(
      190, 6, f"Jumlah Operator Eksisting : {staff_eksis} Orang", ln=True
  )
  pdf.cell(190, 6, f"Kebutuhan Operator Optimal : {staff_opt} Orang", ln=True)
  pdf.cell(
      190,
      6,
      f"Estimasi Biaya Lembur Lini : Rp {biaya_lembur:,.0f} / shift",
      ln=True,
  )
  pdf.ln(6)

  # Tabel Ringkasan Operator
  pdf.set_font("Helvetica", "B", 11)
  pdf.cell(
      190, 8, "2. DETAIL BEBAN KERJA OPERATOR (PASCA SIMULASI)", ln=True
  )
  pdf.set_font("Helvetica", "B", 9)

  # Header Tabel
  pdf.cell(45, 8, "Operator", 1)
  pdf.cell(45, 8, "Total Waktu (Min)", 1)
  pdf.cell(45, 8, "% WLA", 1)
  pdf.cell(55, 8, "Status WLA", 1)
  pdf.ln()

  # Isi Tabel
  pdf.set_font("Helvetica", "", 9)
  for index, row in df_final.iterrows():
    pdf.cell(45, 8, str(row["Operator"]), 1)
    pdf.cell(45, 8, f"{row['Total_Waktu_Kerja_Menit']:.1f}", 1)
    pdf.cell(45, 8, f"{row['Percent_WLA']:.1f}%", 1)
    pdf.cell(55, 8, str(row["Kategori_WLA"]), 1)
    pdf.ln()

  return bytes(pdf.output())


# ==========================================
# 3. SIDEBAR - PARAMETER OPERASIONAL & BIAYA
# ==========================================
st.sidebar.header("⚙️ Parameter Operasional")

jam_kerja_shift = st.sidebar.number_input(
    "Jam Kerja Per Shift (Jam)", min_value=1, max_value=12, value=8
)
waktu_istirahat = st.sidebar.number_input(
    "Waktu Istirahat (Menit)", min_value=0, max_value=120, value=60
)

jam_kerja_efektif = (jam_kerja_shift * 60) - waktu_istirahat
st.sidebar.info(f"⏱️ **Jam Kerja Efektif:** {jam_kerja_efektif} menit/shift")

st.sidebar.subheader("🎯 Threshold WLA (%)")
threshold_underload = st.sidebar.number_input(
    "Batas Maksimal Underload (%)", value=85.0
)
threshold_overload = st.sidebar.number_input(
    "Batas Minimal Overload (%)", value=110.0
)

st.sidebar.subheader("💰 Parameter Finansial (Lembur)")
tarif_lembur_per_jam = st.sidebar.number_input(
    "Tarif Lembur Operator per Jam (Rp)",
    min_value=0,
    value=25000,
    step=5000,
)

st.sidebar.subheader("📂 Sumber Data")
data_source = st.sidebar.radio(
    "Pilih Sumber Data:",
    ["Gunakan Data Dummy (Default)", "Unggah File CSV/Excel"],
)

# ==========================================
# 4. LOAD DATASET EKSISTING
# ==========================================
if data_source == "Gunakan Data Dummy (Default)":
  df_input = pd.DataFrame({
      "Operator": [
          "Operator A",
          "Operator B",
          "Operator C",
          "Operator D",
          "Operator E",
      ],
      "Waktu_Siklus_Menit": [3.5, 4.8, 2.9, 1.4, 2.0],
      "Rating_Factor": [1.10, 1.05, 1.00, 0.95, 1.00],
      "Allowance_Percent": [15.0, 12.0, 15.0, 10.0, 12.0],
      "Target_Output_Unit": [150, 150, 150, 150, 150],
  })
else:
  uploaded_file = st.sidebar.file_uploader(
      "Unggah File (CSV atau XLSX)", type=["csv", "xlsx"]
  )
  st.sidebar.caption(
      "💡 **Format Kolom Excel:** `Operator`, `Waktu_Siklus_Menit`,"
      " `Rating_Factor`, `Allowance_Percent`, `Target_Output_Unit`"
  )

  if uploaded_file is not None:
    if uploaded_file.name.endswith(".csv"):
      df_input = pd.read_csv(uploaded_file)
    else:
      df_input = pd.read_excel(uploaded_file)
  else:
    st.warning(
        "Silakan unggah file dataset sesuai format kolom. Menampilkan data"
        " template sementara:"
    )
    df_input = pd.DataFrame({
        "Operator": ["Operator A"],
        "Waktu_Siklus_Menit": [2.0],
        "Rating_Factor": [1.0],
        "Allowance_Percent": [10.0],
        "Target_Output_Unit": [100],
    })

# ==========================================
# 5. KALKULASI TIME STUDY, WLA & FATIGUE RISK
# ==========================================
df_input["Waktu_Normal_Menit"] = (
    df_input["Waktu_Siklus_Menit"] * df_input["Rating_Factor"]
)
df_input["Waktu_Baku_Menit"] = df_input["Waktu_Normal_Menit"] * (
    1 + (df_input["Allowance_Percent"] / 100)
)
df_input["Total_Waktu_Kerja_Menit"] = (
    df_input["Waktu_Baku_Menit"] * df_input["Target_Output_Unit"]
)
df_input["Percent_WLA"] = (
    df_input["Total_Waktu_Kerja_Menit"] / jam_kerja_efektif
) * 100


def kategorisasi_wla(val):
  if val < threshold_underload:
    return "Underload"
  elif val > threshold_overload:
    return "Overload"
  else:
    return "Normal"


def indikator_fatigue(val):
  if val <= threshold_overload:
    return "🟢 Low Risk (Aman)"
  elif val <= 130.0:
    return "🟡 Moderate Risk (Kelelahan Sedang)"
  else:
    return "🔴 High Hazard Risk (Kelelahan Ekstrem)"


df_input["Kategori_WLA"] = df_input["Percent_WLA"].apply(kategorisasi_wla)
df_input["Fatigue_Risk"] = df_input["Percent_WLA"].apply(indikator_fatigue)

# ==========================================
# 6. TAMPILAN DASHBOARD (5 TAB STRATEGIS)
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Page 1: Data Time Study",
    "📊 Page 2: Visualisasi Beban Kerja",
    "🔄 Page 3: DSS Redistribusi Interaktif",
    "⚖️ Page 4: Analisis Kebutuhan Staff",
    "🎯 Page 5: Rekomendasi Akhir DSS",
])

# ------------------------------------------
# PAGE 1: DATA TIME STUDY & KALKULASI DASAR
# ------------------------------------------
with tab1:
  st.subheader(
      "📋 Perhitungan Time Study dan Jam Kerja Efektif Operator Lini"
  )
  st.dataframe(
      df_input.style.format({
          "Waktu_Siklus_Menit": "{:.2f}",
          "Waktu_Normal_Menit": "{:.2f}",
          "Waktu_Baku_Menit": "{:.2f}",
          "Total_Waktu_Kerja_Menit": "{:.2f}",
          "Percent_WLA": "{:.2f}%",
      }),
      use_container_width=True,
  )

  col_a, col_b, col_c = st.columns(3)
  col_a.metric("Total Operator Lini", f"{len(df_input)} Orang")
  col_b.metric("Rata-rata % WLA Lini", f"{df_input['Percent_WLA'].mean():.2f}%")
  col_c.metric(
      "Total Waktu Baku Diperlukan",
      f"{df_input['Total_Waktu_Kerja_Menit'].sum():.2f} Menit",
  )

# ------------------------------------------
# PAGE 2: VISUALISASI BEBAN KERJA & ERGONOMIC RISK
# ------------------------------------------
with tab2:
  st.subheader("📊 Visualisasi Beban Kerja & Risiko Ergonomi (Eksisting)")
  color_map = {
      "Underload": "#FBBF24",
      "Normal": "#10B981",
      "Overload": "#EF4444",
  }

  fig_bar = px.bar(
      df_input,
      x="Operator",
      y="Percent_WLA",
      color="Kategori_WLA",
      color_discrete_map=color_map,
      text=df_input["Percent_WLA"].apply(lambda x: f"{x:.1f}%"),
      title="Persentase Beban Kerja (% WLA) Eksisting per Operator",
  )
  fig_bar.add_hline(
      y=threshold_underload,
      line_dash="dash",
      line_color="orange",
      annotation_text="Batas Underload",
  )
  fig_bar.add_hline(
      y=threshold_overload,
      line_dash="dash",
      line_color="red",
      annotation_text="Batas Overload",
  )
  fig_bar.update_layout(yaxis_title="% WLA", xaxis_title="Operator")
  st.plotly_chart(fig_bar, use_container_width=True)

  col_pie1, col_pie2 = st.columns(2)
  with col_pie1:
    fig_pie = px.pie(
        df_input,
        names="Kategori_WLA",
        title="Distribusi Status Beban Kerja Lini",
        color="Kategori_WLA",
        color_discrete_map=color_map,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

  with col_pie2:
    st.markdown("### 🫀 Indikator Risiko Kelelahan Kerja (Fatigue)")
    st.dataframe(
        df_input[["Operator", "Percent_WLA", "Fatigue_Risk"]].style.format(
            {"Percent_WLA": "{:.1f}%"}
        ),
        use_container_width=True,
    )

# ------------------------------------------
# PAGE 3: DSS INTERAKTIF (REDISTRIBUSI DINAMIS)
# ------------------------------------------
with tab3:
  st.subheader("🔄 Interactive Decision Support System: Simulasi Redistribusi")
  st.write(
      "Fitur interaktif ini digunakan untuk mencoba pemecahan/redistribusi"
      " elemen kerja dari operator yang **Overload** ke operator yang"
      " **Underload**, dengan batasan tidak melebihi batas maksimal overload."
  )

  if "df_simulasi" not in st.session_state or st.button(
      "Reset Simulasi ke Kondisi Awal"
  ):
    st.session_state.df_simulasi = df_input.copy()

  df_sim = st.session_state.df_simulasi

  col_s1, col_s2 = st.columns(2)

  list_over = df_sim[df_sim["Kategori_WLA"] == "Overload"]["Operator"].tolist()
  list_under = df_sim[df_sim["Kategori_WLA"] != "Overload"][
      "Operator"
  ].tolist()

  if list_over and list_under:
    with col_s1:
      op_sumber = st.selectbox("Pilih Operator Sumber (Overload):", list_over)
    with col_s2:
      op_penerima = st.selectbox(
          "Pilih Operator Penerima (Underload/Normal):", list_under
      )

    waktu_sumber = df_sim.loc[
        df_sim["Operator"] == op_sumber, "Total_Waktu_Kerja_Menit"
    ].values[0]
    waktu_penerima = df_sim.loc[
        df_sim["Operator"] == op_penerima, "Total_Waktu_Kerja_Menit"
    ].values[0]

    kapasitas_maks_penerima_menit = (
        threshold_overload / 100.0
    ) * jam_kerja_efektif
    sisa_kapasitas_menit = max(0.0, kapasitas_maks_penerima_menit - waktu_penerima)

    st.markdown("---")
    st.caption(
        f"🛡️ **Guardrail Sistem:** Maksimal waktu yang dapat dipindahkan ke"
        f" **{op_penerima}** adalah **{sisa_kapasitas_menit:.1f} menit** (agar"
        f" {op_penerima} tidak menjadi Overload)."
    )

    if sisa_kapasitas_menit > 0:
      menit_transfer = st.slider(
          f"Geser Waktu Kerja (Menit) dari {op_sumber} ➡️ {op_penerima}:",
          min_value=0.0,
          max_value=float(sisa_kapasitas_menit),
          value=0.0,
          step=1.0,
      )

      if st.button("Terapkan Redistribusi"):
        st.session_state.df_simulasi.loc[
            st.session_state.df_simulasi["Operator"] == op_sumber,
            "Total_Waktu_Kerja_Menit",
        ] -= menit_transfer
        st.session_state.df_simulasi.loc[
            st.session_state.df_simulasi["Operator"] == op_penerima,
            "Total_Waktu_Kerja_Menit",
        ] += menit_transfer

        st.session_state.df_simulasi["Percent_WLA"] = (
            st.session_state.df_simulasi["Total_Waktu_Kerja_Menit"]
            / jam_kerja_efektif
        ) * 100
        st.session_state.df_simulasi["Kategori_WLA"] = (
            st.session_state.df_simulasi["Percent_WLA"].apply(kategorisasi_wla)
        )
        st.session_state.df_simulasi["Fatigue_Risk"] = (
            st.session_state.df_simulasi["Percent_WLA"].apply(
                indikator_fatigue
            )
        )
        st.success(
            f"Berhasil memindahkan {menit_transfer} menit kerja dari"
            f" {op_sumber} ke {op_penerima}!"
        )
        st.rerun()
    else:
      st.warning(
          f"Operator {op_penerima} sudah berada di ambang batas maksimal"
          " Overload. Pilih operator penerima lain!"
      )

  else:
    st.success(
        "🎉 Luar biasa! Seluruh operator sudah berada pada kondisi seimbang"
        " (Tidak ada operator Overload)."
    )

  st.markdown("### 📊 Perbandingan % WLA Eksisting vs Hasil Simulasi DSS")

  df_compare = pd.DataFrame({
      "Operator": df_input["Operator"],
      "Eksisting (% WLA)": df_input["Percent_WLA"],
      "Hasil Redistribusi DSS (% WLA)": st.session_state.df_simulasi[
          "Percent_WLA"
      ],
  }).melt(id_vars="Operator", var_name="Kondisi", value_name="Percent_WLA")

  fig_sim = px.bar(
      df_compare,
      x="Operator",
      y="Percent_WLA",
      color="Kondisi",
      barmode="group",
      text=df_compare["Percent_WLA"].apply(lambda x: f"{x:.1f}%"),
      title="Dampak Simulasi Redistribusi Elemen Kerja Terhadap Beban Kerja Lini",
  )
  fig_sim.add_hline(
      y=threshold_underload,
      line_dash="dash",
      line_color="orange",
      annotation_text="Batas Underload",
  )
  fig_sim.add_hline(
      y=threshold_overload,
      line_dash="dash",
      line_color="red",
      annotation_text="Batas Overload",
  )
  st.plotly_chart(fig_sim, use_container_width=True)

# ------------------------------------------
# PAGE 4: ANALISIS KEBUTUHAN STAFF
# ------------------------------------------
with tab4:
  st.subheader(
      "⚖️ Analisis Kebutuhan Tenaga Kerja Optimal (Pasca Redistribusi)"
  )
  st.write(
      "Halaman ini menganalisis kebutuhan jumlah tenaga kerja yang dihitung"
      " **berdasarkan kondisi beban kerja setelah simulasi redistribusi pada"
      " Page 3**."
  )

  df_hasil_sim = st.session_state.df_simulasi
  total_waktu_butuh = df_hasil_sim["Total_Waktu_Kerja_Menit"].sum()
  staff_eksisting = len(df_hasil_sim)
  staff_teoritis = total_waktu_butuh / jam_kerja_efektif
  staff_optimal = int(np.ceil(staff_teoritis))

  col1, col2, col3 = st.columns(3)
  col1.metric("Operator Eksisting Lini", f"{staff_eksisting} Orang")
  col2.metric("Kebutuhan Operator (Teoritis)", f"{staff_teoritis:.2f} Orang")
  col3.metric("Kebutuhan Operator Optimal", f"{staff_optimal} Orang")

  st.markdown("---")
  st.markdown(
      "### 🔍 Evaluasi Status Lini Setelah Attempt Redistribusi Page 3"
  )

  sisa_overload = len(
      df_hasil_sim[df_hasil_sim["Kategori_WLA"] == "Overload"]
  )
  sisa_underload = len(
      df_hasil_sim[df_hasil_sim["Kategori_WLA"] == "Underload"]
  )

  col_e1, col_e2 = st.columns(2)
  col_e1.metric("Sisa Operator Overload", f"{sisa_overload} Orang")
  col_e2.metric("Sisa Operator Underload", f"{sisa_underload} Orang")

# ------------------------------------------
# PAGE 5: REKOMENDASI DSS, BIAYA, & EXPORT PDF/EXCEL
# ------------------------------------------
with tab5:
  st.subheader("🎯 Rekomendasi Strategis Pengambilan Keputusan (DSS)")

  df_final = st.session_state.df_simulasi.copy()
  sisa_over = len(df_final[df_final["Kategori_WLA"] == "Overload"])
  sisa_under = len(df_final[df_final["Kategori_WLA"] == "Underload"])

  total_waktu_butuh = df_final["Total_Waktu_Kerja_Menit"].sum()
  staff_teoritis = total_waktu_butuh / jam_kerja_efektif
  staff_optimal = int(np.ceil(staff_teoritis))
  staff_eksisting = len(df_final)
  selisih_staff = staff_optimal - staff_eksisting

  status_rekomendasi = ""
  total_biaya_lembur = 0

  if sisa_over == 0 and sisa_under == 0:
    status_rekomendasi = "REKOMENDASI 1: CUKUP LAKUKAN REDISTRIBUSI TUGAS"
    st.success(
        "✅ **REKOMENDASI 1: CUKUP LAKUKAN REDISTRIBUSI (TANPA REKRUTMEN /"
        " LEMBUR)**"
    )
    st.write("""
        * **Keputusan:** Penyeimbangan lini (*Line Balancing*) pada Page 3 berhasil menghilangkan seluruh status Overload dan Underload.
        * **Tindakan:** Terapkan alokasi tugas hasil simulasi secara resmi di lini produksi.
        * **Dampak Biaya:** **Rp 0 (Hemat 100%)**.
        """)

  elif sisa_over > 0 and selisih_staff > 0:
    status_rekomendasi = (
        f"REKOMENDASI 2: PENAMBAHAN {selisih_staff} STAFF ATAU SKEMA LEMBUR"
    )
    st.error(
        f"⚠️ **REKOMENDASI 2: PERLU PENAMBAHAN TENAGA KERJA ({selisih_staff}"
        " ORANG) ATAU SKEMA LEMBUR**"
    )
    st.write(f"""
        * **Keputusan:** Meskipun telah dilakukan redistribusi pada Page 3, masih terdapat operator yang mengalami *Overload* karena total beban kerja lini melampaui jam kerja efektif.
        * **Tindakan Jangka Panjang:** Rekrut **{selisih_staff} orang operator baru** untuk menyeimbangkan kapasitas lini secara permanen.
        * **Tindakan Jangka Pendek:** Berlakukan skema **jam kerja lembur (*overtime*)** dengan estimasi biaya di bawah ini:
        """)

    st.markdown(
        "### ⏱️ Rincian Kebutuhan Jam Lembur & Estimasi Biaya (per Shift)"
    )

    df_lembur = df_final[df_final["Kategori_WLA"] == "Overload"].copy()
    df_lembur["Kelebihan_Menit"] = (
        df_lembur["Total_Waktu_Kerja_Menit"] - jam_kerja_efektif
    )
    df_lembur["Kebutuhan_Lembur_Jam"] = df_lembur["Kelebihan_Menit"] / 60.0
    df_lembur["Estimasi_Biaya_Lembur_Rp"] = (
        df_lembur["Kebutuhan_Lembur_Jam"] * tarif_lembur_per_jam
    )

    df_tampil_lembur = df_lembur[[
        "Operator",
        "Percent_WLA",
        "Kelebihan_Menit",
        "Kebutuhan_Lembur_Jam",
        "Estimasi_Biaya_Lembur_Rp",
    ]]

    st.dataframe(
        df_tampil_lembur.style.format({
            "Percent_WLA": "{:.1f}%",
            "Kelebihan_Menit": "{:.1f} Menit",
            "Kebutuhan_Lembur_Jam": "{:.2f} Jam",
            "Estimasi_Biaya_Lembur_Rp": "Rp {:,.0f}",
        }),
        use_container_width=True,
    )

    total_jam_lembur = df_lembur["Kebutuhan_Lembur_Jam"].sum()
    total_biaya_lembur = df_lembur["Estimasi_Biaya_Lembur_Rp"].sum()

    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Total Jam Lembur Lini", f"{total_jam_lembur:.2f} Jam/Shift")
    col_m2.metric(
        "Estimasi Tambahan Biaya Lembur", f"Rp {total_biaya_lembur:,.0f} / Shift"
    )

  elif selisih_staff < 0:
    status_rekomendasi = (
        f"REKOMENDASI 3: EFISIENSI OPERATOR ({abs(selisih_staff)} ORANG"
        " OVERSTAFFED)"
    )
    st.warning(f"⚠️ **REKOMENDASI 3: EFISIENSI OPERATOR (OVERSTAFFED)**")
    st.write(
        f"Direkomendasikan memindahkan **{abs(selisih_staff)} orang operator**"
        " ke lini produksi lain yang membutuhkan."
    )

  else:
    status_rekomendasi = "REKOMENDASI 4: OPTIMALKAN KEMBALI REDISTRIBUSI ATOMIK"
    st.info("💡 **REKOMENDASI 4: OPTIMALKAN KEMBALI REDISTRIBUSI ATOMIK**")
    st.write(
        "Kapasitas total jam kerja sebenarnya mencukupi. Cobalah kembali ke"
        " **Page 3** untuk menggeser alokasi waktu ke operator yang masih"
        " Underload."
    )

  # ==========================================
  # FITUR EXPORT LAPORAN (PDF & EXCEL)
  # ==========================================
  st.markdown("---")
  st.markdown("### 📥 Export Laporan Hasil Rekomendasi DSS")
  st.write(
      "Unduh laporan resmi ringkasan analisis beban kerja, hasil simulasi,"
      " dan estimasi keputusan dalam format **PDF** atau **Excel**."
  )

  col_exp1, col_exp2 = st.columns(2)

  # 1. TOMBOL DOWNLOAD EXCEL
  with col_exp1:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
      df_final.to_excel(writer, sheet_name="Simulasi_WLA_Final", index=False)
      df_summary_report = pd.DataFrame({
          "Parameter_Evaluasi": [
              "Status Rekomendasi DSS",
              "Total Operator Eksisting",
              "Kebutuhan Operator Optimal",
              "Tarif Lembur per Jam (Rp)",
              "Total Estimasi Biaya Lembur (Rp/Shift)",
          ],
          "Nilai": [
              status_rekomendasi,
              staff_eksisting,
              staff_optimal,
              f"Rp {tarif_lembur_per_jam:,.0f}",
              f"Rp {total_biaya_lembur:,.0f}",
          ],
      })
      df_summary_report.to_excel(
          writer, sheet_name="Ringkasan_Keputusan", index=False
      )

    st.download_button(
        label="📥 Download Laporan (Excel .xlsx)",
        data=buffer.getvalue(),
        file_name="Laporan_DSS_Analisis_Beban_Kerja.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        use_container_width=True,
    )

  # 2. TOMBOL DOWNLOAD PDF
  with col_exp2:
    pdf_bytes = generate_pdf_report(
        status_rekomendasi,
        staff_eksisting,
        staff_optimal,
        total_biaya_lembur,
        df_final,
    )

    st.download_button(
        label="📄 Download Laporan Resmi (PDF .pdf)",
        data=pdf_bytes,
        file_name="Laporan_DSS_Analisis_Beban_Kerja.pdf",
        mime="application/pdf",
        use_container_width=True,
    )