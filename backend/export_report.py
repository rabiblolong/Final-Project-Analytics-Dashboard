import pandas as pd, io
from datetime import datetime

TEAM = [
    {"name": "Ignasius Rabi Blolong",     "role_id": "Ketua · Backend Flask & Statistik Numerik",    "role_en": "Chair · Flask Backend & Numerical Statistics",
     "task_id": "Mengembangkan backend Flask, routing aplikasi, dan modul statistik deskriptif numerik.",
     "task_en": "Developed the Flask backend, application routing, and the numerical descriptive statistics module."},
    {"name": "Ni Md Aurora Sekarningrum","role_id": "Frontend & UI/UX, Data Management",             "role_en": "Frontend & UI/UX, Data Management",
     "task_id": "Membangun antarmuka dashboard (index.html) dan modul pemuatan data (data_loader.py).",
     "task_en": "Built the dashboard interface (index.html) and the data loading module (data_loader.py)."},
    {"name": "Adinda Maiza Ishfahani",   "role_id": "Analisis Kategorikal & Visualisasi",            "role_en": "Categorical Analysis & Visualization",
     "task_id": "Mengembangkan modul analisis kategorikal dan visualisasi interaktif.",
     "task_en": "Developed the categorical analysis module and interactive visualizations."},
    {"name": "Chricyesia W. F. Uvas",   "role_id": "Statistics Engine & UI Components",             "role_en": "Statistics Engine & UI Components",
     "task_id": "Mengembangkan modul statistik deskriptif dan komponen UI pendukung.",
     "task_en": "Developed the descriptive statistics module and supporting UI components."},
    {"name": "Januaria Teresinha",       "role_id": "Setup, Dokumentasi, Time Series & Export",      "role_en": "Setup, Documentation, Time Series & Export",
     "task_id": "Menyusun dokumentasi proyek, modul time series, dan fitur export laporan.",
     "task_en": "Prepared project documentation, the time series module, and the report export feature."},
]

LECTURER = "Bakti Siregar, M.Sc."

