import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.sidebar.title("🚌 Rute Bus Sekolah")
page = st.sidebar.radio("Halaman", ["📊 Data", "⚙️ Hitung WP", "👥 Profil Kelompok"])

# ==================== LOAD DATA ====================
@st.cache_data # Menyimpan cache agar loading data lebih cepat
def load_data():
    data = pd.read_csv('Filedata Data Operasi Bus Dan Penumpang Bus Sekolah Di DKI Jakarta.csv')
    return data

def aggregate_data(data):
    hasil = []
    for rute in data['nama_rute'].unique(): #ini (maksudnya perulangan unique?)=> iya dibuat unik agar setiap data berbeda dan nantinya kalau mau mengambil data rute tidak ada data yg sama/ datany duplikat, jadi misal ada rute 1, rute 2, dst, maka data_rute akan menyimpan data dari rute 1, rute 2, dst secara terpisah sesuai dengan nama_rute yang unik tersebut
        data_rute = data[data['nama_rute'] == rute] #ini (ini tu maksudnya data bakal nyimpan data dari rute 1, rute 2, dst? apa gimana??)=>filtering data.program sedang looping satu per satu nama rute,Data tiap rute akan diambil satu per satu lalu disimpan ke variabel data_rute
        
        # C1: Rata-rata penumpang
        c1 = data_rute['jumlah_penumpang'].mean() #mean untuk melihat performa umum.
        
        # C2: Efisiensi armada
        with np.errstate(divide='ignore', invalid='ignore'): #ini (kenapa perhitungannya seperti itu? nyari efisiensi armada itu maksudnaya gimana?)=>warning dibisukan,program tetap lanjut.(menyuruh numpy diam aja,biar tidak muncul warning)
            efisiensi_per_hari = data_rute['jumlah_penumpang'] / data_rute['jumlah_bus'].replace(0, np.nan)# misal nantinya ada 100 penumpang tapi busnya 0, maka hasilnya akan jadi infinity, nah dengan replace(0, np.nan) maka hasilnya akan jadi NaN(Not a Number/nilai tersebut tidak valid / tidak bisa dihitung.)[kalau jumlah bus = 0, anggap data efisiensinya tidak bisa dihitung], sehingga tidak mempengaruhi rata-rata keseluruhan.
        c2 = efisiensi_per_hari.mean()
        if np.isnan(c2): #Kalau hasil tetap invalid, ubah jadi 0.
            c2 = 0
            
        # C3: Konsistensi operasi
        std_penumpang = data_rute['jumlah_penumpang'].std() #standard deviation untuk melihat seberapa konsisten jumlah penumpang setiap harinya. Semakin kecil standar deviasi, semakin konsisten jumlah penumpang.
        c3 = 1 / (1 + std_penumpang) #ini (rumusnya paham, tapi logikanya untuk kriterianya ngga, maksudnya?)=>karena WP suka nilai besar=bagus,sedangkan std besar=tidak konsisten, maka kita buat rumusnya jadi 1/(1+std) agar semakin kecil std semakin besar nilai konsistensinya.
        
        # C4: Frekuensi operasional (hari dengan bus > 0)
        c4 = (data_rute['jumlah_bus'] > 0).sum()
        
        # C5: Rata-rata bus per hari
        c5 = data_rute['jumlah_bus'].mean()
        
        hasil.append({ #ini (kenapa pake append?)=>karena kita mengumpulkan data satu per satu.[Analoginya seperti kita punya daftar kosong, lalu kita tambahkan data satu per satu ke dalam daftar tersebut menggunakan append.]
            'nama_rute': rute,
            'C1_Rata2Penumpang': round(c1, 2),
            'C2_EfisiensiArmada': round(c2, 2),
            'C3_Konsistensi': round(c3, 4),
            'C4_Frekuensi': c4,
            'C5_Rata2Bus': round(c5, 2)
        })

    data_agregat = pd.DataFrame(hasil) #ini (kalo aku mau tampilkan datanya dulu bisa ngga? ini aku coba di file berbeda si ipynb)=>print(hasil)
    return data_agregat
    #contoh dari pertanyaan di line 50
    #hasil = []
    #hasil.append({
    #'nama_rute': 'Rute A',
    #'C1': 100
    #})
    #hasil.append({
    #'nama_rute': 'Rute B',
    #'C1': 200
    #})
    # tampil list dulu
    #print(hasil)
    # ubah ke dataframe
    #data_agregat = pd.DataFrame(hasil)
    # tampil dataframe
    #data_agregat
