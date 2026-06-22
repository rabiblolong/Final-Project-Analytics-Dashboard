import pandas as pd, numpy as np, matplotlib, io, base64, warnings, re
matplotlib.use('Agg')
import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')

TEAL   = "#0d9488"
COLORS = ["#0d9488", "#0891b2", "#7c3aed", "#d97706", "#16a34a", "#dc2626"]

# ─── Common datetime patterns ─────────────────────────────────────────────────
_DT_PATTERNS = [
    # ISO / standard
    r'^\d{4}-\d{2}-\d{2}',          # 2024-01-15
    r'^\d{2}/\d{2}/\d{4}',          # 15/01/2024
    r'^\d{2}-\d{2}-\d{4}',          # 15-01-2024
    r'^\d{4}/\d{2}/\d{2}',          # 2024/01/15
    # Month-Year
    r'^\d{4}-\d{2}$',               # 2024-01
    r'^\d{2}-\d{4}$',               # 01-2024
    r'^[A-Za-z]{3,9}-?\s?\d{4}',    # Jan-2024 / January 2024
    r'^\d{4}[A-Za-z]{3}',           # 2024Jan
    # Quarter
    r'^Q[1-4]\s?\d{4}',             # Q1 2024
    r'^\d{4}\s?Q[1-4]',             # 2024 Q1
    # With time
    r'^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}',  # 2024-01-15 08:30
]
_DT_REGEX = [re.compile(p, re.IGNORECASE) for p in _DT_PATTERNS]

# Column name keywords that suggest time/period columns
_TIME_NAME_HINTS = [
    'date', 'time', 'datetime', 'timestamp', 'periode', 'period',
    'bulan', 'month', 'tahun', 'year', 'tanggal', 'tgl', 'dt',
    'hari', 'day', 'minggu', 'week', 'quarter', 'triwulan',
    'jam', 'hour', 'menit', 'minute'
]


def _b64(fig):
    b = io.BytesIO()
    fig.savefig(b, format='png', bbox_inches='tight', dpi=100, facecolor='white')
    plt.close(fig); b.seek(0)
    return "data:image/png;base64," + base64.b64encode(b.read()).decode()


def _matches_dt_pattern(sample_str: str) -> bool:
    """Check if a string looks like a date."""
    s = str(sample_str).strip()
    return any(rx.match(s) for rx in _DT_REGEX)


def detect_datetime_cols(df: pd.DataFrame) -> list:
    """
    Smarter datetime detection:
    1. Already parsed as datetime64
    2. Object/string columns that parse as dates (threshold lowered to 0.5)
    3. String columns matching known date patterns
    4. Numeric columns named like year/period (e.g. YEAR, TAHUN)
    5. Integer columns that look like years (1990–2100)
    Returns list of (col_name, parsed_series or None) tuples ranked by confidence.
    """
    results = []   # list of (confidence_score, col_name, parsed_or_none)

    for col in df.columns:
        col_lower = col.lower().strip()
        series = df[col]

        # ── 1. Already datetime ───────────────────────────────────────────────
        if pd.api.types.is_datetime64_any_dtype(series):
            results.append((1.0, col, series))
            continue

        # ── 2. Numeric YEAR column ────────────────────────────────────────────
        if pd.api.types.is_numeric_dtype(series):
            s = series.dropna()
            if len(s) == 0:
                continue
            # Check if column name hints at time
            name_hint = any(h in col_lower for h in _TIME_NAME_HINTS)
            # Check if values look like years (1900–2100)
            looks_like_year = (s >= 1900).all() and (s <= 2100).all() and s.nunique() >= 2
            if name_hint and looks_like_year:
                # Convert year ints to datetime (Jan 1 of that year)
                try:
                    parsed = pd.to_datetime(s.astype(int).astype(str), format='%Y', errors='coerce')
                    if parsed.notna().sum() / len(s) > 0.7:
                        results.append((0.75, col, parsed.reindex(series.index)))
                        continue
                except Exception:
                    pass
            # Numeric period column (e.g. 202401 = year+month)
            if name_hint and (s >= 190001).all() and (s <= 210012).all():
                try:
                    parsed = pd.to_datetime(s.astype(int).astype(str), format='%Y%m', errors='coerce')
                    ratio = parsed.notna().sum() / len(s)
                    if ratio > 0.7:
                        results.append((0.7, col, parsed.reindex(series.index)))
                        continue
                except Exception:
                    pass
            continue  # skip other numeric

        # ── 3. Object / string columns ────────────────────────────────────────
        if series.dtype not in (object, 'string', 'category'):
            continue

        s_str = series.dropna().astype(str)
        if len(s_str) == 0:
            continue

        # Sample up to 20 rows for pattern matching
        sample = s_str.head(20)
        pattern_hits = sum(1 for v in sample if _matches_dt_pattern(v))
        pattern_ratio = pattern_hits / len(sample)

        # Also try pandas parser
        try:
            parsed = pd.to_datetime(series, errors='coerce')
            parse_ratio = parsed.notna().sum() / len(series)
        except Exception:
            parsed = None
            parse_ratio = 0.0

        name_hint = any(h in col_lower for h in _TIME_NAME_HINTS)

        # Confidence formula
        conf = max(pattern_ratio * 0.6, parse_ratio * 0.5)
        if name_hint:
            conf += 0.2

        # Accept if any evidence
        if conf >= 0.35 or (name_hint and parse_ratio >= 0.3) or parse_ratio >= 0.6:
            effective_parsed = parsed if (parsed is not None and parse_ratio > 0) else None
            results.append((min(conf, 1.0), col, effective_parsed))

    # Sort by confidence descending
    results.sort(key=lambda x: x[0], reverse=True)
    return [(col, parsed) for _, col, parsed in results]