# ════════════════════════════════════════════════════════════════════════════
# i18n text — every chapter has a short, formal human-language introduction
# ════════════════════════════════════════════════════════════════════════════
_T = {
  'id': {
    'report_title':'Laporan Analisis Data (Exploratory Data Analysis)',
    'app_name':'Auto EDA Analytics Dashboard',
    'subtitle':'SD-1306 Final Project',
    'dataset_label':'Dataset','generated_label':'Tanggal Generate',
    'group_label':'Kelompok 6 · Kelas B · Institut Teknologi Sains Bandung (ITSB)',
    'lecturer_label':'Dosen Pengampu',

    # ── BAB I — Pendahuluan, EDA, Tim ──────────────────────────────────────
    'bab1_title':'BAB I — Pendahuluan',
    'bab1_intro':'Bab ini menjelaskan latar belakang dan tujuan pembuatan aplikasi Auto EDA Analytics Dashboard, '
                 'pengertian dasar mengenai Exploratory Data Analysis (EDA) sebagai metode yang digunakan, '
                 'serta susunan tim pengembang beserta pembagian tugas masing-masing anggota.',
    's11_title':'1.1 Latar Belakang & Tentang Aplikasi',
    's11_text':'Dalam praktik analisis data, tahap awal yang krusial sebelum membangun model atau mengambil keputusan '
               'adalah memahami karakteristik data itu sendiri. Proses ini sering memakan waktu apabila dilakukan '
               'secara manual. <b>Auto EDA Analytics Dashboard</b> dikembangkan untuk menjawab kebutuhan tersebut — '
               'sebuah aplikasi web berbasis Flask yang memungkinkan pengguna melakukan Exploratory Data Analysis '
               'secara otomatis dan interaktif. Pengguna hanya perlu mengunggah berkas dataset (CSV, Excel, TXT, TSV, '
               'atau JSON), dan sistem akan secara otomatis mendeteksi tipe setiap kolom, melakukan pembersihan data, '
               'menghitung statistik deskriptif, menyajikan empat belas jenis visualisasi interaktif, serta menghasilkan '
               'wawasan analitis (insight) yang relevan untuk pengambilan keputusan. Aplikasi ini dirancang agar dapat '
               'menyesuaikan diri secara otomatis terhadap berbagai jenis dataset yang diunggah, sehingga proses '
               'eksplorasi data dapat dilakukan dengan mudah tanpa memerlukan konfigurasi manual dari pengguna.',
    's12_title':'1.2 Pengertian Exploratory Data Analysis (EDA)',
    's12_text':'Exploratory Data Analysis (EDA) adalah suatu pendekatan dalam menganalisis dataset yang bertujuan '
               'untuk merangkum karakteristik utamanya, umumnya dengan bantuan metode visual maupun statistik '
               'sederhana. Melalui EDA, seorang analis dapat mengidentifikasi pola, mendeteksi anomali atau outlier, '
               'menguji asumsi awal terhadap data, serta memeriksa hubungan antar variabel sebelum melangkah ke tahap '
               'pemodelan yang lebih kompleks. Pada aplikasi ini, proses EDA dilaksanakan melalui beberapa tahapan '
               'yang saling berurutan, yaitu pembersihan data (data cleaning), penghitungan statistik deskriptif, '
               'visualisasi data, hingga penyusunan wawasan otomatis (smart insight) yang siap digunakan sebagai '
               'bahan pertimbangan pengambilan keputusan.',
    's13_title':'1.3 Tim Pengembang',
    's13_text':'Aplikasi ini disusun sebagai bagian dari tugas akhir (final project) mata kuliah SD-1306 Programming '
               'for Data Science, dikerjakan oleh Kelompok 6 Kelas B, di bawah bimbingan dosen pengampu '
               '<b>{lecturer}</b>. Pembagian tugas dalam pengembangan aplikasi ini disusun sebagai berikut:',
    'col_name':'Nama','col_role':'Peran','col_task':'Tugas Singkat',

    # ── BAB II — Statistik Deskriptif ──────────────────────────────────────
    'bab2_title':'BAB II — Statistik Deskriptif',
    'bab2_intro':'Bab ini menyajikan hasil pengolahan data dalam bentuk angka, mencakup ringkasan ukuran dataset, '
                 'evaluasi kualitas data (missing value, duplikat, dan outlier), pratinjau isi dataset, serta tabel '
                 'statistik deskriptif lengkap untuk variabel numerik maupun kategorikal. Bagian ini menjadi dasar '
                 'kuantitatif sebelum dilakukan visualisasi dan interpretasi lebih lanjut pada bab berikutnya.',
    's21_title':'2.1 Ringkasan Dataset','s22_title':'2.2 Evaluasi Kualitas Data',
    's23_title':'2.3 Pratinjau Dataset (5 Baris Pertama)',
    's24_title':'2.4 Tabel Statistik Deskriptif',
    'kpi_rows':'Total Baris','kpi_cols':'Total Kolom','kpi_num':'Var. Numerik','kpi_cat':'Var. Kategorikal',
    'kpi_missing':'Total Missing','kpi_missing_pct':'Missing %','kpi_dup':'Duplikat','kpi_out':'Outlier',
    'quality_clean':'Berdasarkan hasil evaluasi, data dinyatakan dalam kondisi bersih — tidak ditemukan missing value, duplikat, maupun outlier yang signifikan.',
    'quality_issue':'Berdasarkan hasil evaluasi, data masih memiliki beberapa isu kualitas yang perlu diperhatikan, sebagaimana dijabarkan pada rincian berikut.',
    'quality_mv_head':'Rincian Missing Value per Kolom:','quality_out_head':'Rincian Outlier per Kolom (Metode IQR):',
    'tbl_metric':'Metrik','tbl_num':'Tabel 2.1 — Statistik Deskriptif Variabel Numerik','tbl_cat':'Tabel 2.2 — Statistik Deskriptif Variabel Kategorikal',

    # ── BAB III — Visualisasi ──────────────────────────────────────────────
    'bab3_title':'BAB III — Visualisasi Data',
    'bab3_intro':'Bab ini menampilkan grafik-grafik utama hasil visualisasi data yang dihasilkan secara otomatis '
                 'oleh sistem. Visualisasi disajikan dalam empat kategori, yaitu: (a) visualisasi numerik untuk '
                 'menggambarkan distribusi nilai pada setiap variabel angka, (b) visualisasi kategorikal untuk '
                 'menggambarkan proporsi tiap kategori, (c) visualisasi bivariate dan multivariate untuk melihat '
                 'pola hubungan antar variabel numerik, serta (d) visualisasi kategorikal terhadap numerik untuk '
                 'membandingkan nilai numerik antar kategori. Keseluruhan visualisasi interaktif (14 jenis grafik, '
                 'dengan opsi pemilihan jenis chart dan warna) dapat diakses secara penuh melalui halaman '
                 'Visualisasi pada dashboard.',
    'viz_a':'(a) Visualisasi Numerik','viz_b':'(b) Visualisasi Kategorikal',
    'viz_c':'(c) Bivariate & Multivariate','viz_d':'(d) Kategorikal vs Numerik',
    'viz_none':'Visualisasi belum digenerate pada saat laporan ini dibuat. Silakan buka halaman Visualisasi pada dashboard untuk melihat seluruh 14 jenis grafik secara interaktif.',

    # ── BAB IV — Smart Insight & Rekomendasi ───────────────────────────────
    'bab4_title':'BAB IV — Smart Insight & Rekomendasi',
    'bab4_intro':'Bab ini menyajikan narasi analitis tingkat lanjut yang disusun khusus untuk kebutuhan pimpinan '
                 'dan pemangku kepentingan (stakeholder) dalam pengambilan keputusan bisnis. Berbeda dengan bab '
                 'sebelumnya yang bersifat deskriptif, bagian ini menafsirkan temuan-temuan penting dalam data — '
                 'termasuk kondisi kualitas data, karakteristik tiap variabel, pola hubungan antar variabel — '
                 'serta menyusunnya menjadi rekomendasi tindak lanjut yang konkret dan dapat segera diterapkan.',
    's41_title':'4.1 Ringkasan Eksekutif (Executive Summary)',
    's42_title':'4.2 Temuan Utama (Key Findings)',
    's43_title':'4.3 Wawasan Variabel Numerik',
    's44_title':'4.4 Wawasan Variabel Kategorikal',
    's45_title':'4.5 Hubungan Antar Variabel (Korelasi)',
    's46_title':'4.6 Rekomendasi Tindak Lanjut',
    'no_findings':'Tidak ditemukan temuan kritis pada data ini.',
    'no_corr':'Tidak ditemukan korelasi yang signifikan antar variabel numerik pada dataset ini.',
    'no_rec':'Tidak ada rekomendasi tambahan — data dan hasil analisis sudah dalam kondisi optimal.',
    'sev_critical':'KRITIS','sev_high':'TINGGI','sev_medium':'SEDANG','sev_low':'RENDAH','sev_info':'INFORMASI',
    'pri_segera':'SEGERA','pri_jangka_pendek':'JANGKA PENDEK','pri_jangka_panjang':'JANGKA PANJANG',
    'pri_immediate':'SEGERA','pri_short_term':'JANGKA PENDEK','pri_long_term':'JANGKA PANJANG',
    'impact_label':'Dampak terhadap keputusan bisnis:','rationale_label':'Alasan:',
    'source_ai':'Insight dihasilkan oleh AI (Claude)','source_rule':'Insight dihasilkan secara rule-based',

    # ── BAB V — Penutup ─────────────────────────────────────────────────────
    'bab5_title':'BAB V — Penutup',
    'bab5_intro':'Bab ini merupakan bagian akhir dari laporan yang menyajikan kesimpulan dari keseluruhan proses '
                 'analisis data yang telah dilakukan, serta saran tindak lanjut yang dapat dipertimbangkan oleh '
                 'pengguna maupun pemangku kepentingan terkait.',
    's51_title':'5.1 Kesimpulan',
    's51_text':'Berdasarkan proses analisis yang telah dilakukan, dataset <b>{fname}</b> berhasil diolah dengan '
               'total {rows} baris dan {cols} kolom, terdiri dari {num} variabel numerik dan {cat} variabel '
               'kategorikal. Proses Exploratory Data Analysis yang dijalankan mencakup evaluasi kualitas data, '
               'penghitungan statistik deskriptif, visualisasi data dalam berbagai bentuk grafik, hingga penyusunan '
               'wawasan analitis (smart insight) dan rekomendasi tindak lanjut. Secara keseluruhan, laporan ini '
               'memberikan gambaran yang komprehensif mengenai karakteristik data, kondisi kualitasnya, serta pola '
               'hubungan antar variabel yang dapat menjadi dasar pertimbangan dalam pengambilan keputusan.',
    's52_title':'5.2 Saran',
    's52_items':[
      'Apabila masih ditemukan missing value, duplikat, atau outlier yang signifikan, disarankan untuk melakukan pembersihan data lebih lanjut melalui halaman Pembersihan Data pada dashboard.',
      'Untuk eksplorasi visual yang lebih mendalam, pengguna dapat memanfaatkan halaman Visualisasi dengan memilih jenis grafik dan skema warna sesuai kebutuhan analisis.',
      'Halaman Smart Insight & Rekomendasi dapat dijadikan acuan utama dalam menentukan langkah analisis atau pemodelan lanjutan yang akan diambil.',
      'Hasil analisis pada laporan ini dapat dijadikan dasar awal sebelum melakukan pemodelan statistik atau machine learning lanjutan, seperti regresi, klasifikasi, maupun clustering.',
    ],
    'footer':'Laporan ini dihasilkan secara otomatis oleh Auto EDA Analytics Dashboard — SD-1306 Final Project<br>'
             'Kelompok 6 · Kelas B · Institut Teknologi Sains Bandung (ITSB) · Dosen Pengampu: {lecturer}',
  },
  'en': {
    'report_title':'Data Analysis Report (Exploratory Data Analysis)',
    'app_name':'Auto EDA Analytics Dashboard',
    'subtitle':'SD-1306 Final Project',
    'dataset_label':'Dataset','generated_label':'Generated on',
    'group_label':'Group 6 · Class B · Institut Teknologi Sains Bandung (ITSB)',
    'lecturer_label':'Lecturer',

    'bab1_title':'CHAPTER I — Introduction',
    'bab1_intro':'This chapter explains the background and purpose of the Auto EDA Analytics Dashboard application, '
                 'the basic concept of Exploratory Data Analysis (EDA) used as its underlying method, and the '
                 'development team along with each member\'s assigned responsibilities.',
    's11_title':'1.1 Background & About the Application',
    's11_text':'In data analysis practice, a crucial early step before building models or making decisions is '
               'understanding the characteristics of the data itself. This process is often time-consuming when '
               'done manually. <b>Auto EDA Analytics Dashboard</b> was developed to address this need — a '
               'Flask-based web application that allows users to perform Exploratory Data Analysis automatically '
               'and interactively. Users simply upload a dataset file (CSV, Excel, TXT, TSV, or JSON), and the '
               'system automatically detects each column type, performs data cleaning, computes descriptive '
               'statistics, presents fourteen types of interactive visualizations, and generates relevant analytical '
               'insights for decision-making. The application is designed to automatically adapt to a wide range of '
               'uploaded datasets, allowing the data exploration process to be carried out easily without requiring '
               'manual configuration from the user.',
    's12_title':'1.2 Understanding Exploratory Data Analysis (EDA)',
    's12_text':'Exploratory Data Analysis (EDA) is an approach to analyzing datasets aimed at summarizing their '
               'main characteristics, typically with the help of visual methods or simple statistics. Through EDA, '
               'an analyst can identify patterns, detect anomalies or outliers, test initial assumptions about the '
               'data, and examine relationships between variables before moving to more complex modeling stages. '
               'In this application, the EDA process is carried out through several sequential stages: data '
               'cleaning, descriptive statistics computation, data visualization, and the generation of automated '
               'smart insights ready to be used as a basis for decision-making.',
    's13_title':'1.3 Development Team',
    's13_text':'This application was developed as part of the final project for the course SD-1306 Programming '
               'for Data Science, carried out by Group 6, Class B, under the guidance of lecturer '
               '<b>{lecturer}</b>. The division of responsibilities in developing this application is as follows:',
    'col_name':'Name','col_role':'Role','col_task':'Task Summary',

    'bab2_title':'CHAPTER II — Descriptive Statistics',
    'bab2_intro':'This chapter presents the quantitative results of data processing, including a summary of the '
                 'dataset size, data quality evaluation (missing values, duplicates, and outliers), a data preview, '
                 'and complete descriptive statistics tables for both numerical and categorical variables. This '
                 'section serves as the quantitative foundation before further visualization and interpretation in '
                 'the following chapter.',
    's21_title':'2.1 Dataset Summary','s22_title':'2.2 Data Quality Evaluation',
    's23_title':'2.3 Dataset Preview (First 5 Rows)',
    's24_title':'2.4 Descriptive Statistics Tables',
    'kpi_rows':'Total Rows','kpi_cols':'Total Columns','kpi_num':'Numeric Vars','kpi_cat':'Categorical Vars',
    'kpi_missing':'Total Missing','kpi_missing_pct':'Missing %','kpi_dup':'Duplicates','kpi_out':'Outliers',
    'quality_clean':'Based on the evaluation results, the data is confirmed to be clean — no significant missing values, duplicates, or outliers were found.',
    'quality_issue':'Based on the evaluation results, the data still has several quality issues that require attention, as detailed below.',
    'quality_mv_head':'Missing Value Details per Column:','quality_out_head':'Outlier Details per Column (IQR Method):',
    'tbl_metric':'Metric','tbl_num':'Table 2.1 — Descriptive Statistics of Numerical Variables','tbl_cat':'Table 2.2 — Descriptive Statistics of Categorical Variables',

    'bab3_title':'CHAPTER III — Data Visualization',
    'bab3_intro':'This chapter presents the main charts resulting from data visualization automatically generated '
                 'by the system. Visualizations are presented in four categories: (a) numerical visualizations to '
                 'illustrate the distribution of values for each numeric variable, (b) categorical visualizations '
                 'to illustrate the proportion of each category, (c) bivariate and multivariate visualizations to '
                 'examine relationship patterns between numerical variables, and (d) categorical-vs-numerical '
                 'visualizations to compare numerical values across categories. The complete set of interactive '
                 'visualizations (14 chart types, with chart-type and color selection options) is fully accessible '
                 'through the Visualization page on the dashboard.',
    'viz_a':'(a) Numerical Visualization','viz_b':'(b) Categorical Visualization',
    'viz_c':'(c) Bivariate & Multivariate','viz_d':'(d) Categorical vs Numerical',
    'viz_none':'Visualizations had not been generated at the time this report was created. Please open the Visualization page on the dashboard to view all 14 chart types interactively.',

    'bab4_title':'CHAPTER IV — Smart Insights & Recommendations',
    'bab4_intro':'This chapter presents advanced analytical narratives prepared specifically for leadership and '
                 'stakeholders in business decision-making. Unlike the previous chapter, which is descriptive in '
                 'nature, this section interprets the key findings within the data — including data quality '
                 'conditions, the characteristics of each variable, and relationship patterns between variables — '
                 'and translates them into concrete, immediately actionable recommendations.',
    's41_title':'4.1 Executive Summary',
    's42_title':'4.2 Key Findings',
    's43_title':'4.3 Numerical Variable Insights',
    's44_title':'4.4 Categorical Variable Insights',
    's45_title':'4.5 Relationships Between Variables (Correlations)',
    's46_title':'4.6 Follow-up Recommendations',
    'no_findings':'No critical findings were identified in this data.',
    'no_corr':'No significant correlation was found between numerical variables in this dataset.',
    'no_rec':'No additional recommendations — the data and analysis results are already in optimal condition.',
    'sev_critical':'CRITICAL','sev_high':'HIGH','sev_medium':'MEDIUM','sev_low':'LOW','sev_info':'INFO',
    'pri_segera':'IMMEDIATE','pri_jangka_pendek':'SHORT TERM','pri_jangka_panjang':'LONG TERM',
    'pri_immediate':'IMMEDIATE','pri_short_term':'SHORT TERM','pri_long_term':'LONG TERM',
    'impact_label':'Impact on business decisions:','rationale_label':'Rationale:',
    'source_ai':'Insights generated by AI (Claude)','source_rule':'Insights generated rule-based',

    'bab5_title':'CHAPTER V — Conclusion',
    'bab5_intro':'This chapter is the final section of the report, presenting the conclusion of the entire data '
                 'analysis process carried out, along with follow-up suggestions that may be considered by users '
                 'and relevant stakeholders.',
    's51_title':'5.1 Conclusion',
    's51_text':'Based on the analysis process carried out, the dataset <b>{fname}</b> was successfully processed '
               'with a total of {rows} rows and {cols} columns, consisting of {num} numerical variables and {cat} '
               'categorical variables. The Exploratory Data Analysis process conducted included data quality '
               'evaluation, descriptive statistics computation, data visualization in various chart forms, and the '
               'preparation of analytical insights (smart insights) and follow-up recommendations. Overall, this '
               'report provides a comprehensive overview of the data\'s characteristics, quality conditions, and '
               'relationship patterns between variables that can serve as a basis for decision-making.',
    's52_title':'5.2 Suggestions',
    's52_items':[
      'If significant missing values, duplicates, or outliers remain, further data cleaning is recommended via the Data Cleaning page on the dashboard.',
      'For deeper visual exploration, users may use the Visualization page by selecting chart types and color schemes according to their analysis needs.',
      'The Smart Insight & Recommendations page can serve as the main reference for determining the next analysis or modeling steps.',
      'The results of this report can serve as a starting point before conducting further statistical or machine learning modeling, such as regression, classification, or clustering.',
    ],
    'footer':'This report was automatically generated by Auto EDA Analytics Dashboard — SD-1306 Final Project<br>'
             'Group 6 · Class B · Institut Teknologi Sains Bandung (ITSB) · Lecturer: {lecturer}',
  },
}