# ==================== HITUNG WEIGHTED PRODUCT ====================
def hitung_wp(kriteria, bobot):
    data_normalisasi = kriteria.copy() #ini (buat apa digandakan? merusak data asli maksudhnya gimana?)=>karen kalau tidak di copy akan jadi gini-> data_normalisasi = kriteria,maka keduanya menunjuk objek yang sama. Jadi kalau kita ubah data_normalisasi, maka data kriteria juga akan berubah. Dengan menggunakan copy(), kita membuat salinan baru dari data kriteria, sehingga perubahan pada data_normalisasi tidak akan mempengaruhi data kriteria asli. Jadi data_normalisasi bisa kita modifikasi untuk proses normalisasi dan perhitungan WP tanpa merusak data kriteria yang asli.[analoginya kyk fotokopi dokumen, kita punya dokumen asli (kriteria), lalu kita buat fotokopi (data_normalisasi) untuk kita modifikasi, sehingga dokumen asli tetap utuh/tidak merusak data asli]
    nama_kriteria = ['C1_Rata2Penumpang', 'C2_EfisiensiArmada', 'C3_Konsistensi', 'C4_Frekuensi', 'C5_Rata2Bus']

# ==================== NORMALISASI ====================
    # Normalisasi (benefit: X / max)
    for kolom in nama_kriteria:
        max_perkolom = kriteria[kolom].max()
        if max_perkolom > 0:
            data_normalisasi[kolom] = kriteria[kolom] / max_perkolom
        else:
            data_normalisasi[kolom] = 0
# ==================== HITUNG S ====================
    # Hitung S (Product of X^w)
    data_normalisasi['S'] = 1 #ini (maksud codenya apa?)=>karena nantinya S *= nilai jdi kalau dimulai dari 0, maka hasilnya akan selalu 0. Dengan memulai dari 1, kita bisa mengalikan nilai kriteria yang sudah dipangkatkan dengan bobotnya tanpa membuat hasilnya menjadi 0. Jadi S akan menjadi hasil perkalian dari semua kriteria yang sudah dipangkatkan dengan bobotnya.
    for i, kolom in enumerate(nama_kriteria): #ini (maksud codenya?)=>enumerate untuk mendapatkan indeks i dan nama kolom secara bersamaan. Jadi i akan menjadi indeks (0, 1, 2, dst) yang sesuai dengan posisi kolom dalam daftar nama_kriteria, sedangkan kolom akan menjadi nama kolom itu sendiri (misal 'C1_Rata2Penumpang', 'C2_EfisiensiArmada', dll). Dengan menggunakan enumerate, kita bisa mengakses bobot yang sesuai dengan kolom yang sedang diproses.
        data_normalisasi['S'] *= data_normalisasi[kolom] ** bobot[i] #ini (berati ini bobotnya tergantung nanti yang diinput user kan?)=>benar, nantinyansetiap nilai kriteria akan dipangkatkan dengan bobot yang diinput user.
# ==================== HITUNG V ====================
    # Hitung V (normalisasi S)
    total_s = data_normalisasi['S'].sum() #ini (maksud codenya apa? kenapa dijumlah padahal kalo di teori inikan menghitung produk tertimbang, nah dia tinggal mengalikan setiap value di rute 1 dst, dan udah tinggal perangkingan)=>menjumlahkan semua nilai S dari semua rute.,kenapa masih ada V karena biar lebih mudah dibandingkan antar rute. Jadi V adalah nilai preferensi yang sudah dinormalisasi dari S, sehingga kita bisa melihat seberapa baik setiap rute dibandingkan dengan yang lain berdasarkan nilai preferensi tersebut.
    data_normalisasi['V'] = data_normalisasi['S'] / total_s if total_s > 0 else 0 #ini (tapi ini kan pembagian, bukan perkalian? bukannya kalo WP itu tinggal ngalikan setiap value yang udah dikalikan dengan bobotnya, terus langsung bisa dibandingin aja gitu? kenapa harus dibagi total S?)=>menormalisasi hasil akhir WP.
    
    # Inti alur metode Weighted Product (WP):
