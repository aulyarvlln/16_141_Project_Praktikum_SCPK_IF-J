import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==================== KONFIGURASI HALAMAN ====================
st.set_page_config(page_title="SPK Bus Sekolah DKI", layout="wide")

# ==================== SIDEBAR NAVIGASI ====================
st.sidebar.title("🚌 Navigasi")
page = st.sidebar.radio("Pilih Halaman", ["📊 Data", "⚙️ Hitung WP", "👥 Profil Kelompok"])

# ==================== LOAD DATA ====================
@st.cache_data
def load_data():
    # GANTI DENGAN NAMA FILE CSV KALIAN
    df = pd.read_csv('Filedata Data Operasi Bus Dan Penumpang Bus Sekolah Di DKI Jakarta.csv')
    return df

def aggregate_data(df):
    """Menghitung nilai 5 kriteria per rute"""
    hasil = []
    for rute in df['nama_rute'].unique():
        data_rute = df[df['nama_rute'] == rute]
        
        # C1: Rata-rata penumpang
        c1 = data_rute['jumlah_penumpang'].mean()
        
        # C2: Efisiensi armada (penumpang/bus)
        with np.errstate(divide='ignore', invalid='ignore'):
            efisiensi_per_hari = data_rute['jumlah_penumpang'] / data_rute['jumlah_bus'].replace(0, np.nan)
        c2 = efisiensi_per_hari.mean()
        if np.isnan(c2):
            c2 = 0
            
        # C3: Konsistensi operasi (1/(1+std))
        std_penumpang = data_rute['jumlah_penumpang'].std()
        c3 = 1 / (1 + std_penumpang)
        
        # C4: Frekuensi operasional (hari dengan bus > 0)
        c4 = (data_rute['jumlah_bus'] > 0).sum()
        
        # C5: Rata-rata bus per hari
        c5 = data_rute['jumlah_bus'].mean()
        
        hasil.append({
            'nama_rute': rute,
            'C1_Rata2Penumpang': round(c1, 2),
            'C2_EfisiensiArmada': round(c2, 2),
            'C3_Konsistensi': round(c3, 4),
            'C4_Frekuensi': c4,
            'C5_Rata2Bus': round(c5, 2)
        })
    
    df_agregat = pd.DataFrame(hasil)
    return df_agregat

def hitung_wp(df_kriteria, bobot):
    """Menghitung Weighted Product (semua benefit)"""
    df_normalisasi = df_kriteria.copy()
    kolom_kriteria = ['C1_Rata2Penumpang', 'C2_EfisiensiArmada', 'C3_Konsistensi', 'C4_Frekuensi', 'C5_Rata2Bus']
    
    # Normalisasi (benefit: X / max)
    for kol in kolom_kriteria:
        max_val = df_kriteria[kol].max()
        if max_val > 0:
            df_normalisasi[kol] = df_kriteria[kol] / max_val
        else:
            df_normalisasi[kol] = 0
    
    # Hitung S (Product of X^w)
    df_normalisasi['S'] = 1
    for i, kol in enumerate(kolom_kriteria):
        df_normalisasi['S'] *= df_normalisasi[kol] ** bobot[i]
    
    # Hitung V (normalisasi S)
    total_s = df_normalisasi['S'].sum()
    df_normalisasi['V'] = df_normalisasi['S'] / total_s if total_s > 0 else 0
    
    # Ranking
    df_normalisasi['Ranking'] = df_normalisasi['V'].rank(ascending=False, method='dense').astype(int)
    
    # Urutkan berdasarkan V tertinggi
    df_hasil = df_normalisasi.sort_values('V', ascending=False).reset_index(drop=True)
    
    return df_hasil, df_normalisasi

# ==================== HALAMAN DATA ====================
if page == "📊 Data":
    st.title("📊 Data Operasional Bus Sekolah DKI Jakarta")
    
    df_raw = load_data()
    st.subheader("Dataset Mentah")
    st.dataframe(df_raw, use_container_width=True)
    
    st.subheader("Statistik Dataset")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Jumlah Baris", f"{len(df_raw):,}")
    col2.metric("Jumlah Kolom", len(df_raw.columns))
    col3.metric("Jumlah Rute", df_raw['nama_rute'].nunique())
    col4.metric("Periode", "Jan-Mei 2014")
    
    st.subheader("Preview Data Agregat per Rute")
    df_agregat = aggregate_data(df_raw)
    st.dataframe(df_agregat, use_container_width=True)