# ════════════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════════════
def _tbl(d, title, T):
    if not d: return ""
    mets = list(d.keys()); cols = list(d[mets[0]].keys())
    h = f'<h3 style="margin-top:14px">{title}</h3><table><tr style="background:#0d9488;color:white"><th>{T["tbl_metric"]}</th>'
    for c in cols: h += f'<th>{c}</th>'
    h += '</tr>'
    for m in mets:
        bg = 'background:#fff8e1' if 'missing' in m else ''
        h += f'<tr style="{bg}"><td><b>{m}</b></td>'
        for c in cols:
            v = d[m].get(c,'')
            if isinstance(v, float): v = f'{v:,.2f}'
            h += f'<td>{v}</td>'
        h += '</tr>'
    return h + '</table>'

def _team_table(T):
    is_id = (T['col_role'] == 'Peran')
    rk = 'role_id' if is_id else 'role_en'
    tk = 'task_id' if is_id else 'task_en'
    h = f'<table><tr style="background:#115e59;color:white"><th>{T["col_name"]}</th><th>{T["col_role"]}</th><th>{T["col_task"]}</th></tr>'
    for m in TEAM:
        h += f'<tr><td><b>{m["name"]}</b></td><td>{m[rk]}</td><td>{m[tk]}</td></tr>'
    return h + '</table>'