# 1. Menghitung nilai S sebagai inti metode WP, yaitu dengan mengalikan setiap nilai kriteria yang sudah dipangkatkan dengan bobotnya.
# 2. Menghitung total seluruh nilai S dari semua rute.
# 3. Menghitung nilai preferensi V dengan membagi setiap nilai S dengan total S, 
#    agar hasil ternormalisasi dan berada pada rentang 0–1.
#    Nilai V digunakan sebagai nilai akhir untuk perangkingan rute.
# ==================== RANKING ====================
    data_normalisasi['Ranking'] = data_normalisasi['V'].rank(ascending=False, method='dense').astype(int) #ini (methode dense dan astype int ini apa? jelasin!)=>memberi ranking berdasarkan nilai V.
    # ascending=False untuk memberi peringkat dengan nilai V tertinggi mendapatkan peringkat 1.(mengurutkan dari nilai V yang terbesar ke terkecil)
    # method='dense' untuk memberikan peringkat yang berurutan tanpa melewati angka, jadi jika ada nilai V yang sama, mereka akan mendapatkan peringkat yang sama, dan peringkat berikutnya akan langsung berurutan tanpa melewati angka. Misalnya, jika ada dua rute dengan nilai V tertinggi yang sama, keduanya akan mendapatkan peringkat 1, dan rute berikutnya akan mendapatkan peringkat 2 (bukan 3).[method='dense' digunakan agar ranking tidak lompat]
    # astype(int) untuk mengubah tipe data ranking menjadi integer, sehingga peringkat ditampilkan sebagai angka bulat tanpa desimal.
# ==================== SORTING ====================
    # Urutkan berdasarkan V tertinggi
    data_hasil = data_normalisasi.sort_values('V', ascending=False).reset_index(drop=True) #ini (maksud codenya apa? kenapa diurutkan lagi? tadi code sblmnya kan udah ngasih ranking, nah kenapa harus diurutkan lagi?)=># Mengurutkan data berdasarkan nilai V terbesar,lalu merapikan kembali index tabel
    #rank() memberikan nomor rangking
    #sort_values() mengurutkan data berdasarkan nilai V, sehingga rute dengan nilai V tertinggi akan berada di urutan teratas. Ini penting untuk menampilkan hasil perangkingan dengan benar, karena kita ingin melihat rute terbaik (dengan nilai V tertinggi) di bagian atas tabel hasil.
    #reset_index(drop=True) digunakan untuk merapikan kembali index tabel setelah diurutkan, sehingga index akan dimulai dari 0 dan tidak mempertahankan index lama yang mungkin sudah tidak berurutan setelah sorting.
    return data_hasil, data_normalisasi

# ==================== FUNGSI INPUT BOBOT ====================

# ==================== INPUT BOBOT DENGAN SLIDER ====================
def input_bobot_slider(): #perubahan1 (buat fungsi input bobot dengan slider)
    """Metode 1: Menggunakan Slider"""
    st.info("📌 **Metode Slider** - Geser slider untuk mengatur bobot (step 0.01)")
    # Membagi tampilan menjadi 5 kolom untuk masing-masing kriteria
    col1, col2, col3, col4, col5 = st.columns(5)
    # Slider bobot C1
    with col1:
        # Slider: label, nilai minimum, maksimum, default, step
        b1 = st.slider("C1 - Penumpang", 0.0, 1.0, 0.35, 0.01)
        # Menampilkan nilai slider dalam persen
        st.caption(f"Nilai: {b1:.2f} ({b1*100:.0f}%)")
    # Slider bobot C2
    with col2:
        b2 = st.slider("C2 - Efisiensi", 0.0, 1.0, 0.25, 0.01)
        st.caption(f"Nilai: {b2:.2f} ({b2*100:.0f}%)")
    # Slider bobot C3
    with col3:
        b3 = st.slider("C3 - Konsistensi", 0.0, 1.0, 0.20, 0.01)
        st.caption(f"Nilai: {b3:.2f} ({b3*100:.0f}%)")
    # Slider bobot C4
    with col4:
        b4 = st.slider("C4 - Frekuensi", 0.0, 1.0, 0.10, 0.01)
        st.caption(f"Nilai: {b4:.2f} ({b4*100:.0f}%)")
    # Slider bobot C5
    with col5:
        b5 = st.slider("C5 - Rata2 Bus", 0.0, 1.0, 0.10, 0.01)
        st.caption(f"Nilai: {b5:.2f} ({b5*100:.0f}%)")
    # Mengembalikan semua bobot dalam bentuk list
    return [b1, b2, b3, b4, b5]