def _prep(df: pd.DataFrame, dc: str, nc: str, parsed_dt=None) -> pd.DataFrame:
    """Prepare a 2-column dataframe sorted by datetime."""
    d = df[[dc, nc]].copy()
    if parsed_dt is not None:
        d[dc] = parsed_dt.values
    else:
        d[dc] = pd.to_datetime(d[dc], errors='coerce')
    d = d.dropna().sort_values(dc).reset_index(drop=True)
    return d


def _adaptive_windows(n: int):
    """Choose sensible MA and rolling windows based on dataset size."""
    if n < 5:
        return 2, 3
    elif n < 15:
        return 3, 5
    elif n < 30:
        return 5, 10
    elif n < 100:
        return 7, 14
    elif n < 365:
        return 7, 30
    else:
        return 14, 90


def plot_timeseries(df, dc, nc, parsed_dt=None):
    d = _prep(df, dc, nc, parsed_dt)
    if len(d) < 2: return None
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(d[dc], d[nc], color=TEAL, linewidth=1.8)
    ax.fill_between(d[dc], d[nc], alpha=0.1, color=TEAL)
    ax.set_title(f'Time Series — {nc}', fontsize=11, fontweight='bold')
    ax.spines[['top', 'right']].set_visible(False)
    plt.xticks(rotation=30, ha='right')
    return _b64(fig)


def plot_moving_average(df, dc, nc, parsed_dt=None):
    d = _prep(df, dc, nc, parsed_dt)
    if len(d) < 3: return None
    w, _ = _adaptive_windows(len(d))
    d['MA'] = d[nc].rolling(w, min_periods=1).mean()
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(d[dc], d[nc], color='#94a3b8', linewidth=1, alpha=0.6, label='Actual')
    ax.plot(d[dc], d['MA'], color=TEAL, linewidth=2.5, label=f'MA({w})')
    ax.set_title(f'Moving Average ({w}) — {nc}', fontsize=11, fontweight='bold')
    ax.legend(fontsize=9)
    ax.spines[['top', 'right']].set_visible(False)
    plt.xticks(rotation=30, ha='right')
    return _b64(fig)


def plot_rolling_mean(df, dc, nc, parsed_dt=None):
    d = _prep(df, dc, nc, parsed_dt)
    if len(d) < 3: return None
    _, w = _adaptive_windows(len(d))
    d['RM']  = d[nc].rolling(w, min_periods=1).mean()
    d['STD'] = d[nc].rolling(w, min_periods=1).std().fillna(0)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(d[dc], d['RM'], color=TEAL, linewidth=2, label=f'Rolling Mean({w})')
    ax.fill_between(d[dc], d['RM'] - d['STD'], d['RM'] + d['STD'],
                    alpha=0.15, color=TEAL, label='±1 Std')
    ax.plot(d[dc], d[nc], color='#94a3b8', linewidth=0.8, alpha=0.5, label='Actual')
    ax.set_title(f'Rolling Mean ({w}) — {nc}', fontsize=11, fontweight='bold')
    ax.legend(fontsize=9)
    ax.spines[['top', 'right']].set_visible(False)
    plt.xticks(rotation=30, ha='right')
    return _b64(fig)


