import streamlit as st
import pandas as pd
from datetime import datetime
import io
import re

st.set_page_config(page_title="Siklus Akuntansi Dagang", layout="wide")
st.title("📈 Aplikasi Siklus Akuntansi Perusahaan Dagang")
st.markdown("Gunakan sidebar di sebelah kiri untuk input transaksi dan lihat laporan lengkap.")

if "jurnal" not in st.session_state:
    st.session_state.jurnal = pd.DataFrame(columns=["Tanggal","Akun","Debit","Kredit","Keterangan"])
if "jurnal_penyesuaian" not in st.session_state:
    st.session_state.jurnal_penyesuaian = pd.DataFrame(columns=["Tanggal","Akun","Debit","Kredit","Keterangan"])

# Sidebar - Input Transaksi
st.sidebar.header("📝 Input Transaksi")
tgl = st.sidebar.date_input("Tanggal", datetime.today())
akun_debit = st.sidebar.text_input("Akun Debit")
jumlah_debit = st.sidebar.number_input("Jumlah Debit", min_value=0.0, format="%.2f")
akun_kredit = st.sidebar.text_input("Akun Kredit")
kredit = st.sidebar.number_input("Jumlah Kredit", min_value=0.0, format="%.2f")
keterangan = st.sidebar.text_input("Keterangan")

if st.sidebar.button("Tambah Transaksi"):
    if jumlah_debit != kredit:
        st.sidebar.error("Jumlah debit dan kredit harus sama!")
    else:
        entries = pd.DataFrame([
            {"Tanggal": tgl, "Akun": akun_debit, "Debit": jumlah_debit, "Kredit": 0.0, "Keterangan": keterangan},
            {"Tanggal": tgl, "Akun": akun_kredit, "Debit": 0.0, "Kredit": kredit, "Keterangan": keterangan}
        ])
        st.session_state.jurnal = pd.concat([st.session_state.jurnal, entries], ignore_index=True)
        st.sidebar.success("Transaksi berhasil ditambahkan.")

# Fungsi Buku Besar
def buku_besar(df):
    ledger = {}
    for akun in df['Akun'].unique():
        df_akun = df[df['Akun'] == akun].copy()
        df_akun.sort_values(by="Tanggal", inplace=True)
        df_akun['Mutasi'] = df_akun['Debit'] - df_akun['Kredit']
        df_akun['Saldo Akhir'] = df_akun['Mutasi'].cumsum()
        ledger[akun] = df_akun
    return ledger

# Fungsi Neraca Saldo
def neraca_saldo(ledger_dict):
    ns = []
    for akun, df in ledger_dict.items():
        akhir = df['Saldo Akhir'].iloc[-1] if not df.empty else 0
        ns.append({"Akun": akun, "Debit": max(akhir, 0), "Kredit": max(-akhir, 0)})
    return pd.DataFrame(ns, columns=["Akun", "Debit", "Kredit"])

# 1. Jurnal Umum
st.subheader("1. 📒 Jurnal Umum")
st.dataframe(st.session_state.jurnal)

# 2. Buku Besar
st.subheader("2. 📚 Buku Besar")
ledger = buku_besar(st.session_state.jurnal)
for akun, df in ledger.items():
    with st.expander(f"Akun: {akun}"):
        st.dataframe(df)

# 3. Neraca Saldo Awal
st.subheader("3. 📊 Neraca Saldo Awal")
ns_awal = neraca_saldo(ledger)
st.dataframe(ns_awal)

# 4. Jurnal Penyesuaian
st.subheader("4. 🔧 Jurnal Penyesuaian")
with st.expander("Input Jurnal Penyesuaian"):
    tgl_adj = st.date_input("Tanggal Penyesuaian", datetime.today(), key='tgl_adj')
    akun_debit_adj = st.text_input("Akun Debit Penyesuaian", key='akun_debit_adj')
    akun_kredit_adj = st.text_input("Akun Kredit Penyesuaian", key='akun_kredit_adj')
    jumlah_adj = st.number_input("Jumlah Penyesuaian", min_value=0.0, format="%.2f", key='jumlah_adj')
    ket_adj = st.text_input("Keterangan Penyesuaian", key='ket_adj')
    if st.button("Tambah Penyesuaian", key='btn_tambah_penyesuaian'):
        if jumlah_adj > 0 and akun_debit_adj and akun_kredit_adj:
            adj_entries = pd.DataFrame([
                {"Tanggal": tgl_adj, "Akun": akun_debit_adj, "Debit": jumlah_adj, "Kredit": 0.0, "Keterangan": ket_adj},
                {"Tanggal": tgl_adj, "Akun": akun_kredit_adj, "Debit": 0.0, "Kredit": jumlah_adj, "Keterangan": ket_adj}
            ])
            st.session_state.jurnal_penyesuaian = pd.concat([st.session_state.jurnal_penyesuaian, adj_entries], ignore_index=True)
            st.success("Jurnal penyesuaian berhasil ditambahkan.")
        else:
            st.error("Isi semua field dengan benar.")
st.dataframe(st.session_state.jurnal_penyesuaian)

# 5. Neraca Saldo Disesuaikan
st.subheader("5. 📈 Neraca Saldo Setelah Penyesuaian")
all_journal = pd.concat([st.session_state.jurnal, st.session_state.jurnal_penyesuaian], ignore_index=True)
ledger_adj = buku_besar(all_journal)
ns_disesuaikan = neraca_saldo(ledger_adj)
st.dataframe(ns_disesuaikan)