# ==================== INPUT BOBOT DENGAN NUMBER INPUT ====================
def input_bobot_number():#perubahan2 (buat fungsi input bobot dengan number input)
    """Metode 2: Menggunakan Number Input"""
    st.info("📌 **Metode Number Input** - Ketik nilai bobot secara presisi")
    # Membagi tampilan menjadi 5 kolom untuk masing-masing kriteria
    col1, col2, col3, col4, col5 = st.columns(5)
    # Input angka untuk bobot C1
    with col1:
        # number_input digunakan agar user bisa mengetik nilai bobot secara langsung
        # format %.3f berarti angka ditampilkan 3 digit di belakang koma
        b1 = st.number_input("C1 - Penumpang", 0.0, 1.0, 0.35, 0.01, format="%.3f")
        # Menampilkan bobot dalam persen
        st.caption(f"{(b1*100):.1f}%")
    # Input angka untuk bobot C2
    with col2:
        b2 = st.number_input("C2 - Efisiensi", 0.0, 1.0, 0.25, 0.01, format="%.3f")
        st.caption(f"{(b2*100):.1f}%")
    # Input angka untuk bobot C3
    with col3:
        b3 = st.number_input("C3 - Konsistensi", 0.0, 1.0, 0.10, 0.01, format="%.3f")
        st.caption(f"{(b3*100):.1f}%")
    # Input angka untuk bobot C4
    with col4:
        b4 = st.number_input("C4 - Frekuensi", 0.0, 1.0, 0.15, 0.01, format="%.3f")
        st.caption(f"{(b4*100):.1f}%")
    # Input angka untuk bobot C5
    with col5:
        b5 = st.number_input("C5 - Rata2 Bus", 0.0, 1.0, 0.15, 0.01, format="%.3f")
        st.caption(f"{(b5*100):.1f}%")
    # Mengembalikan semua bobot dalam bentuk list
    return [b1, b2, b3, b4, b5]
# ==================== INPUT BOBOT DENGAN SELECTION PRESET ====================
def input_bobot_preset():#perubahan3 (buat fungsi input bobot dengan selectbox preset)
    """Metode 3: Menggunakan Selectbox Preset"""
    st.info("📌 **Metode Preset** - Pilih strategi bobot yang sudah tersedia")
    # Selectbox untuk memilih strategi bobot
    strategi = st.selectbox(
        "Pilih Strategi Bobot",
        [
            "Seimbang (20%, 20%, 20%, 20%, 20%)",
            "Fokus Penumpang (50%, 20%, 10%, 10%, 10%)",
            "Fokus Efisiensi (20%, 50%, 10%, 10%, 10%)",
            "Fokus Konsistensi (15%, 15%, 40%, 15%, 15%)",
            "Fokus Frekuensi (10%, 10%, 10%, 60%, 10%)",
            "Fokus Armada (15%, 15%, 10%, 10%, 50%)"
        ]
    )
    # Jika memilih strategi seimbang
    if strategi == "Seimbang (20%, 20%, 20%, 20%, 20%)":
        bobot = [0.20, 0.20, 0.20, 0.20, 0.20] # Semua kriteria memiliki bobot yang sama
        keterangan = "Semua kriteria dianggap sama penting"
    # Jika memilih fokus penumpang
    elif strategi == "Fokus Penumpang (50%, 20%, 10%, 10%, 10%)":
        bobot = [0.50, 0.20, 0.10, 0.10, 0.10]# Bobot terbesar diberikan ke jumlah penumpang
        keterangan = "Prioritas utama pada jumlah penumpang"
    # Fokus efisiensi
    elif strategi == "Fokus Efisiensi (20%, 50%, 10%, 10%, 10%)":
        bobot = [0.20, 0.50, 0.10, 0.10, 0.10]
        keterangan = "Prioritas pada efisiensi armada"
    # Fokus konsistensi
    elif strategi == "Fokus Konsistensi (15%, 15%, 40%, 15%, 15%)":
        bobot = [0.15, 0.15, 0.40, 0.15, 0.15]
        keterangan = "Prioritas pada konsistensi operasi"
    # Fokus frekuensi
    elif strategi == "Fokus Frekuensi (10%, 10%, 10%, 60%, 10%)":
        bobot = [0.10, 0.10, 0.10, 0.60, 0.10]
        keterangan = "Prioritas pada frekuensi operasional"
    # Fokus armada
    else:
        bobot = [0.15, 0.15, 0.10, 0.10, 0.50]
        keterangan = "Prioritas pada ketersediaan armada"
    
    # Menampilkan bobot yang dipilih
    st.subheader("Bobot yang Dipilih:")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("C1 - Penumpang", f"{bobot[0]*100:.0f}%")
    with col2:
        st.metric("C2 - Efisiensi", f"{bobot[1]*100:.0f}%")
    with col3:
        st.metric("C3 - Konsistensi", f"{bobot[2]*100:.0f}%")
    with col4:
        st.metric("C4 - Frekuensi", f"{bobot[3]*100:.0f}%")
    with col5:
        st.metric("C5 - Armada", f"{bobot[4]*100:.0f}%")
    # Menampilkan penjelasan strategi yang dipilih
    st.caption(f"💡 **Keterangan:** {keterangan}")
    
    return bobot