def _quality_block(quality, T):
    if not quality: return '<p>—</p>'
    miss_rows = ''.join(f'<li>{k}: {v}</li>' for k, v in quality.get('missing_per_col',{}).items())
    out_rows  = ''.join(f'<li>{k}: {v}</li>' for k, v in quality.get('outlier_cols',{}).items())
    status    = T['quality_clean'] if quality.get('is_clean') else T['quality_issue']
    return f"""
    <div class="kpi">
      <div class="k"><div class="n">{quality.get('total_missing','—')}</div><div class="l">{T['kpi_missing']}</div></div>
      <div class="k"><div class="n">{quality.get('missing_pct','—')}%</div><div class="l">{T['kpi_missing_pct']}</div></div>
      <div class="k"><div class="n">{quality.get('duplicates','—')}</div><div class="l">{T['kpi_dup']}</div></div>
      <div class="k"><div class="n">{quality.get('outliers','—')}</div><div class="l">{T['kpi_out']}</div></div>
    </div>
    <p>{status}</p>
    {f'<p><b>{T["quality_mv_head"]}</b></p><ul>{miss_rows}</ul>' if miss_rows else ''}
    {f'<p><b>{T["quality_out_head"]}</b></p><ul>{out_rows}</ul>' if out_rows else ''}
    """

def _viz_block(viz_charts, T):
    if not viz_charts: return f'<p>{T["viz_none"]}</p>'
    sections = [
        ('numerical',  T['viz_a'], {'histogram':'Histogram','boxplot':'Boxplot','density':'Density Plot','qqplot':'QQ Plot','violin':'Violin Plot'}),
        ('categorical',T['viz_b'], {'bar':'Bar Chart','pie':'Pie Chart','donut':'Donut Chart','countplot':'Count Plot','pareto':'Pareto Chart'}),
        ('bivariate',  T['viz_c'], {'heatmap':'Correlation Heatmap','pairplot':'Pair Plot','scatter':'Scatter Plot','regression':'Regression Plot','bubble':'Bubble Chart'}),
        ('cat_vs_num', T['viz_d'], {'boxplot_by_cat':'Boxplot by Category','violin_by_cat':'Violin Plot by Category','grouped_bar':'Grouped Bar Chart','strip':'Strip Plot'}),
    ]
    out = ''
    for key, title, labels in sections:
        items = viz_charts.get(key, {})
        if not items: continue
        out += f'<h3 style="margin-top:14px">{title}</h3><div class="vizgrid">'
        count = 0
        for col_or_key, value in items.items():
            if col_or_key == '_meta':
                continue
            if isinstance(value, str):
                out += f'<div class="vizcard"><div class="vizcap">{labels.get(col_or_key,col_or_key)}</div><img src="{value}"></div>'
                count += 1
            elif isinstance(value, dict):
                for ctype, src in value.items():
                    if ctype == '_meta' or not src: continue
                    out += f'<div class="vizcard"><div class="vizcap">{labels.get(ctype,ctype)} — {col_or_key}</div><img src="{src}"></div>'
                    count += 1
            if count >= 8: break
        out += '</div>'
    return out or f'<p>{T["viz_none"]}</p>'