# 6. Laporan Laba Rugi
st.subheader("6. 📉 Laporan Laba Rugi")
pendapatan = ns_disesuaikan.loc[ns_disesuaikan['Akun'].str.contains("Pendapatan", case=False), 'Kredit'].sum()
beban = ns_disesuaikan.loc[ns_disesuaikan['Akun'].str.contains("Beban", case=False), 'Debit'].sum()
laba_bersih = pendapatan - beban
st.write(f"**Total Pendapatan:** Rp {pendapatan:,.2f}")
st.write(f"**Total Beban:** Rp {beban:,.2f}")
st.write(f"### ➕ Laba Bersih: Rp {laba_bersih:,.2f}")

# 7. Laporan Perubahan Modal
st.subheader("7. 🔄 Laporan Perubahan Modal")
modal_awal = st.number_input("Modal Awal", value=0.0)
prive = st.number_input("Prive", value=0.0)
modal_akhir = modal_awal + laba_bersih - prive
st.write(f"### 🧮 Modal Akhir: Rp {modal_akhir:,.2f}")

# 8. Neraca
st.subheader("8. 🧾 Neraca")
aktiva = ns_disesuaikan.loc[ns_disesuaikan['Akun'].str.contains("Kas|Piutang|Persediaan", case=False), 'Debit'].sum()
kewajiban = ns_disesuaikan.loc[ns_disesuaikan['Akun'].str.contains("Utang", case=False), 'Kredit'].sum()
col1, col2 = st.columns(2)
with col1:
    st.write(f"**Total Aktiva:** Rp {aktiva:,.2f}")
with col2:
    st.write(f"**Total Kewajiban + Modal:** Rp {kewajiban + modal_akhir:,.2f}")

# 9. Jurnal Penutup
st.subheader("9. 🛑 Jurnal Penutup")
def buat_jurnal_penutup():
    penutup = []
    if pendapatan > 0:
        penutup += [
            {"Akun": "Pendapatan Penjualan", "Debit": pendapatan, "Kredit": 0.0, "Keterangan": "Tutup pendapatan"},
            {"Akun": "Ikhtisar Laba Rugi", "Debit": 0.0, "Kredit": pendapatan, "Keterangan": "Tutup pendapatan"}
        ]
    if beban > 0:
        penutup += [
            {"Akun": "Ikhtisar Laba Rugi", "Debit": beban, "Kredit": 0.0, "Keterangan": "Tutup beban"},
            {"Akun": "Beban", "Debit": 0.0, "Kredit": beban, "Keterangan": "Tutup beban"}
        ]
    if laba_bersih != 0:
        penutup += [
            {"Akun": "Ikhtisar Laba Rugi", "Debit": laba_bersih, "Kredit": 0.0, "Keterangan": "Tutup laba ke modal"},
            {"Akun": "Modal", "Debit": 0.0, "Kredit": laba_bersih, "Keterangan": "Tutup laba ke modal"}
        ]
    return pd.DataFrame(penutup)

jpenutup = buat_jurnal_penutup()
st.dataframe(jpenutup)

# 10. Neraca Setelah Penutupan
st.subheader("10. 📌 Neraca Saldo Setelah Penutupan")
final_journal = pd.concat([all_journal, jpenutup], ignore_index=True)
ledger_final = buku_besar(final_journal)
ns_akhir = neraca_saldo(ledger_final)
st.dataframe(ns_akhir)

# Export ke Excel
st.subheader("📤 Ekspor Data Keuangan ke Excel")
output = io.BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    st.session_state.jurnal.to_excel(writer, sheet_name="Jurnal Umum", index=False)
    st.session_state.jurnal_penyesuaian.to_excel(writer, sheet_name="Jurnal Penyesuaian", index=False)
    ns_awal.to_excel(writer, sheet_name="Neraca Saldo Awal", index=False)
    ns_disesuaikan.to_excel(writer, sheet_name="Neraca Disesuaikan", index=False)
    jpenutup.to_excel(writer, sheet_name="Jurnal Penutup", index=False)
    ns_akhir.to_excel(writer, sheet_name="Neraca Setelah Penutupan", index=False)

    pd.DataFrame({
        "Keterangan": ["Pendapatan", "Beban", "Laba Bersih"],
        "Jumlah": [pendapatan, beban, laba_bersih]
    }).to_excel(writer, sheet_name="Laba Rugi", index=False)

    pd.DataFrame({
        "Keterangan": ["Modal Awal", "Laba Bersih", "Prive", "Modal Akhir"],
        "Jumlah": [modal_awal, laba_bersih, prive, modal_akhir]
    }).to_excel(writer, sheet_name="Perubahan Modal", index=False)

    pd.DataFrame({
        "Keterangan": ["Total Aktiva", "Total Kewajiban + Modal"],
        "Jumlah": [aktiva, kewajiban + modal_akhir]
    }).to_excel(writer, sheet_name="Neraca", index=False)

    # Buku Besar
    for akun, df_akun in ledger_adj.items():
        safe_sheet = re.sub(r'[\[\]:\\/*?]', '_', akun)[:31]
        df_akun.to_excel(writer, sheet_name=f"Buku - {safe_sheet}", index=False)

    writer.close()
    output.seek(0)

st.download_button(
    label="⬇️ Unduh Laporan Lengkap (Excel)",
    data=output,
    file_name="laporan_keuangan_dagang_lengkap.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.markdown("---")
st.caption("BISMILLAH, BAPAK ATTA KASIH KITA NILAI A.")