# ==================== VISUALISASI BOBOT ====================
def visualisasi_bobot(bobot, metode):#perubahan4 (buat fungsi visualisasi bobot dengan pie chart)
    """Visualisasi bobot dalam bentuk pie chart"""
    # Membuat figure dan axis matplotlib
    fig, ax = plt.subplots(figsize=(8, 6))
    
    labels = ['Penumpang', 'Efisiensi', 'Konsistensi', 'Frekuensi', 'Armada']
    colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7']
    explode = (0.05, 0.05, 0.05, 0.05, 0.05) #Memberi efek sedikit keluar pada setiap bagian pie
    
    #Membuat pie chart distribusi bobot
    ax.pie(
        bobot, 
        labels=labels, 
        autopct='%1.1f%%', 
        colors=colors, 
        explode=explode, 
        shadow=True, 
        startangle=90)
    # Memberi judul grafik
    ax.set_title(
        f'Distribusi Bobot Kriteria\n(Metode: {metode})', 
        fontsize=14, 
        fontweight='bold')
    # Mengembalikan figure untuk ditampilkan di streamlit
    return fig

# ==================== HALAMAN DATA ====================
# Jika user memilih halaman Data
if page == "📊 Data":
    # Menampilkan judul halaman
    st.title("📊 Data Operasional Bus Sekolah DKI Jakarta")
    # Memanggil dataset mentah dari file CSV
    df_raw = load_data()

    st.subheader("Dataset Mentah")

    # Menampilkan dataframe dataset mentah
    # use_container_width=True agar tabel menyesuaikan lebar halaman
    st.dataframe(df_raw, use_container_width=True)
    # ==================== STATISTIK DATASET ====================
    st.subheader("Statistik Dataset")
    # Membagi tampilan menjadi 4 kolom untuk menampilkan statistik dasar dataset
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Jumlah Baris", f"{len(df_raw):,}")
    col2.metric("Jumlah Kolom", len(df_raw.columns))
    col3.metric("Jumlah Rute", df_raw['nama_rute'].nunique())
    col4.metric("Periode", "Jan-Mei 2014")
    # ==================== DATA AGREGAT ====================
    st.subheader("Preview Data Agregat per Rute")
    
    # Memanggil fungsi aggregate_data()
    # untuk menghitung nilai kriteria tiap rute
    df_agregat = aggregate_data(df_raw)
    
    # Menampilkan data hasil agregasi dengan kriteria yang sudah dihitung
    st.dataframe(df_agregat, use_container_width=True)