def plot_trend_line(df, dc, nc, parsed_dt=None):
    d = _prep(df, dc, nc, parsed_dt)
    if len(d) < 3: return None
    x = np.arange(len(d))
    z = np.polyfit(x, d[nc], 1)
    p = np.poly1d(z)
    trend = "📈 Naik" if z[0] > 0 else "📉 Turun"
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.scatter(d[dc], d[nc], color=TEAL, alpha=0.4, s=20, label='Data')
    ax.plot(d[dc], p(x), color='#dc2626', linewidth=2.5, label=f'Trend ({trend})')
    ax.set_title(f'Trend Line — {nc} ({trend})', fontsize=11, fontweight='bold')
    ax.legend(fontsize=9)
    ax.spines[['top', 'right']].set_visible(False)
    plt.xticks(rotation=30, ha='right')
    return _b64(fig)


def analyze_timeseries(df: pd.DataFrame) -> dict:
    """
    Main entry point. Returns:
    {
      has_ts: bool,
      date_col: str,
      date_col_type: 'datetime' | 'numeric_year' | 'string_date',
      charts: { col: { timeseries, moving_avg, rolling_mean, trend_line } },
      summaries: { col: { date_range, total_points, trend, mean, volatility } },
      error: str (only if has_ts=False),
      candidates: [str]  # all detected time-like cols
    }
    """
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # ── Detect datetime columns ───────────────────────────────────────────────
    dt_candidates = detect_datetime_cols(df)

    if not dt_candidates:
        # Last resort: if no datetime found, suggest numeric year columns
        year_like = [c for c in num_cols
                     if any(h in c.lower() for h in ['year','tahun','yr'])
                     and df[c].between(1900, 2100).all()]
        if year_like:
            return {
                "has_ts": False,
                "error": (
                    f"Tidak ada kolom datetime yang terdeteksi otomatis. "
                    f"Kolom '{year_like[0]}' kemungkinan berisi data tahun — "
                    f"pastikan nama kolomnya mengandung kata 'year', 'tahun', atau 'date'."
                ),
                "candidates": year_like,
            }
        return {
            "has_ts": False,
            "error": (
                "Tidak ada kolom datetime atau numerik waktu yang terdeteksi. "
                "Pastikan dataset memiliki kolom tanggal/waktu "
                "(contoh: 'Date', 'Tanggal', 'Year', 'Period', 'Bulan')."
            ),
            "candidates": [],
        }

    # Filter num_cols — exclude the datetime column itself
    dc, parsed_dt = dt_candidates[0]
    nc_list = [c for c in num_cols if c != dc]

    if not nc_list:
        return {
            "has_ts": False,
            "error": "Kolom datetime ditemukan, tetapi tidak ada kolom numerik untuk dianalisis.",
            "candidates": [d[0] for d in dt_candidates],
        }

    # Determine col type label for frontend
    if pd.api.types.is_datetime64_any_dtype(df[dc]):
        col_type = 'datetime'
    elif pd.api.types.is_numeric_dtype(df[dc]):
        col_type = 'numeric_year'
    else:
        col_type = 'string_date'

    result = {
        "has_ts":        True,
        "date_col":      dc,
        "date_col_type": col_type,
        "candidates":    [d[0] for d in dt_candidates],
        "charts":        {},
        "summaries":     {},
    }

    for nc in nc_list[:4]:
        d = _prep(df, dc, nc, parsed_dt)
        if len(d) < 2:
            continue

        x = np.arange(len(d))
        z = np.polyfit(x, d[nc], 1)
        result["summaries"][nc] = {
            "date_range":   f"{d[dc].min().date()} → {d[dc].max().date()}",
            "total_points": len(d),
            "trend":        "Naik" if z[0] > 0 else "Turun",
            "slope":        round(float(z[0]), 4),
            "mean":         round(float(d[nc].mean()), 2),
            "volatility":   round(float(d[nc].std()), 2),
        }

        charts = {}
        for key, fn in [
            ("timeseries",  plot_timeseries),
            ("moving_avg",  plot_moving_average),
            ("rolling_mean",plot_rolling_mean),
            ("trend_line",  plot_trend_line),
        ]:
            try:
                img = fn(df, dc, nc, parsed_dt)
                if img:
                    charts[key] = img
            except Exception as e:
                pass  # skip failed chart silently

        result["charts"][nc] = charts

    return result