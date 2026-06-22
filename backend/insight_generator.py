"""
backend/insight_generator.py
Three-tier insight system:
  1. generate_insights()        — fast rule-based, for Dashboard "Wawasan Otomatis"
  2. generate_smart_insights()  — tries Claude API first, then Gemini API,
                                  and falls back to enhanced rule-based if both unavailable
"""
import pandas as pd
import numpy as np
import os
import json
import urllib.request
import urllib.error

# ══════════════════════════════════════════════════════════════════════════════
# TIER 1 — Quick rule-based insights (Dashboard widget)
# ══════════════════════════════════════════════════════════════════════════════
def generate_insights(df, num_cols, cat_cols):
    insights = []
    rows, cols = df.shape
    missing_total = int(df.isnull().sum().sum())
    missing_pct = round(missing_total / (rows * cols) * 100, 1) if rows * cols > 0 else 0
    insights.append(
        f"📋 Dataset memiliki <b>{rows:,} baris</b> dan <b>{cols} kolom</b> "
        f"({len(num_cols)} numerik, {len(cat_cols)} kategorikal)."
    )
    if missing_total > 0:
        worst_col = df.isnull().sum().idxmax()
        worst_pct = round(df[worst_col].isnull().mean() * 100, 1)
        insights.append(
            f"❗ Total <b>{missing_pct}% missing values</b>. "
            f"Kolom terbanyak: <b>{worst_col}</b> ({worst_pct}% kosong)."
        )
    else:
        insights.append("✅ Tidak ada missing values — dataset bersih.")
    if num_cols:
        outlier_cols = []
        for col in num_cols:
            s = df[col].dropna()
            if len(s) < 4:
                continue
            q1, q3 = s.quantile(0.25), s.quantile(0.75)
            iqr = q3 - q1
            n_out = int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum())
            if n_out > 0:
                outlier_cols.append((col, n_out))
        if outlier_cols:
            top3 = sorted(outlier_cols, key=lambda x: x[1], reverse=True)[:3]
            desc = ", ".join(f"<b>{c}</b> ({n})" for c, n in top3)
            insights.append(f"⚠️ Outlier terdeteksi (IQR): {desc}.")
        skewed_cols = []
        for col in num_cols:
            s = df[col].dropna()
            if len(s) < 4:
                continue
            skew_val = float(s.skew())
            if abs(skew_val) >= 1.0:
                skewed_cols.append((col, skew_val))
        if skewed_cols:
            top_skew = sorted(skewed_cols, key=lambda x: abs(x[1]), reverse=True)[:2]
            desc = ", ".join(
                f"<b>{c}</b> ({'positif' if v > 0 else 'negatif'} {v:.2f})"
                for c, v in top_skew
            )
            insights.append(f"📈 Distribusi miring: {desc}.")
    if len(num_cols) >= 2:
        corr = df[num_cols].corr().abs()
        vals = corr.to_numpy().copy()
        np.fill_diagonal(vals, 0)
        corr.iloc[:, :] = vals
        max_pair = corr.unstack().idxmax()
        max_val = corr.loc[max_pair]
        if max_val > 0.5:
            insights.append(
                f"🔗 Korelasi tertinggi: <b>{max_pair[0]}</b> ↔ <b>{max_pair[1]}</b> "
                f"(r = {max_val:.2f})."
            )
    return "<br>".join(insights[:5])