# ==================== HALAMAN HITUNG WP ====================
elif page == "⚙️ Hitung WP":
    st.title("⚙️ Perhitungan Weighted Product")
    
    # Load dan agregasi data
    df_raw = load_data()
    df_agregat = aggregate_data(df_raw)
    
    # Tampilkan matriks keputusan
    st.subheader("📋 Matriks Keputusan (Nilai Kriteria per Rute)")
    st.dataframe(df_agregat, use_container_width=True)
    
    # Input bobot
    st.subheader("🎚️ Input Bobot Kriteria")
    st.write("Semua kriteria bersifat **Benefit** (semakin tinggi semakin baik)")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        b1 = st.slider("C1 - Rata2 Penumpang", 0.0, 1.0, 0.35, 0.05)
    with col2:
        b2 = st.slider("C2 - Efisiensi Armada", 0.0, 1.0, 0.25, 0.05)
    with col3:
        b3 = st.slider("C3 - Konsistensi", 0.0, 1.0, 0.10, 0.05)
    with col4:
        b4 = st.slider("C4 - Frekuensi", 0.0, 1.0, 0.15, 0.05)
    with col5:
        b5 = st.slider("C5 - Rata2 Bus", 0.0, 1.0, 0.15, 0.05)
    
    total_bobot = b1 + b2 + b3 + b4 + b5
    st.info(f"📌 Total bobot: **{total_bobot:.2f}** (harus 1.00)")
    
    if total_bobot != 1.0:
        st.warning("⚠️ Total bobot harus 1.00. Silakan sesuaikan slider!")
    
    bobot = [b1, b2, b3, b4, b5]
    
    # Tombol eksekusi
    if st.button("🚀 Hitung WP", type="primary"):
        if total_bobot != 1.0:
            st.error("Total bobot tidak 1.00, silakan sesuaikan!")
        else:
            # Hitung WP
            df_hasil, df_normalisasi = hitung_wp(df_agregat, bobot)
            
            # Tabel hasil perangkingan
            st.subheader("🏆 Hasil Perangkingan Rute Bus Sekolah")
            
            kolom_tampil = ['nama_rute', 'V', 'Ranking']
            df_ranking = df_hasil[kolom_tampil].copy()
            df_ranking['V'] = df_ranking['V'].apply(lambda x: f"{x:.6f}")
            st.dataframe(df_ranking, use_container_width=True)
            
            # Tabel lengkap
            with st.expander("📊 Lihat Tabel Lengkap (Normalisasi + S + V)"):
                st.dataframe(df_hasil, use_container_width=True)
            
            # ==================== GRAFIK 1: BAR CHART RANKING (Matplotlib) ====================
            st.subheader("📊 Visualisasi Hasil")
            
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            top10 = df_hasil.head(10)
            warna = ['green' if i == 0 else 'steelblue' for i in range(len(top10))]
            ax1.barh(top10['nama_rute'], top10['V'], color=warna)
            ax1.set_xlabel('Nilai Preferensi (V)')
            ax1.set_ylabel('Nama Rute')
            ax1.set_title('Top 10 Rute Bus Sekolah Terbaik')
            ax1.invert_yaxis()
            
            # Tambahkan label nilai
            for i, (idx, row) in enumerate(top10.iterrows()):
                ax1.text(row['V'] + 0.001, i, f"{row['V']:.5f}", va='center')
            
            st.pyplot(fig1)
            
            # ==================== GRAFIK 2: PERBANDINGAN KRITERIA (Matplotlib) ====================
            fig2, ax2 = plt.subplots(figsize=(12, 6))
            top5 = df_hasil.head(5)
            kriteria = ['C1_Rata2Penumpang', 'C2_EfisiensiArmada', 'C3_Konsistensi', 'C4_Frekuensi', 'C5_Rata2Bus']
            kriteria_labels = ['Rata2 Penumpang', 'Efisiensi', 'Konsistensi', 'Frekuensi', 'Rata2 Bus']
            
            # Normalisasi per kriteria untuk perbandingan
            x = np.arange(len(kriteria))
            lebar = 0.15
            warna_bar = ['#e74c3c', '#e67e22', '#f1c40f', '#2ecc71', '#3498db']
            
            for i, (idx, row) in enumerate(top5.iterrows()):
                nilai_asli = [row[k] for k in kriteria]
                max_per_kriteria = [df_agregat[k].max() for k in kriteria]
                nilai_normalisasi = [nilai_asli[j]/max_per_kriteria[j] if max_per_kriteria[j] > 0 else 0 for j in range(len(kriteria))]
                ax2.bar(x + i*lebar, nilai_normalisasi, lebar, label=row['nama_rute'], color=warna_bar[i % len(warna_bar)])
            
            ax2.set_xlabel('Kriteria')
            ax2.set_ylabel('Nilai Ternormalisasi')
            ax2.set_title('Perbandingan 5 Rute Terbaik per Kriteria')
            ax2.set_xticks(x + lebar * 2)
            ax2.set_xticklabels(kriteria_labels, rotation=45, ha='right')
            ax2.legend(loc='upper right')
            ax2.set_ylim(0, 1.1)
            st.pyplot(fig2)
            
            # ==================== GRAFIK 3: LINE CHART PERBANDINGAN NILAI V ====================
            fig3, ax3 = plt.subplots(figsize=(12, 5))
            all_rutes = df_hasil['nama_rute'].tolist()
            all_v = df_hasil['V'].tolist()
            
            ax3.plot(all_rutes, all_v, marker='o', linestyle='-', linewidth=2, markersize=6, color='steelblue')
            ax3.set_xlabel('Nama Rute')
            ax3.set_ylabel('Nilai Preferensi (V)')
            ax3.set_title('Perbandingan Nilai V untuk Semua Rute')
            ax3.tick_params(axis='x', rotation=90)
            ax3.grid(True, alpha=0.3)
            
            # Tandai rute tertinggi
            max_idx = all_v.index(max(all_v))
            ax3.plot(max_idx, all_v[max_idx], 'ro', markersize=10, label=f"Terbaik: {all_rutes[max_idx]}")
            ax3.legend()
            
            st.pyplot(fig3)
            
            st.success("✅ Perhitungan WP selesai!")