# ==================== HALAMAN HITUNG WP ====================
# Jika user memilih halaman Hitung WP
elif page == "⚙️ Hitung WP":
    st.title("⚙️ Perhitungan Weighted Product")
    st.markdown("---") #perubahan5 (buat garis pemisah)
    # ==================== LOAD DATA ====================
    # Memanggil dataset mentah
    df_raw = load_data()

    # Mengubah dataset mentah menjadi data agregat, agar bisa digunakan dalam perhitungan WP
    df_agregat = aggregate_data(df_raw)
    
    # ==================== TAMPILKAN MATRKS KEPUTUSAN ====================
    st.subheader("📋 Matriks Keputusan (Nilai Kriteria per Rute)")
    
    # Menampilkan dataframe nilai kriteria tiap rute yang sudah dihitung di halaman Data, agar user bisa melihat data yang akan digunakan dalam perhitungan WP
    st.dataframe(df_agregat, use_container_width=True)
    
    st.markdown("---") #perubahan6 (buat garis pemisah)
    
    # ============ PILIH METODE INPUT BOBOT ============
    st.subheader("🎚️ Input Bobot Kriteria")
    st.write("Semua kriteria bersifat **Benefit** (semakin tinggi semakin baik)")
    #perubahan7 (buat pilihan metode input bobot)
    # Radio button untuk memilih metode input bobot
    metode_input = st.radio(
        "Silakan pilih metode yang ingin digunakan:",
        ["🎚️ Slider (Geser untuk mengatur bobot)", 
        "🔢 Number Input (Ketik nilai presisi)", 
        "📋 Preset (Pilih strategi yang tersedia)"]
    )
    
    st.markdown("---")
    
    # ==================== PILIH METODE INPUT ====================
    if metode_input == "🎚️ Slider (Geser untuk mengatur bobot)":
        bobot = input_bobot_slider()
        metode_terpilih = "Slider"
        
    elif metode_input == "🔢 Number Input (Ketik nilai presisi)":
        bobot = input_bobot_number()
        metode_terpilih = "Number Input"
        
    else:  # Preset
        bobot = input_bobot_preset()
        metode_terpilih = "Preset"
    
    # ==================== VALIDASI BOBOT ====================
    # Menjumlahkan seluruh bobot untuk memastikan totalnya 1.00
    total_bobot = sum(bobot)
    
    st.markdown("---")
    st.subheader("📊 Ringkasan Bobot")
    # Membagi tampilan menjadi 3 kolom
    col1, col2, col3 = st.columns(3)
    # Menampilkan total bobot
    with col1:
        st.metric("Total Bobot", f"{total_bobot:.3f}")
    # Validasi apakah total bobot = 1
    with col2:
        # abs() digunakan untuk menghindari error pembulatan desimal
        if abs(total_bobot - 1.0) < 0.01:
            st.success("✅ STATUS: VALID (Total = 1.00)")
        else:
            st.error(f"❌ STATUS: INVALID (Total harus 1.00, saat ini {total_bobot:.3f})")
    # Menampilkan metode input yang digunakan
    with col3:
        st.metric("Metode Input", metode_terpilih)
    
    # ==================== VISUALISASI BOBOT ====================
    # Pie chart hanya ditampilkan jika total bobot valid
    if abs(total_bobot - 1.0) < 0.01:
        # Memanggil fungsi visualisasi pie chart untuk menampilkan distribusi bobot yang dipilih user
        fig_bobot = visualisasi_bobot(bobot, metode_terpilih)
        # Menampilkan grafik ke streamlit
        st.pyplot(fig_bobot)
    
    st.markdown("---")
    
    # ==================== TOMBOL EKSEKUSI HITUNG WP ====================
    if st.button("🚀 Hitung WP", type="primary"):
        if total_bobot != 1.0:
            st.error("Total bobot tidak 1.00, silakan sesuaikan!")
        else:
            # Memanggil fungsi hitung_wp()
            # menghasilkan dataframe hasil dan normalisasi berdasarkan data agregat dan bobot yang diinput user
            df_hasil, df_normalisasi = hitung_wp(df_agregat, bobot)
            
            # ==================== TABEL HASIL RANKING ====================
            st.subheader("🏆 Hasil Perangkingan Rute Bus Sekolah")
            
            kolom_tampil = ['nama_rute', 'V', 'Ranking']
            df_ranking = df_hasil[kolom_tampil].copy() # copy() digunakan agar perubahan tidak memengaruhi dataframe asli
            df_ranking['V'] = df_ranking['V'].apply(lambda x: f"{x:.6f}") # apply(lambda) digunakan untuk mengatur format desimal nilai V
            st.dataframe(df_ranking, use_container_width=True)
            
            # ==================== TABEL LENGKAP ====================
            # Expander digunakan agar tabel lengkap bisa dibuka/tutup
            with st.expander("📊 Lihat Tabel Lengkap (Normalisasi + S + V)"):
                # Menampilkan seluruh hasil perhitungan
                st.dataframe(df_hasil, use_container_width=True)
            
            # ==================== GRAFIK 1: BAR CHART RANKING (Matplotlib) ====================
            st.subheader("📊 Visualisasi Hasil")
            # Membuat figure dan axis matplotlib untuk bar chart ranking
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            top10 = df_hasil.head(10) # Mengambil 10 rute terbaik
            warna = ['green' if i == 0 else 'steelblue' for i in range(len(top10))] # Memberi warna hijau untuk ranking 1 dan biru untuk lainnya
            ax1.barh(top10['nama_rute'], top10['V'], color=warna) # Membuat horizontal bar chart
            ax1.set_xlabel('Nilai Preferensi (V)') # Label sumbu X
            ax1.set_ylabel('Nama Rute')# Label sumbu Y
            ax1.set_title('Top 10 Rute Bus Sekolah Terbaik')
            ax1.invert_yaxis() # Membalik urutan agar ranking 1 berada di atas
            # ==================== LABEL NILAI BAR ====================
            # Menambahkan label angka di samping bar untuk menunjukkan nilai V dengan format 5 desimal, agar nilai preferensi tiap rute lebih mudah dibaca
            for i, (idx, row) in enumerate(top10.iterrows()):
                ax1.text(row['V'] + 0.001,
                i, 
                f"{row['V']:.5f}", 
                va='center')
            # Menampilkan grafik ke streamlit
            st.pyplot(fig1)
            
            # ==================== GRAFIK 2: PERBANDINGAN KRITERIA (Matplotlib) ====================
            # Membuat figure dan axis untuk grafik kedua
            fig2, ax2 = plt.subplots(figsize=(12, 6))
            # Mengambil 5 rute terbaik berdasarkan ranking
            top5 = df_hasil.head(5)

            kriteria = ['C1_Rata2Penumpang', 'C2_EfisiensiArmada', 'C3_Konsistensi', 'C4_Frekuensi', 'C5_Rata2Bus']
            kriteria_labels = ['Rata2 Penumpang', 'Efisiensi', 'Konsistensi', 'Frekuensi', 'Rata2 Bus']
            
            # ==================== NORMALISASI UNTUK VISUALISASI ====================
            # np.arange(len(kriteria)) membuat array posisi sumbu X
            # contoh hasil: [0,1,2,3,4]
            x = np.arange(len(kriteria))

            # Lebar masing-masing bar chart
            lebar = 0.15

            # Warna untuk tiap rute dalam grafik perbandingan kriteria
            warna_bar = ['#e74c3c', '#e67e22', '#f1c40f', '#2ecc71', '#3498db']
            # Looping untuk setiap rute pada top 5
            for i, (idx, row) in enumerate(top5.iterrows()):
                nilai_asli = [row[k] for k in kriteria] # Mengambil nilai asli tiap kriteria dari rute
                max_per_kriteria = [df_agregat[k].max() for k in kriteria] # Mengambil nilai maksimum tiap kriteria,digunakan untuk normalisasi visualisasi
                nilai_normalisasi = [nilai_asli[j]/max_per_kriteria[j] if max_per_kriteria[j] > 0 else 0 for j in range(len(kriteria))]  # Normalisasi nilai agar berada pada rentang 0-1,nilai dibagi nilai maksimum per kriteria untuk memastikan perbandingan yang adil antar kriteria, karena skala tiap kriteria bisa berbeda-beda. Jika nilai maksimum per kriteria adalah 0, maka nilai normalisasi diatur menjadi 0 untuk menghindari pembagian dengan nol.
                ax2.bar(
                    x + i*lebar, 
                    nilai_normalisasi, 
                    lebar, 
                    label=row['nama_rute'], 
                    color=warna_bar[i % len(warna_bar)])  # Membuat grouped bar chart, x + i*lebar digunakan agar bar tiap rute tidak bertumpuk melainkan berdampingan, lebar adalah lebar masing-masing bar, label digunakan untuk legenda, dan warna diambil dari daftar warna_bar dengan indeks i yang diulang jika lebih dari jumlah warna yang tersedia.
            
            ax2.set_xlabel('Kriteria')
            ax2.set_ylabel('Nilai Ternormalisasi')
            ax2.set_title('Perbandingan 5 Rute Terbaik per Kriteria')
            ax2.set_xticks(x + lebar * 2) # Mengatur posisi label sumbu X agar berada di tengah grup bar
            ax2.set_xticklabels(kriteria_labels, rotation=45, ha='right') # Menampilkan nama label kriteria pada sumbu X, rotation=45 agar tulisan miring dan tidak bertumpuk
            ax2.legend(loc='upper right')
            ax2.set_ylim(0, 1.1) # Mengatur batas maksimum sumbu Y agar grafik lebih proporsional, karena nilai normalisasi berada pada rentang 0-1, maka batas atas diatur sedikit di atas 1 untuk memberikan ruang visual yang lebih baik.
            st.pyplot(fig2)
            
            # ==================== GRAFIK 3: LINE CHART PERBANDINGAN NILAI V ====================
            # Membuat figure dan axis grafik ketiga
            fig3, ax3 = plt.subplots(figsize=(12, 5))
            all_rutes = df_hasil['nama_rute'].tolist()# Mengubah nama rute menjadi list
            all_v = df_hasil['V'].tolist() # Mengubah nilai V menjadi list
            # Membuat line chart nilai V seluruh rute
            ax3.plot(
                all_rutes, 
                all_v, 
                marker='o', 
                linestyle='-', 
                linewidth=2, 
                markersize=6, 
                color='steelblue')
            ax3.set_xlabel('Nama Rute')
            ax3.set_ylabel('Nilai Preferensi (V)')
            ax3.set_title('Perbandingan Nilai V untuk Semua Rute')
            ax3.tick_params(axis='x', rotation=90) # Memutar label sumbu X agar tidak bertumpuk dan lebih mudah dibaca, karena nama rute bisa panjang dan banyak, sehingga memutar label akan membantu menghindari tumpang tindih dan meningkatkan keterbacaan grafik.
            ax3.grid(True, alpha=0.3) # Menampilkan grid pada grafik, alpha digunakan untuk mengatur transparansi grid agar tidak terlalu dominan namun tetap membantu dalam membaca nilai pada grafik.
            
            #==================== MENANDAI RUTE TERBAIK ====================
            max_idx = all_v.index(max(all_v)) # Mencari index nilai V terbesar
            # Menandai titik rute terbaik dengan warna merah
            ax3.plot(
                max_idx, 
                all_v[max_idx], 
                'ro', #red circle marker
                markersize=10, 
                label=f"Terbaik: {all_rutes[max_idx]}")
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
    | **Mata Kuliah** | Pratikum Sistem Cerdas dan Pengambilan Keputusan (SCPK) |
    | **Metode** | Weighted Product (WP) |
    | **Sumber Data** | Data Operasi Bus Dan Penumpang Bus Sekolah Di DKI Jakarta |
    | **Periode Data** | Januari - Mei 2014 |
    """)
    
    st.subheader("Anggota Kelompok")

    # Penjelasan proses pengerjaan project
    st.write("""
    Pada awal pengerjaan, seluruh anggota bersama-sama menyusun alur,
    konsep, dan pengembangan project. Setelah itu dilakukan pembagian
    tugas untuk finalisasi project. Setelah itu kelompok melakukan sinkronisasi untuk memastikan semua bagian berjalan dengan baik dan terintegrasi dengan lancar serta pengujian aplikasi untuk memastikan hasil perhitungan WP sesuai dengan yang diharapkan.
    """)
    anggota = pd.DataFrame({
        "Nama": ["Nayla Saskia Zallianti", "Aulya Revalina"],
        "NIM": ["123240016", "123240141"],
        "Peran": ["Desain antarmuka aplikasi, visualisasi grafik","Implementasi logika sistem, perhitungan WP "]
    })
    st.dataframe(anggota, use_container_width=True)
    
    st.subheader("Kriteria yang Digunakan")
    kriteria_df = pd.DataFrame({
        "Kode": ["C1", "C2", "C3", "C4", "C5"],
        "Kriteria": ["Rata-rata Penumpang", "Efisiensi Armada", "Konsistensi Operasi", "Frekuensi Operasional", "Rata-rata Bus per Hari"],
        "Jenis": ["Benefit"] * 5,
        "Bobot Default": [0.35, 0.25, 0.20, 0.10, 0.10]
    })
    st.dataframe(kriteria_df, use_container_width=True)
    
    st.subheader("Tentang Project Penentuan Rute Bus Sekolah Paling Efektif Berdasarkan Data Operasional Menggunakan Metode Weighted Product.")
    st.write("""
    Aplikasi ini dibangun menggunakan:
    - **Streamlit** untuk antarmuka GUI
    - **Pandas & NumPy** untuk pengolahan data
    - **Matplotlib** untuk visualisasi
    - **Metode Weighted Product** untuk perhitungan SPK
    """)