# ══════════════════════════════════════════════════════════════════════════════
# TIER 2 — Smart LLM API Executive Insights
# ══════════════════════════════════════════════════════════════════════════════
def _build_data_summary(df, num_cols, cat_cols, dt_cols=None, quality=None):
    """Build a compact, data-rich summary to send to LLM APIs."""
    rows, cols_n = df.shape
    summary = {
        "dataset": {
            "rows": rows,
            "cols": cols_n,
            "numeric_cols": len(num_cols),
            "categorical_cols": len(cat_cols),
            "datetime_cols": len(dt_cols or []),
        },
        "quality": quality or {},
        "numerical": {},
        "categorical": {},
        "correlations": [],
    }
    # Numerical stats per column
    for col in num_cols:
        s = df[col].dropna()
        if s.empty:
            continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        n_out = int(((s < q1 - 1.5*iqr) | (s > q3 + 1.5*iqr)).sum())
        summary["numerical"][col] = {
            "mean":     round(float(s.mean()), 4),
            "median":   round(float(s.median()), 4),
            "std":      round(float(s.std()), 4),
            "min":      round(float(s.min()), 4),
            "max":      round(float(s.max()), 4),
            "skewness": round(float(s.skew()), 4),
            "kurtosis": round(float(s.kurt()), 4),
            "outliers": n_out,
            "missing":  int(df[col].isnull().sum()),
            "cv_pct":   round(abs(float(s.std()) / float(s.mean()) * 100), 1) if s.mean() != 0 else None,
        }
    # Categorical stats per column
    for col in cat_cols:
        s = df[col].dropna()
        if s.empty:
            continue
        vc = s.value_counts()
        top_val, top_count = vc.index[0], int(vc.iloc[0])
        summary["categorical"][col] = {
            "n_unique":     int(s.nunique()),
            "top_value":    str(top_val),
            "top_pct":      round(top_count / len(s) * 100, 1),
            "missing":      int(df[col].isnull().sum()),
            "top5":         {str(k): int(v) for k, v in vc.head(5).items()},
        }
    # Top correlations
    if len(num_cols) >= 2:
        corr = df[num_cols].corr()
        seen = set()
        pairs = []
        for c1 in num_cols:
            for c2 in num_cols:
                if c1 == c2 or (c2, c1) in seen:
                    continue
                seen.add((c1, c2))
                r = corr.loc[c1, c2]
                if not pd.isna(r) and abs(r) >= 0.3:
                    pairs.append({"col1": c1, "col2": c2, "r": round(float(r), 4)})
        pairs.sort(key=lambda x: abs(x["r"]), reverse=True)
        summary["correlations"] = pairs[:8]
    return summary