# ==================== HALAMAN PROFIL ====================
elif page == "👥 Profil Kelompok":
    st.title("👥 Profil Kelompok")
    
    st.subheader("Identitas Proyek")
    st.markdown("""
    | Item | Keterangan |
    |------|-------------|
    | **Judul Proyek** | Penentuan Rute Bus Sekolah Paling Efektif Berdasarkan Data Operasional Menggunakan Metode Weighted Product |
    | **Mata Kuliah** | Sistem Cerdas dan Pengambilan Keputusan (SCPK) |
    | **Metode** | Weighted Product (WP) |
    | **Sumber Data** | Data Operasi Bus Dan Penumpang Bus Sekolah Di DKI Jakarta |
    | **Periode Data** | Januari - Mei 2014 |
    """)
    
    st.subheader("Anggota Kelompok")
    
    # GANTI DENGAN NAMA DAN NIM KALIAN
    anggota = pd.DataFrame({
        "Nama": ["Nama Mahasiswa 1", "Nama Mahasiswa 2"],
        "NIM": ["1234567890", "1234567891"],
        "Peran": ["Backend & Dokumentasi", "Frontend & Analisis Data"]
    })
    st.dataframe(anggota, use_container_width=True)
    
    st.subheader("Kriteria yang Digunakan")
    kriteria_df = pd.DataFrame({
        "Kode": ["C1", "C2", "C3", "C4", "C5"],
        "Kriteria": ["Rata-rata Penumpang", "Efisiensi Armada", "Konsistensi Operasi", "Frekuensi Operasional", "Rata-rata Bus per Hari"],
        "Jenis": ["Benefit"] * 5,
        "Bobot Default": [0.35, 0.25, 0.10, 0.15, 0.15]
    })
    st.dataframe(kriteria_df, use_container_width=True)
    
    st.subheader("Tentang Aplikasi")
    st.write("""
    Aplikasi ini dibangun menggunakan:
    - **Streamlit** untuk antarmuka GUI
    - **Pandas & NumPy** untuk pengolahan data
    - **Matplotlib** untuk visualisasi
    - **Metode Weighted Product** untuk perhitungan SPK
    """)