def _smart_block(smart, T):
    if not smart: return '<p>—</p>'

    out = ''
    is_ai = smart.get('source') == 'claude_api'
    src_label = T['source_ai'] if is_ai else T['source_rule']

    # 4.1 Executive Summary
    out += f'<h3 style="margin-top:14px">{T["s41_title"]}</h3>'
    out += f'<p style="font-size:10px;color:#94a3b8;margin-bottom:6px"><i>{src_label}</i></p>'
    out += f'<div class="ins">{smart.get("executive_summary","—")}</div>'
    if smart.get('data_quality_verdict'):
        out += f'<p style="background:#f8fafc;border-left:3px solid #94a3b8;padding:8px 12px;border-radius:0 6px 6px 0;font-size:12px">{smart["data_quality_verdict"]}</p>'

    # 4.2 Key Findings
    findings = smart.get('key_findings', [])
    out += f'<h3 style="margin-top:14px">{T["s42_title"]}</h3>'
    if findings:
        sev_map = {'critical':T['sev_critical'],'high':T['sev_high'],'medium':T['sev_medium'],'low':T['sev_low'],'info':T['sev_info']}
        sev_color = {'critical':'#dc2626','high':'#f43f5e','medium':'#d97706','low':'#0891b2','info':'#0d9488'}
        out += '<table><tr style="background:#115e59;color:white"><th style="width:80px">' + ('Tingkat' if T['col_role']=='Peran' else 'Severity') + '</th><th>Finding</th><th>' + T['impact_label'].rstrip(':') + '</th></tr>'
        for f in findings:
            sev = f.get('severity','info')
            color = sev_color.get(sev, '#0d9488')
            out += f'<tr><td><span style="background:{color};color:white;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700">{sev_map.get(sev,sev.upper())}</span></td><td>{f.get("finding","")}</td><td>{f.get("impact","")}</td></tr>'
        out += '</table>'
    else:
        out += f'<p>{T["no_findings"]}</p>'

    # 4.3 Numeric insights
    vars_all = smart.get('variable_insights', [])
    numv = [v for v in vars_all if v.get('type') == 'numerical']
    out += f'<h3 style="margin-top:14px">{T["s43_title"]}</h3>'
    if numv:
        for v in numv:
            out += f'<p><b>📊 {v.get("variable","")}</b><br>{v.get("insight","")}<br><i style="color:#64748b;font-size:11px">{v.get("business_relevance","")}</i></p>'
    else:
        out += '<p>—</p>'

    # 4.4 Categorical insights
    catv = [v for v in vars_all if v.get('type') == 'categorical']
    out += f'<h3 style="margin-top:14px">{T["s44_title"]}</h3>'
    if catv:
        for v in catv:
            out += f'<p><b>🏷️ {v.get("variable","")}</b><br>{v.get("insight","")}<br><i style="color:#64748b;font-size:11px">{v.get("business_relevance","")}</i></p>'
    else:
        out += '<p>—</p>'

    # 4.5 Correlations
    out += f'<h3 style="margin-top:14px">{T["s45_title"]}</h3>'
    corr_text = smart.get('correlations_insight','')
    out += f'<p>{corr_text}</p>' if corr_text else f'<p>{T["no_corr"]}</p>'

    # 4.6 Recommendations
    recs = smart.get('recommendations', [])
    out += f'<h3 style="margin-top:14px">{T["s46_title"]}</h3>'
    if recs:
        pri_map = {k: T.get(f'pri_{k}', k.upper()) for k in ['segera','jangka_pendek','jangka_panjang','immediate','short_term','long_term']}
        pri_color = {'segera':'#dc2626','immediate':'#dc2626','jangka_pendek':'#d97706','short_term':'#d97706','jangka_panjang':'#0891b2','long_term':'#0891b2'}
        out += '<table><tr style="background:#115e59;color:white"><th style="width:110px">Priority</th><th>Action</th><th>' + T['rationale_label'].rstrip(':') + '</th></tr>'
        for r in recs:
            pri = r.get('priority','info')
            color = pri_color.get(pri, '#0d9488')
            out += f'<tr><td><span style="background:{color};color:white;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700">{pri_map.get(pri,pri.upper())}</span></td><td>{r.get("action","")}</td><td><i>{r.get("rationale","")}</i></td></tr>'
        out += '</table>'
    else:
        out += f'<p>{T["no_rec"]}</p>'

    return out


# ════════════════════════════════════════════════════════════════════════════
# Public API
# ════════════════════════════════════════════════════════════════════════════
def export_csv(df):
    b = io.StringIO(); df.to_csv(b, index=False); return b.getvalue().encode('utf-8')

def export_excel(df, stats=None):
    b = io.BytesIO()
    with pd.ExcelWriter(b, engine='openpyxl') as w:
        df.to_excel(w, sheet_name='Dataset', index=False)
        if stats:
            if stats.get('numeric_summary'):
                pd.DataFrame(stats['numeric_summary']).to_excel(w, sheet_name='Statistik Numerik')
            if stats.get('categorical_summary'):
                pd.DataFrame(stats['categorical_summary']).to_excel(w, sheet_name='Statistik Kategorikal')
    b.seek(0); return b.getvalue()

