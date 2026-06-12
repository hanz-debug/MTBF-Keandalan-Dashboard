import streamlit as st
import pandas as pd
from io import BytesIO

# ==========================================
# 1. PENGATURAN TEMA & HALAMAN
# ==========================================
st.set_page_config(page_title="Dashboard MTBF & Reliability", layout="wide")

# INJEKSI CSS UNTUK BACKGROUND INDUSTRI & DARK GLASSMORPHISM
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}
    
    /* Mengganti background utama dengan gambar industri */
    [data-testid="stAppViewContainer"] {
        background-image: url("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=2000&q=80");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    /* Efek Dark Glassmorphism agar teks putih terbaca sangat jelas */
    .block-container {
        background-color: rgba(25, 30, 36, 0.90) !important; /* Warna gelap elegan semi-transparan */
        padding: 2.5rem !important;
        border-radius: 15px;
        box-shadow: 0 15px 30px rgba(0, 0, 0, 0.6);
        margin-top: 2rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1); /* Garis tepi tipis agar terlihat tajam */
    }
    
    /* Memastikan judul dan teks berwarna putih/abu terang agar kontras */
    h1, h2, h3, h4, p, li, label {
        color: #F8F9FA !important;
    }
    
    /* Menyesuaikan kotak notifikasi agar menyatu dengan tema gelap */
    div[data-testid="stInfo"] {
        background-color: rgba(52, 152, 219, 0.15) !important;
        border: 1px solid rgba(52, 152, 219, 0.4) !important;
        color: #F8F9FA !important;
    }
    
    /* Menyesuaikan warna header tabel */
    th {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

TOTAL_BULAN_3_TAHUN = 36

def format_waktu_detail(total_bulan):
    tahun = int(total_bulan // 12)
    sisa_bulan = total_bulan % 12
    bulan = int(sisa_bulan)
    hari = int(round((sisa_bulan - bulan) * 30))
    
    if hari == 30:
        bulan += 1
        hari = 0
        if bulan == 12:
            tahun += 1
            bulan = 0
            
    hasil = []
    if tahun > 0:
        hasil.append(f"{tahun} Tahun")
    if bulan > 0:
        hasil.append(f"{bulan} Bulan")
    if hari > 0:
        hasil.append(f"{hari} Hari")
        
    if not hasil:
        return "0 Hari"
        
    return " ".join(hasil)

def tentukan_rekomendasi(bulan):
    if bulan < 6:
        return "🔴 Kritis - Segera Lakukan RCA"
    elif bulan < 12:
        return "🟡 Waspada - Cek Jadwal PM"
    else:
        return "🟢 Andal - Operasi Normal"

# ==========================================
# 2. PANEL SAMPING (SIDEBAR) KENDALI UTAMA
# ==========================================
st.sidebar.title("Panel Kendali")
st.sidebar.info("Silakan unggah file database riwayat kerusakan equipment pabrik di sini.")

file_unggahan = st.sidebar.file_uploader("Unggah File Excel (.xlsx)", type=["xlsx"])

# ==========================================
# 3. LAYAR UTAMA (MAIN AREA)
# ==========================================
st.title("Dashboard Keandalan & MTBF Equipment")
st.write("Sistem Pemantauan Performa Mesin dan Prediksi Jadwal Maintenance.")
st.markdown("---")

if file_unggahan is not None:
    df = pd.read_excel(file_unggahan)
    df['MTBF_Angka_Bulan'] = df['Total_Kerusakan_3_Tahun'].apply(
        lambda x: TOTAL_BULAN_3_TAHUN / x if x > 0 else TOTAL_BULAN_3_TAHUN
    )
    
    df['MTBF_Format'] = df['MTBF_Angka_Bulan'].apply(format_waktu_detail)
    df['Rekomendasi'] = df['MTBF_Angka_Bulan'].apply(tentukan_rekomendasi)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Penyaringan Data")
    list_area = ["Semua Area Operasional"] + list(df['Area'].unique())
    pilihan_area = st.sidebar.selectbox("Pilih Area:", list_area)
    
    if pilihan_area == "Semua Area Operasional":
        df_filtered = df
    else:
        df_filtered = df[df['Area'] == pilihan_area]

    # ==========================================
    # 4. KARTU METRIK & KPI
    # ==========================================
    st.subheader(f"Status Performa: {pilihan_area}")
    
    total_alat = len(df_filtered)
    total_rusak = df_filtered['Total_Kerusakan_3_Tahun'].sum()
    rata_rata_mtbf_bulan = df_filtered['MTBF_Angka_Bulan'].mean()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**Total Equipment**\n\n### {total_alat} Unit")
    with col2:
        st.warning(f"**Total Insiden Kerusakan**\n\n### {total_rusak} Kali")
    with col3:
        st.success(f"**Rata-rata MTBF**\n\n### {format_waktu_detail(rata_rata_mtbf_bulan)}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ==========================================
    # 5. VISUALISASI GRAFIK
    # ==========================================
    st.subheader("Identifikasi 'Bad Actors' (Top 10 Paling Sering Rusak)")
    top_10_rusak = df_filtered.nlargest(10, 'Total_Kerusakan_3_Tahun')
    
    if top_10_rusak['Total_Kerusakan_3_Tahun'].sum() == 0:
        st.success("Tidak ada catatan kerusakan pada area ini. Seluruh equipment beroperasi optimal!")
    else:
        data_grafik = top_10_rusak.set_index('ID_Equipment')[['Total_Kerusakan_3_Tahun']]
        st.bar_chart(data_grafik, color="#ff4b4b", height=350)
        
    st.markdown("---")

    # ==========================================
    # 6. TABEL DATA
    # ==========================================
    st.subheader("Detail Data Historis & Status Maintenance")
    
    tabel_tampil = df_filtered.drop(columns=['MTBF_Angka_Bulan'])
    tabel_tampil = tabel_tampil.rename(columns={
        "ID_Equipment": "ID Alat",
        "Jenis_Equipment": "Jenis Alat",
        "Total_Kerusakan_3_Tahun": "Frekuensi Rusak",
        "MTBF_Format": "Nilai MTBF",
        "Rekomendasi": "Status & Tindakan"
    })
    
    st.dataframe(tabel_tampil, use_container_width=True, height=400)
    
    st.write("")
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        tabel_tampil.to_excel(writer, index=False, sheet_name='Analisis_MTBF')
    
    st.download_button(
        label="Unduh Laporan Tabel ini (.xlsx)",
        data=output.getvalue(),
        file_name=f"Laporan_Keandalan_Alat_{pilihan_area}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )

else:
    # ==========================================
    # LAYAR SAMBUTAN
    # ==========================================
    st.info("Selamat datang di Sistem Analisis Keandalan Equipment.")
    st.write("""
    **Cara Menggunakan Sistem:**
    1. Siapkan file riwayat kerusakan dari database (Format Excel `.xlsx`).
    2. Buka panel menu di sebelah kiri.
    3. Klik **Browse files** dan masukkan file Anda.
    4. Sistem akan secara otomatis menghitung Mean Time Between Failures (MTBF) hingga presisi Tahun, Bulan, dan Hari, lalu memetakan 10 mesin yang membutuhkan inspeksi lebih lanjut.
    """)