def _call_claude_api(prompt: str, lang: str = 'id') -> str | None:
    """
    Call Anthropic /v1/messages. Returns text or None on failure.
    API key read from env ANTHROPIC_API_KEY.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None
    payload = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type":      "application/json",
            "x-api-key":         api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body["content"][0]["text"]
    except Exception:
        return None

def _call_gemini_api(prompt: str, lang: str = 'id') -> str | None:
    """
    Call Google Gemini API using native urllib.
    API key read from env GEMINI_API_KEY.
    Uses gemini-2.5-flash for fast structured JSON responses.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None
    
    # Menyiapkan payload request sesuai spesifikasi Google AI Studio API
    payload = json.dumps({
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.3
        }
    }).encode("utf-8")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            # Mengambil text output dari struktur response Gemini
            return body["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return None

def _build_prompt(summary: dict, lang: str) -> str:
    """Build the prompt for LLM APIs."""
    summary_json = json.dumps(summary, ensure_ascii=False, indent=2)
    if lang == 'en':
        return f"""You are a Summary Data Scientist presenting findings to a CEO and key stakeholders. 
Your job is to turn the dataset statistics below into sharp, executive-level insights and clear recommendations.
RULES:
- Be direct, confident, and business-oriented. No fluff.
- Every insight must state WHAT was found AND WHY it matters for decisions.
- Prioritize findings by business impact (high → medium → low).
- Flag data quality issues that could mislead analysis.
- Recommendations must be specific and actionable.
- Use plain language. Avoid jargon unless essential.
- Return ONLY valid JSON — no markdown, no extra text.
DATASET STATISTICS:
{summary_json}
Return this exact JSON structure:
{{
  "executive_summary": "2-3 sentence overall assessment of the dataset and its business readiness",
  "key_findings": [
    {{
      "finding": "specific finding",
      "impact": "why this matters for business decisions",
      "severity": "critical|high|medium|low|info"
    }}
  ],
  "data_quality_verdict": "Overall data quality assessment in 1-2 sentences",
  "variable_insights": [
    {{
      "variable": "column name",
      "type": "numerical|categorical",
      "insight": "what this variable tells us",
      "business_relevance": "why stakeholders should care"
    }}
  ],
  "correlations_insight": "What the correlation patterns reveal about the data relationships",
  "recommendations": [
    {{
      "priority": "immediate|short_term|long_term",
      "action": "specific action to take",
      "rationale": "why this action is needed"
    }}
  ]
}}"""
    else:
        return f"""Kamu adalah Senior Data Scientist yang mempresentasikan temuan kepada CEO dan para pemangku kepentingan (stakeholder) utama.
Tugasmu adalah mengubah statistik dataset di bawah ini menjadi insight tajam setingkat eksekutif dan rekomendasi yang jelas.
ATURAN:
- Langsung, percaya diri, dan berorientasi bisnis. Tidak ada basa-basi.
- Setiap insight harus menyatakan APA yang ditemukan DAN MENGAPA itu penting untuk pengambilan keputusan.
- Prioritaskan temuan berdasarkan dampak bisnis (tinggi → sedang → rendah).
- Tandai masalah kualitas data yang bisa menyesatkan analisis.
- Rekomendasi harus spesifik dan dapat ditindaklanjuti.
- Gunakan bahasa yang mudah dipahami. Hindari jargon teknis kecuali sangat perlu.
- Kembalikan HANYA JSON yang valid — tanpa markdown, tanpa teks tambahan.
STATISTIK DATASET:
{summary_json}
Kembalikan struktur JSON ini persis:
{{
  "executive_summary": "Penilaian keseluruhan dataset dalam 2-3 kalimat dan kesiapannya untuk analisis bisnis",
  "key_findings": [
    {{
      "finding": "temuan spesifik",
      "impact": "mengapa ini penting untuk keputusan bisnis",
      "severity": "critical|high|medium|low|info"
    }}
  ],
  "data_quality_verdict": "Penilaian kualitas data secara keseluruhan dalam 1-2 kalimat",
  "variable_insights": [
    {{
      "variable": "nama kolom",
      "type": "numerical|categorical",
      "insight": "apa yang diceritakan variabel ini",
      "business_relevance": "mengapa stakeholder perlu memperhatikan ini"
    }}
  ],
  "correlations_insight": "Apa yang diungkapkan pola korelasi tentang hubungan dalam data",
  "recommendations": [
    {{
      "priority": "segera|jangka_pendek|jangka_panjang",
      "action": "tindakan spesifik yang perlu diambil",
      "rationale": "mengapa tindakan ini diperlukan"
    }}
  ]
}}"""

def _fallback_insights(summary: dict, lang: str) -> dict:
    """
    Enhanced rule-based fallback when Claude and Gemini APIs are unavailable.
    Still produces structured, business-oriented insights.
    """
    is_id = lang == 'id'
    qual = summary.get("quality", {})
    num  = summary.get("numerical", {})
    cat  = summary.get("categorical", {})
    corr = summary.get("correlations", [])
    ds   = summary.get("dataset", {})
    total_missing = qual.get("total_missing", 0)
    duplicates    = qual.get("duplicates", 0)
    outliers      = qual.get("outliers", 0)
    is_clean      = qual.get("is_clean", False)
    rows          = ds.get("rows", 0)
    key_findings = []
    var_insights = []
    recs = []
    # ── Data quality findings ─────────────────────────────────────────────────
    if not is_clean:
        if total_missing > 0:
            miss_pct = qual.get("missing_pct", 0)
            if is_id:
                key_findings.append({
                    "finding": f"Terdapat {total_missing:,} missing value ({miss_pct}% dari seluruh sel data)",
                    "impact": "Missing value dapat menyebabkan bias dalam model prediktif dan kesimpulan yang keliru jika tidak ditangani sebelum analisis lebih lanjut.",
                    "severity": "critical" if miss_pct > 20 else ("high" if miss_pct > 5 else "medium")
                })
                recs.append({"priority": "segera", "action": "Tangani missing value melalui halaman Pembersihan Data — pilih strategi imputasi (mean/median/modus) atau hapus baris kosong sesuai konteks.", "rationale": f"Missing value {miss_pct}% berpotensi mendistorsi hasil analisis."})
            else:
                key_findings.append({"finding": f"{total_missing:,} missing values detected ({miss_pct}% of all data cells)", "impact": "Missing values can introduce bias in predictive models and lead to incorrect conclusions if not handled before further analysis.", "severity": "critical" if miss_pct > 20 else ("high" if miss_pct > 5 else "medium")})
                recs.append({"priority": "immediate", "action": "Handle missing values via the Data Cleaning page — choose an imputation strategy or remove incomplete rows based on context.", "rationale": f"Missing rate of {miss_pct}% risks distorting analysis results."})
        if duplicates > 0:
            dup_pct = round(duplicates / rows * 100, 1) if rows else 0
            if is_id:
                key_findings.append({"finding": f"{duplicates:,} baris duplikat terdeteksi ({dup_pct}% dari data)", "impact": "Duplikat dapat menggelemaskan metrik bisnis (misal: jumlah transaksi, jumlah pelanggan) dan menyebabkan kesimpulan yang tidak akurat.", "severity": "high"})
                recs.append({"priority": "segera", "action": "Hapus baris duplikat sebelum analisis lanjutan untuk memastikan integritas data.", "rationale": "Duplikat dapat mendistorsi rata-rata, total, dan model prediktif."})
            else:
                key_findings.append({"finding": f"{duplicates:,} duplicate rows detected ({dup_pct}% of data)", "impact": "Duplicates can inflate business metrics (e.g. transaction counts, customer counts) and lead to inaccurate conclusions.", "severity": "high"})
                recs.append({"priority": "immediate", "action": "Remove duplicate rows before further analysis to ensure data integrity.", "rationale": "Duplicates distort averages, totals, and predictive models."})
        if outliers > 0:
            out_cols = qual.get("outlier_cols", {})
            top_out = sorted(out_cols.items(), key=lambda x: x[1], reverse=True)[:3]
            col_desc = ", ".join(f"{c} ({n})" for c, n in top_out)
            if is_id:
                key_findings.append({"finding": f"{outliers:,} outlier terdeteksi pada kolom: {col_desc}", "impact": "Outlier dapat menggeser rata-rata dan memperburuk performa model ML. Penting untuk diverifikasi apakah outlier adalah error input atau nilai ekstrem yang valid.", "severity": "medium"})
                recs.append({"priority": "jangka_pendek", "action": f"Verifikasi outlier pada kolom {col_desc} — jika error, hapus; jika valid, gunakan median/winsorize untuk analisis statistik.", "rationale": "Outlier tidak tertangani dapat merusak model dan menyesatkan interpretasi."})
            else:
                key_findings.append({"finding": f"{outliers:,} outliers detected in columns: {col_desc}", "impact": "Outliers can skew averages and degrade ML model performance. It's important to verify whether outliers are data entry errors or valid extreme values.", "severity": "medium"})
                recs.append({"priority": "short_term", "action": f"Verify outliers in {col_desc} — if errors, remove; if valid, use median/winsorize for statistical analysis.", "rationale": "Unhandled outliers can damage models and mislead interpretation."})
    else:
        if is_id:
            key_findings.append({"finding": "Data dalam kondisi bersih — tidak ada missing value, duplikat, maupun outlier signifikan", "impact": "Dataset siap digunakan langsung untuk analisis statistik dan pemodelan tanpa preprocessing tambahan.", "severity": "info"})
        else:
            key_findings.append({"finding": "Data is clean — no missing values, duplicates, or significant outliers", "impact": "Dataset is ready for direct use in statistical analysis and modeling without additional preprocessing.", "severity": "info"})
    # ── Numerical variable insights ───────────────────────────────────────────
    for col, stats in num.items():
        insights_list = []
        mean_v  = stats.get("mean", 0)
        std_v   = stats.get("std", 0)
        skew_v  = stats.get("skewness", 0)
        cv      = stats.get("cv_pct")
        n_out   = stats.get("outliers", 0)
        if cv is not None:
            if cv > 50:
                insights_list.append(
                    f"Variabilitas sangat tinggi (CV={cv:.0f}%) — data sangat tersebar, rata-rata kurang representatif." if is_id
                    else f"Very high variability (CV={cv:.0f}%) — data is widely spread, mean is not representative.")
            elif cv < 10:
                insights_list.append(
                    f"Variabilitas rendah (CV={cv:.0f}%) — data cukup homogen, konsisten." if is_id
                    else f"Low variability (CV={cv:.0f}%) — data is homogeneous and consistent.")
        if abs(skew_v) >= 1.5:
            direction = "kanan (ekor panjang ke kanan, ada nilai ekstrem tinggi)" if skew_v > 0 else "kiri (ekor panjang ke kiri, ada nilai ekstrem rendah)"
            insights_list.append(
                f"Distribusi sangat miring ke {direction} — transformasi log atau sqrt direkomendasikan sebelum pemodelan." if is_id
                else f"Highly {'right' if skew_v > 0 else 'left'}-skewed distribution — log or sqrt transformation recommended before modeling.")
        if n_out > 0:
            pct = round(n_out / rows * 100, 1) if rows else 0
            insights_list.append(
                f"Ada {n_out} outlier ({pct}%) — perlu diverifikasi apakah error atau nilai bisnis yang valid." if is_id
                else f"{n_out} outliers ({pct}%) — verify whether data entry errors or valid business values.")
        var_insights.append({
            "variable": col, "type": "numerical",
            "insight": " | ".join(insights_list) if insights_list else (
                f"Rata-rata {mean_v:,.2f}, std {std_v:,.2f} — distribusi normal." if is_id
                else f"Mean {mean_v:,.2f}, std {std_v:,.2f} — approximately normal distribution."),
            "business_relevance": (
                f"Kolom '{col}' merupakan metrik numerik kunci yang perlu dipantau tren dan penyimpangannya." if is_id
                else f"Column '{col}' is a key numerical metric that requires trend and deviation monitoring.")
        })
    # ── Categorical variable insights ─────────────────────────────────────────
    for col, stats in cat.items():
        n_unique = stats.get("n_unique", 0)
        top_val  = stats.get("top_value", "")
        top_pct  = stats.get("top_pct", 0)
        top5     = stats.get("top5", {})
        if top_pct > 80:
            insight = (f"Sangat tidak seimbang — '{top_val}' mendominasi {top_pct}% data. Jika digunakan untuk klasifikasi, perlu teknik balancing."
                       if is_id else
                       f"Highly imbalanced — '{top_val}' dominates {top_pct}% of data. If used for classification, balancing techniques required.")
        elif n_unique > 50:
            insight = (f"Kardinalitas tinggi ({n_unique} nilai unik) — pertimbangkan frequency encoding atau target encoding, bukan one-hot."
                       if is_id else
                       f"High cardinality ({n_unique} unique values) — consider frequency or target encoding instead of one-hot.")
        elif n_unique <= 2:
            insight = (f"Kolom biner ({n_unique} nilai: {list(top5.keys())}) — cocok sebagai variabel target klasifikasi biner."
                       if is_id else
                       f"Binary column ({n_unique} values: {list(top5.keys())}) — suitable as a binary classification target variable.")
        else:
            insight = (f"{n_unique} kategori unik, '{top_val}' terbanyak ({top_pct}%)."
                       if is_id else
                       f"{n_unique} unique categories, '{top_val}' is most frequent ({top_pct}%).")
        var_insights.append({
            "variable": col, "type": "categorical",
            "insight": insight,
            "business_relevance": (
                f"Kolom '{col}' bisa digunakan sebagai segmentasi atau variabel target analisis." if is_id
                else f"Column '{col}' can be used for segmentation or as an analysis target variable.")
        })
    # ── Correlation insights ──────────────────────────────────────────────────
    if corr:
        strong = [c for c in corr if abs(c["r"]) >= 0.7]
        moderate = [c for c in corr if 0.5 <= abs(c["r"]) < 0.7]
        if is_id:
            corr_txt = ""
            if strong:
                pairs = ", ".join(f"{c['col1']}↔{c['col2']} (r={c['r']:.2f})" for c in strong[:3])
                corr_txt += f"Korelasi kuat terdeteksi: {pairs}. Waspadai multikolinearitas jika variabel ini digunakan bersama dalam model regresi. "
                recs.append({"priority": "jangka_pendek", "action": f"Evaluasi multikolinearitas antara {strong[0]['col1']} dan {strong[0]['col2']} sebelum membangun model regresi.", "rationale": f"Korelasi r={strong[0]['r']:.2f} dapat menyebabkan estimasi koefisien yang tidak stabil."})
            if moderate:
                pairs = ", ".join(f"{c['col1']}↔{c['col2']} (r={c['r']:.2f})" for c in moderate[:3])
                corr_txt += f"Korelasi sedang: {pairs} — berpotensi sebagai fitur prediktif yang berguna."
            if not corr_txt:
                corr_txt = "Tidak ada korelasi signifikan antar variabel numerik — setiap variabel memberikan informasi independen."
        else:
            corr_txt = ""
            if strong:
                pairs = ", ".join(f"{c['col1']}↔{c['col2']} (r={c['r']:.2f})" for c in strong[:3])
                corr_txt += f"Strong correlations detected: {pairs}. Watch for multicollinearity if these variables are used together in regression models. "
                recs.append({"priority": "short_term", "action": f"Assess multicollinearity between {strong[0]['col1']} and {strong[0]['col2']} before building regression models.", "rationale": f"Correlation r={strong[0]['r']:.2f} can cause unstable coefficient estimates."})
            if moderate:
                pairs = ", ".join(f"{c['col1']}↔{c['col2']} (r={c['r']:.2f})" for c in moderate[:3])
                corr_txt += f"Moderate correlations: {pairs} — potentially useful predictive features."
            if not corr_txt:
                corr_txt = "No significant correlations between numerical variables — each variable provides independent information."
    else:
        corr_txt = ("Tidak cukup variabel numerik untuk analisis korelasi." if is_id
                    else "Insufficient numerical variables for correlation analysis.")
    # ── General modeling recommendation ──────────────────────────────────────
    if num and cat:
        recs.append({
            "priority": "jangka_pendek" if is_id else "short_term",
            "action": ("Lakukan feature engineering dan eksplorasi pemodelan (regresi/klasifikasi/clustering) menggunakan kombinasi variabel numerik dan kategorikal yang tersedia." if is_id
                       else "Perform feature engineering and explore modeling (regression/classification/clustering) using the available mix of numerical and categorical variables."),
            "rationale": ("Dataset memiliki kombinasi tipe variabel yang ideal untuk pemodelan supervised maupun unsupervised." if is_id
                          else "Dataset has an ideal mix of variable types for both supervised and unsupervised modeling.")
        })
    # ── Executive summary ─────────────────────────────────────────────────────
    n_issues = (1 if total_missing > 0 else 0) + (1 if duplicates > 0 else 0) + (1 if outliers > 0 else 0)
    if is_id:
        if is_clean:
            exec_summary = (f"Dataset dengan {rows:,} baris dan {ds.get('cols',0)} kolom ini berada dalam kondisi bersih dan siap untuk analisis mendalam. "
                            f"Terdapat {len(num)} variabel numerik dan {len(cat)} variabel kategorikal yang dapat dieksploitasi untuk pemodelan dan pengambilan keputusan.")
        else:
            exec_summary = (f"Dataset dengan {rows:,} baris dan {ds.get('cols',0)} kolom ini memerlukan pembersihan data sebelum dapat digunakan untuk analisis yang andal. "
                            f"Ditemukan {n_issues} isu kualitas data utama yang perlu ditangani segera untuk memastikan keakuratan insight yang dihasilkan.")
        quality_verdict = ("Data bersih dan dapat langsung digunakan untuk analisis dan pemodelan." if is_clean
                           else f"Kualitas data perlu ditingkatkan — terdapat {n_issues} isu aktif yang berisiko menghasilkan insight yang menyesatkan jika tidak ditangani.")
    else:
        if is_clean:
            exec_summary = (f"This dataset with {rows:,} rows and {ds.get('cols',0)} columns is clean and ready for in-depth analysis. "
                            f"It contains {len(num)} numerical and {len(cat)} categorical variables that can be leveraged for modeling and decision-making.")
        else:
            exec_summary = (f"This dataset with {rows:,} rows and {ds.get('cols',0)} columns requires data cleaning before it can be used for reliable analysis. "
                            f"{n_issues} major data quality issues were identified that must be addressed immediately to ensure the accuracy of generated insights.")
        quality_verdict = ("Data is clean and ready for immediate analysis and modeling." if is_clean
                           else f"Data quality needs improvement — {n_issues} active issues risk producing misleading insights if left unresolved.")
    return {
        "source":              "rule_based_fallback",
        "executive_summary":   exec_summary,
        "data_quality_verdict":quality_verdict,
        "key_findings":        key_findings,
        "variable_insights":   var_insights[:10],
        "correlations_insight":corr_txt,
        "recommendations":     recs[:8],
    }
def generate_smart_insights(df, num_cols, cat_cols, dt_cols=None, quality=None, lang='id'):
    """
    Main entry point for Smart Insights page.
    Tries Claude API first, then Gemini API; falls back to enhanced rule-based.
    Returns structured dict.
    """
    summary = _build_data_summary(df, num_cols, cat_cols, dt_cols, quality)
    prompt  = _build_prompt(summary, lang)
    
    # --------------------------------------------------------------------------
    # LAPIS 1: Coba Claude API
    # --------------------------------------------------------------------------
    if os.environ.get("ANTHROPIC_API_KEY"):
        raw_claude = _call_claude_api(prompt, lang)
        if raw_claude:
            try:
                clean = raw_claude.strip()
                if clean.startswith("```"):
                    clean = clean.split("```")[1]
                    if clean.startswith("json"):
                        clean = clean[4:]
                result = json.loads(clean.strip())
                result["source"] = "claude_api"
                return result
            except (json.JSONDecodeError, KeyError):
                pass

    # --------------------------------------------------------------------------
    # LAPIS 2: Coba Gemini API (Super Aman dari Blok Markdown)
    # --------------------------------------------------------------------------
    if os.environ.get("GEMINI_API_KEY"):
        raw_gemini = _call_gemini_api(prompt, lang)
        if raw_gemini:
            try:
                clean = raw_gemini.strip()
                if "```" in clean:
                    parts = clean.split("```")
                    for part in parts:
                        part_clean = part.strip()
                        if part_clean.startswith("json"):
                            part_clean = part_clean[4:].strip()
                        if part_clean.startswith("{") and part_clean.endswith("}"):
                            clean = part_clean
                            break
                
                result = json.loads(clean.strip())
                result["source"] = "gemini_api"
                return result
            except (json.JSONDecodeError, KeyError):
                pass

    # --------------------------------------------------------------------------
    # LAPIS 3: Fallback ke Rule-Based Lokal
    # --------------------------------------------------------------------------
    return _fallback_insights(summary, lang)