def export_html(df, stats, info=None, viz_charts=None, smart_insights=None, lang='id'):
    L = lang if lang in ('id','en') else 'id'
    T = _T[L]
    now    = datetime.now().strftime("%d %B %Y")
    now_dt = datetime.now().strftime("%d %B %Y, %H:%M")
    fname  = info.get('filename','dataset') if info else 'dataset'
    meta   = stats.get('meta', {})
    quality = stats.get('quality', {})
    insights = stats.get('insights', '')
    is_id = (L == 'id')

    # ── Kata Pengantar ────────────────────────────────────────────────────
    if is_id:
        kp_title = "KATA PENGANTAR"
        kp_body = f"""<p>Puji syukur kami panjatkan kepada Tuhan Yang Maha Esa atas terselesaikannya laporan
analisis data ini. Laporan ini disusun sebagai bagian dari tugas akhir (final project) mata kuliah
<b>SD-1306 Programming for Data Science</b>, Kelompok 6 Kelas B, Institut Teknologi Sains Bandung (ITSB),
di bawah bimbingan <b>{LECTURER}</b>.</p>
<p>Laporan ini menyajikan hasil Exploratory Data Analysis (EDA) secara menyeluruh terhadap dataset
<b>{fname}</b>, meliputi pembersihan data, analisis statistik deskriptif, visualisasi data,
serta wawasan analitis (smart insight) dan rekomendasi yang ditujukan untuk mendukung pengambilan
keputusan oleh pimpinan dan pemangku kepentingan.</p>
<p>Kami menyadari bahwa laporan ini masih jauh dari sempurna. Oleh karena itu, kami mengharapkan
kritik dan saran yang membangun demi penyempurnaan ke depannya. Semoga laporan ini bermanfaat
bagi semua pihak yang membutuhkan.</p>
<br><p style="text-align:right">Cikarang, {now}<br><br><b>Tim Pengembang Kelompok 6</b></p>"""
        toc_title = "DAFTAR ISI"
        toc_items = [
            ("Halaman Judul", "i"),
            ("Kata Pengantar", "ii"),
            ("Daftar Isi", "iii"),
            ("BAB I — Pendahuluan", "1"),
            ("\u00a0\u00a0\u00a01.1 Latar Belakang & Tentang Aplikasi", "1"),
            ("\u00a0\u00a0\u00a01.2 Pengertian Exploratory Data Analysis", "2"),
            ("\u00a0\u00a0\u00a01.3 Tim Pengembang", "2"),
            ("BAB II — Statistik Deskriptif", "3"),
            ("\u00a0\u00a0\u00a02.1 Ringkasan Dataset", "3"),
            ("\u00a0\u00a0\u00a02.2 Evaluasi Kualitas Data", "3"),
            ("\u00a0\u00a0\u00a02.3 Pratinjau Dataset", "4"),
            ("\u00a0\u00a0\u00a02.4 Tabel Statistik Deskriptif", "4"),
            ("BAB III — Visualisasi Data", "5"),
            ("BAB IV — Smart Insight & Rekomendasi", "6"),
            ("\u00a0\u00a0\u00a04.1 Ringkasan Eksekutif", "6"),
            ("\u00a0\u00a0\u00a04.2 Temuan Utama", "6"),
            ("\u00a0\u00a0\u00a04.3-4.4 Wawasan Variabel", "7"),
            ("\u00a0\u00a0\u00a04.5 Korelasi Antar Variabel", "7"),
            ("\u00a0\u00a0\u00a04.6 Rekomendasi Tindak Lanjut", "8"),
            ("BAB V — Penutup", "9"),
            ("Daftar Pustaka", "10"),
        ]
        ref_title = "DAFTAR PUSTAKA"
        refs = [
            "Hadley Wickham &amp; Garrett Grolemund. (2017). <i>R for Data Science</i>. O'Reilly Media.",
            "Jake VanderPlas. (2016). <i>Python Data Science Handbook</i>. O'Reilly Media.",
            "Wes McKinney. (2017). <i>Python for Data Analysis</i> (2nd ed.). O'Reilly Media.",
            "Pandas Development Team. (2024). <i>pandas documentation</i>. https://pandas.pydata.org/docs/",
            "Flask Project. (2024). <i>Flask Documentation</i>. https://flask.palletsprojects.com/",
            "Anthropic. (2024). <i>Claude API Documentation</i>. https://docs.anthropic.com/",
            "McKinney, W. (2010). Data Structures for Statistical Computing in Python. <i>Proceedings of the 9th Python in Science Conference</i>, 51-56.",
            "Matplotlib Development Team. (2024). <i>Matplotlib: Visualization with Python</i>. https://matplotlib.org/",
        ]
        print_btn = "Print / Simpan PDF"
        auto_insights_title = "2.5 Wawasan Otomatis (Auto Insights)"
    else:
        kp_title = "PREFACE"
        kp_body = f"""<p>We give thanks to God Almighty for the completion of this data analysis report.
This report was prepared as part of the final project for the course <b>SD-1306 Programming for Data Science</b>,
Group 6 Class B, Institut Teknologi Sains Bandung (ITSB), under the guidance of <b>{LECTURER}</b>.</p>
<p>This report presents a comprehensive Exploratory Data Analysis (EDA) of the dataset <b>{fname}</b>,
covering data cleaning, descriptive statistics, data visualization, and analytical insights (smart insights)
and recommendations aimed at supporting decision-making by leadership and stakeholders.</p>
<p>We recognize that this report is still far from perfect. Therefore, we welcome constructive criticism
and suggestions for future improvement. We hope this report will be beneficial to all parties who need it.</p>
<br><p style="text-align:right">Cikarang, {now}<br><br><b>Group 6 Development Team</b></p>"""
        toc_title = "TABLE OF CONTENTS"
        toc_items = [
            ("Title Page", "i"),
            ("Preface", "ii"),
            ("Table of Contents", "iii"),
            ("CHAPTER I — Introduction", "1"),
            ("\u00a0\u00a0\u00a01.1 Background & About the Application", "1"),
            ("\u00a0\u00a0\u00a01.2 Understanding Exploratory Data Analysis", "2"),
            ("\u00a0\u00a0\u00a01.3 Development Team", "2"),
            ("CHAPTER II — Descriptive Statistics", "3"),
            ("\u00a0\u00a0\u00a02.1 Dataset Summary", "3"),
            ("\u00a0\u00a0\u00a02.2 Data Quality Evaluation", "3"),
            ("\u00a0\u00a0\u00a02.3 Dataset Preview", "4"),
            ("\u00a0\u00a0\u00a02.4 Descriptive Statistics Tables", "4"),
            ("CHAPTER III — Data Visualization", "5"),
            ("CHAPTER IV — Smart Insights & Recommendations", "6"),
            ("\u00a0\u00a0\u00a04.1 Executive Summary", "6"),
            ("\u00a0\u00a0\u00a04.2 Key Findings", "6"),
            ("\u00a0\u00a0\u00a04.3-4.4 Variable Insights", "7"),
            ("\u00a0\u00a0\u00a04.5 Correlations Between Variables", "7"),
            ("\u00a0\u00a0\u00a04.6 Follow-up Recommendations", "8"),
            ("CHAPTER V — Conclusion", "9"),
            ("References", "10"),
        ]
        ref_title = "REFERENCES"
        refs = [
            "Hadley Wickham &amp; Garrett Grolemund. (2017). <i>R for Data Science</i>. O'Reilly Media.",
            "Jake VanderPlas. (2016). <i>Python Data Science Handbook</i>. O'Reilly Media.",
            "Wes McKinney. (2017). <i>Python for Data Analysis</i> (2nd ed.). O'Reilly Media.",
            "Pandas Development Team. (2024). <i>pandas documentation</i>. https://pandas.pydata.org/docs/",
            "Flask Project. (2024). <i>Flask Documentation</i>. https://flask.palletsprojects.com/",
            "Anthropic. (2024). <i>Claude API Documentation</i>. https://docs.anthropic.com/",
            "McKinney, W. (2010). Data Structures for Statistical Computing in Python. <i>Proceedings of the 9th Python in Science Conference</i>, 51-56.",
            "Matplotlib Development Team. (2024). <i>Matplotlib: Visualization with Python</i>. https://matplotlib.org/",
        ]
        print_btn = "Print / Save as PDF"
        auto_insights_title = "2.5 Auto Insights"

    # Build TOC HTML
    toc_rows = ""
    for item, pg in toc_items:
        bold = "font-weight:700" if not item.startswith('\u00a0') else "font-weight:400"
        toc_rows += f'<tr><td style="border:none;padding:4px 0;{bold}">{item}</td><td style="border:none;text-align:right;padding:4px 0;{bold}">{pg}</td></tr>'

    # Build refs HTML
    refs_html = "\n".join(f'<li style="margin-bottom:8px">{r}</li>' for r in refs)

    html = f"""<!DOCTYPE html>
<html lang="{L}">
<head>
<meta charset="UTF-8">
<title>{T['report_title']} — {fname}</title>
<style>
@page {{size:A4;margin:2.5cm 2.5cm 2cm 3cm}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Times New Roman',Times,serif;color:#0f172a;line-height:1.8;
     text-align:justify;font-size:12pt;background:#fff;
     max-width:800px;margin:0 auto;padding:20px 32px 60px}}
h1{{font-size:16pt;font-weight:700;text-align:center;color:#042f2e;
    border-bottom:2px solid #0d9488;padding-bottom:8px;margin:16px 0 8px;
    page-break-after:avoid}}
h2{{font-size:14pt;font-weight:700;color:#0d9488;margin:20px 0 8px;
    padding-bottom:5px;border-bottom:1.5px solid #e2e8f0;page-break-after:avoid}}
h3{{font-size:12pt;font-weight:700;color:#115e59;margin:14px 0 6px;page-break-after:avoid}}
p{{margin:6px 0;text-indent:1.5em}}
p.no-indent{{text-indent:0}}
ul,ol{{margin:6px 0 10px 24px}}
li{{margin-bottom:5px}}
/* Cover */
.cover{{display:flex;flex-direction:column;align-items:center;justify-content:center;
        min-height:95vh;text-align:center;page-break-after:always;
        border:3px double #0d9488;padding:40px 30px;margin:-20px -32px 0}}
.cover-logo{{font-size:52px;margin-bottom:16px}}
.cover-inst{{font-size:11pt;color:#475569;margin-bottom:20px;line-height:1.7}}
.cover-title{{font-size:17pt;font-weight:900;color:#042f2e;margin-bottom:6px;line-height:1.3;text-transform:uppercase}}
.cover-subtitle{{font-size:12pt;color:#115e59;margin-bottom:20px}}
.cover-hr{{width:80px;height:3px;background:#0d9488;margin:16px auto}}
.cover-meta{{font-size:11pt;line-height:2.2;margin-top:10px}}
.cover-footer{{margin-top:auto;padding-top:20px;border-top:1px solid #cbd5e1;
               font-size:10pt;color:#64748b;width:100%;text-align:center}}
/* Chapter intro */
.chapter-intro{{background:#f8fafc;border-left:4px solid #94a3b8;padding:10px 14px;
               font-size:11pt;color:#475569;margin:8px 0 16px;page-break-inside:avoid}}
/* KPI */
.kpi{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:12px 0;page-break-inside:avoid}}
.k{{background:#f0fdfa;border:1px solid #99f6e4;border-radius:6px;padding:10px;text-align:center}}
.k .n{{font-size:22pt;font-weight:900;color:#0d9488;line-height:1.1}}
.k .l{{font-size:8pt;color:#64748b;text-transform:uppercase;letter-spacing:.5px}}
/* Insight */
.ins{{background:#f0fdfa;border-left:4px solid #0d9488;padding:10px 14px;
     margin:10px 0;font-size:11pt;page-break-inside:avoid}}
/* Tables */
table{{border-collapse:collapse;width:100%;font-size:10pt;margin:10px 0;page-break-inside:auto}}
thead{{display:table-header-group}}
tr{{page-break-inside:avoid}}
th{{background:#0d9488;color:white;font-weight:700;padding:5px 7px;border:1px solid #0d9488}}
td{{padding:4px 7px;border:1px solid #cbd5e1}}
tr:nth-child(even) td{{background:#f8fffe}}
tr.hl td{{background:#fff8e1}}
/* Viz */
.vizgrid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin:12px 0}}
.vizcard{{border:1px solid #e2e8f0;border-radius:5px;overflow:hidden;
         page-break-inside:avoid;break-inside:avoid}}
.vizcard img{{width:100%;display:block;max-height:260px;object-fit:contain}}
.vizcap{{background:#f8fffe;font-size:9pt;font-weight:700;padding:4px 8px;
         border-bottom:1px solid #e2e8f0;color:#115e59}}
/* TOC */
.toc-table{{border:none;width:100%}}
.toc-table td{{border:none;padding:3px 0}}
/* Sections */
.section{{page-break-before:always;padding-top:8px}}
/* Footer */
.foot{{margin-top:32px;padding-top:10px;border-top:1px solid #e2e8f0;
      font-size:9pt;color:#94a3b8;text-align:center}}
/* Print button */
.print-btn{{position:fixed;bottom:20px;right:20px;background:#0d9488;color:white;
            border:none;padding:10px 18px;border-radius:8px;font-size:12pt;
            font-weight:700;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,.25);z-index:9999}}
.print-btn:hover{{background:#0f766e}}
/* Findings */
.finding-row{{display:flex;gap:10px;margin-bottom:8px;padding:9px 11px;border-radius:6px;
             border-left:4px solid #ccc;page-break-inside:avoid}}
.rec-row{{display:flex;gap:10px;margin-bottom:8px;padding:9px 11px;border-radius:6px;
         border-left:4px solid #ccc;page-break-inside:avoid}}
.var-card{{padding:9px 11px;border-radius:6px;margin-bottom:8px;page-break-inside:avoid}}
@media print{{
  .print-btn{{display:none!important}}
  .cover{{min-height:0;height:26cm}}
  .section{{page-break-before:always}}
  tr{{page-break-inside:avoid}}
  .vizcard{{page-break-inside:avoid;break-inside:avoid}}
  h2,h3{{page-break-after:avoid}}
  .chapter-intro,.kpi,.ins,.finding-row,.rec-row,.var-card{{page-break-inside:avoid}}
  body{{padding:0;max-width:100%}}
  img{{max-height:250px;object-fit:contain}}
}}
</style>
</head>
<body>

<button class="print-btn" onclick="window.print()">🖨️ {print_btn}</button>

<!-- ══════════════════ COVER ══════════════════ -->
<div class="cover">
  <div class="cover-logo">📊</div>
  <div class="cover-inst">
    Institut Teknologi Sains Bandung (ITSB)<br>
    Program Studi Sains Data · SD-1306 Programming for Data Science<br>
    Final Project 2026
  </div>
  <div class="cover-title">{T['report_title']}</div>
  <div class="cover-subtitle">Dataset: {fname}</div>
  <div class="cover-hr"></div>
  <div class="cover-meta">
    <b>Kelompok 6 · Kelas B</b><br>
    Ignasius Rabi Blolong &nbsp;|&nbsp; Ni Md Aurora Sekarningrum<br>
    Adinda Maiza Ishfahani &nbsp;|&nbsp; Chricyesia W. F. Uvas &nbsp;|&nbsp; Januaria Teresinha<br><br>
    {T['lecturer_label']}: <b>{LECTURER}</b>
  </div>
  <div class="cover-footer">{now}</div>
</div>

<!-- ══════════════════ KATA PENGANTAR ══════════════════ -->
<div class="section">
  <h1>{kp_title}</h1>
  {kp_body}
</div>

<!-- ══════════════════ DAFTAR ISI ══════════════════ -->
<div class="section">
  <h1>{toc_title}</h1>
  <table class="toc-table">
    {toc_rows}
  </table>
</div>

<!-- ══════════════════ BAB I ══════════════════ -->
<div class="section">
  <h2>{T['bab1_title']}</h2>
  <div class="chapter-intro">{T['bab1_intro']}</div>
  <h3>{T['s11_title']}</h3>
  <p class="no-indent">{T['s11_text']}</p>
  <h3>{T['s12_title']}</h3>
  <p class="no-indent">{T['s12_text']}</p>
  <h3>{T['s13_title']}</h3>
  <p class="no-indent">{T['s13_text'].format(lecturer=LECTURER)}</p>
  {_team_table(T)}
</div>

<!-- ══════════════════ BAB II ══════════════════ -->
<div class="section">
  <h2>{T['bab2_title']}</h2>
  <div class="chapter-intro">{T['bab2_intro']}</div>

  <h3>{T['s21_title']}</h3>
  <div class="kpi">
    <div class="k"><div class="n">{meta.get('total_rows','—')}</div><div class="l">{T['kpi_rows']}</div></div>
    <div class="k"><div class="n">{meta.get('total_cols','—')}</div><div class="l">{T['kpi_cols']}</div></div>
    <div class="k"><div class="n">{meta.get('numeric_cols','—')}</div><div class="l">{T['kpi_num']}</div></div>
    <div class="k"><div class="n">{meta.get('categorical_cols','—')}</div><div class="l">{T['kpi_cat']}</div></div>
  </div>

  <h3>{T['s22_title']}</h3>
  {_quality_block(quality, T)}

  <h3>{T['s23_title']}</h3>
  {df.head(5).to_html(index=False, border=0)}

  <h3>{T['s24_title']}</h3>
  {_tbl(stats.get('numeric_summary',{}), T['tbl_num'], T)}
  {_tbl(stats.get('categorical_summary',{}), T['tbl_cat'], T)}

  <h3>{auto_insights_title}</h3>
  <div class="ins">{insights}</div>
</div>

<!-- ══════════════════ BAB III ══════════════════ -->
<div class="section">
  <h2>{T['bab3_title']}</h2>
  <div class="chapter-intro">{T['bab3_intro']}</div>
  {_viz_block(viz_charts, T)}
</div>

<!-- ══════════════════ BAB IV ══════════════════ -->
<div class="section">
  <h2>{T['bab4_title']}</h2>
  <div class="chapter-intro">{T['bab4_intro']}</div>
  {_smart_block(smart_insights, T)}
</div>

<!-- ══════════════════ BAB V ══════════════════ -->
<div class="section">
  <h2>{T['bab5_title']}</h2>
  <div class="chapter-intro">{T['bab5_intro']}</div>
  <h3>{T['s51_title']}</h3>
  <p class="no-indent">{T['s51_text'].format(fname=fname,rows=meta.get('total_rows','—'),cols=meta.get('total_cols','—'),num=meta.get('numeric_cols','—'),cat=meta.get('categorical_cols','—'))}</p>
  <h3>{T['s52_title']}</h3>
  <ol>{''.join(f'<li style="margin-bottom:6px">{i}</li>' for i in T['s52_items'])}</ol>
</div>

<!-- ══════════════════ DAFTAR PUSTAKA ══════════════════ -->
<div class="section">
  <h1>{ref_title}</h1>
  <ol>{refs_html}</ol>
</div>

<div class="foot">
  {T['footer'].format(lecturer=LECTURER)}<br>
  {'Digenerate pada' if is_id else 'Generated on'}: {now_dt}
</div>

</body>
</html>"""
    return html.encode('utf-8')


def export_pdf(df, stats, info=None, viz_charts=None, smart_insights=None, lang='id'):
    html = export_html(df, stats, info, viz_charts, smart_insights, lang)
    try:
        from weasyprint import HTML
        return HTML(string=html.decode('utf-8')).write_pdf(), 'application/pdf', '.pdf'
    except ImportError:
        return html, 'text/html', '.html'