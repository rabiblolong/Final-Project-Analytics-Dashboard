"""
backend/visualization.py
Adaptive chart selection based on data characteristics.

Logic per column type:
  Numerical:
    - binary (2 unique values)     → pie → bar
    - discrete/integer (≤15 unique) → bar → boxplot → histogram
    - continuous                   → histogram → density → boxplot → violin → qqplot
  Categorical:
    - binary (2 unique)            → pie → donut
    - low cardinality (3–8)        → bar → donut → countplot
    - medium cardinality (9–20)    → bar → countplot → pareto
    - high cardinality (>20)       → pareto → countplot
  Bivariate:
    - 2 numeric                    → scatter → regression → bubble → heatmap → pairplot
  Cat vs Num:                      → boxplot_by_cat → grouped_bar → violin_by_cat → strip
"""
import pandas as pd, numpy as np, matplotlib, io, base64, warnings, logging
matplotlib.use('Agg')
import matplotlib.pyplot as plt, seaborn as sns

warnings.filterwarnings('ignore')
sns.set_theme(style="whitegrid")

logger = logging.getLogger(__name__)

TEAL   = "#0d9488"
COLORS = ["#0d9488","#0891b2","#7c3aed","#d97706","#16a34a","#dc2626","#2563eb","#9333ea"]


def _b64(fig):
    b = io.BytesIO()
    fig.savefig(b, format='png', bbox_inches='tight', dpi=100, facecolor='white')
    plt.close(fig)
    b.seek(0)
    return "data:image/png;base64," + base64.b64encode(b.read()).decode()


# ─────────────────────────── Numerical charts ────────────────────────────────

def plot_histogram(df, col):
    fig, ax = plt.subplots(figsize=(6,4))
    ax.hist(df[col].dropna(), bins='auto', color=TEAL, edgecolor='white', alpha=0.85)
    ax.set_title(f'Histogram — {col}', fontsize=11, fontweight='bold')
    ax.spines[['top','right']].set_visible(False)
    return _b64(fig)

def plot_boxplot(df, col):
    fig, ax = plt.subplots(figsize=(6,4))
    bp = ax.boxplot(df[col].dropna(), patch_artist=True,
                    medianprops=dict(color='white', linewidth=2))
    bp['boxes'][0].set_facecolor(TEAL)
    ax.set_title(f'Boxplot — {col}', fontsize=11, fontweight='bold')
    ax.spines[['top','right']].set_visible(False)
    return _b64(fig)

def plot_density(df, col):
    s = df[col].dropna()
    if s.nunique() < 3: return None
    fig, ax = plt.subplots(figsize=(6,4))
    s.plot.kde(ax=ax, color=TEAL, linewidth=2)
    ax.fill_between(ax.lines[0].get_xdata(), ax.lines[0].get_ydata(), alpha=0.15, color=TEAL)
    ax.set_title(f'Density Plot — {col}', fontsize=11, fontweight='bold')
    ax.spines[['top','right']].set_visible(False)
    return _b64(fig)

def plot_qqplot(df, col):
    from scipy import stats as sp
    s = df[col].dropna()
    if len(s) < 8: return None
    fig, ax = plt.subplots(figsize=(6,4))
    (osm, osr), (slope, intercept, r) = sp.probplot(s, dist="norm")
    ax.scatter(osm, osr, color=TEAL, alpha=0.6, s=20)
    ax.plot(osm, slope*np.array(osm)+intercept, color='#dc2626',
            linewidth=1.5, label=f'R²={r**2:.3f}')
    ax.set_title(f'QQ Plot — {col}', fontsize=11, fontweight='bold')
    ax.legend(fontsize=9); ax.spines[['top','right']].set_visible(False)
    return _b64(fig)

def plot_violin(df, col):
    s = df[col].dropna()
    if len(s) < 5: return None
    fig, ax = plt.subplots(figsize=(6,4))
    parts = ax.violinplot(s, showmedians=True)
    for pc in parts['bodies']:
        pc.set_facecolor(TEAL); pc.set_alpha(0.7)
    parts['cmedians'].set_color('white')
    ax.set_title(f'Violin — {col}', fontsize=11, fontweight='bold')
    ax.spines[['top','right']].set_visible(False)
    return _b64(fig)


# ─────────────────────────── Categorical charts ───────────────────────────────

def _normalize_category_series(series):
    s = series.astype(object).fillna('Unknown').astype(str).str.strip()
    s = s.str.replace(r'\s+', ' ', regex=True)
    s = s.str.replace(r'^[\-\._\s]+|[\-\._\s]+$', '', regex=True)
    s = s.replace({
        r'^(?:nan|none|null|undefined|unknown|unk|n/?a|na|x|\?)$': 'Unknown',
        r'^(?:[-]+)$': 'Unknown',
        r'^(?:999+)$': 'Unknown'
    }, regex=True)
    s = s.where(~s.str.match(r'^\s*$'), 'Unknown')
    return s

def plot_bar(df, col):
    vc = _normalize_category_series(df[col]).value_counts().head(10)
    fig, ax = plt.subplots(figsize=(7,4))
    bars = ax.bar(range(len(vc)), vc.values, color=COLORS[:len(vc)], edgecolor='white')
    ax.set_xticks(range(len(vc)))
    ax.set_xticklabels(vc.index, rotation=30, ha='right', fontsize=9)
    for b in bars:
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.1,
                int(b.get_height()), ha='center', va='bottom', fontsize=8)
    ax.set_title(f'Bar Chart — {col}', fontsize=11, fontweight='bold')
    ax.spines[['top','right']].set_visible(False)
    return _b64(fig)

def plot_pie(df, col):
    vc = _normalize_category_series(df[col]).value_counts().head(8)
    fig, ax = plt.subplots(figsize=(6,5))
    wedges, texts, autotexts = ax.pie(
        vc.values, labels=vc.index, autopct='%1.1f%%',
        colors=COLORS[:len(vc)], startangle=90,
        wedgeprops=dict(edgecolor='white', linewidth=2))
    for t in autotexts: t.set_fontsize(9); t.set_color('white')
    ax.set_title(f'Pie Chart — {col}', fontsize=11, fontweight='bold')
    return _b64(fig)

def plot_donut(df, col):
    vc = _normalize_category_series(df[col]).value_counts().head(8)
    fig, ax = plt.subplots(figsize=(6,5))
    wedges, texts, autotexts = ax.pie(
        vc.values, labels=vc.index, autopct='%1.1f%%',
        colors=COLORS[:len(vc)], startangle=90,
        wedgeprops=dict(width=0.4, edgecolor='white', linewidth=2))
    for t in autotexts: t.set_fontsize(9); t.set_color('#333333')
    ax.set_title(f'Donut Chart — {col}', fontsize=11, fontweight='bold')
    ax.set(aspect='equal')
    return _b64(fig)

def plot_countplot(df, col):
    vc = _normalize_category_series(df[col]).value_counts().head(10)
    fig, ax = plt.subplots(figsize=(7,4))
    bars = ax.barh(range(len(vc)), vc.values, color=TEAL, alpha=0.85, edgecolor='white')
    ax.set_yticks(range(len(vc))); ax.set_yticklabels(vc.index, fontsize=9)
    for b in bars:
        ax.text(b.get_width()+0.1, b.get_y()+b.get_height()/2,
                int(b.get_width()), va='center', fontsize=8)
    ax.set_title(f'Count Plot — {col}', fontsize=11, fontweight='bold')
    ax.spines[['top','right']].set_visible(False)
    return _b64(fig)

def plot_pareto(df, col):
    vc  = _normalize_category_series(df[col]).value_counts().head(10)
    cum = vc.cumsum() / vc.sum() * 100
    fig, ax1 = plt.subplots(figsize=(7,4))
    ax1.bar(range(len(vc)), vc.values, color=TEAL, alpha=0.8, edgecolor='white')
    ax1.set_xticks(range(len(vc)))
    ax1.set_xticklabels(vc.index, rotation=30, ha='right', fontsize=9)
    ax2 = ax1.twinx()
    ax2.plot(range(len(vc)), cum.values, color='#dc2626', marker='o', markersize=5, linewidth=2)
    ax2.axhline(80, color='#dc2626', linestyle='--', alpha=0.5); ax2.set_ylim(0, 105)
    ax1.set_title(f'Pareto — {col}', fontsize=11, fontweight='bold')
    return _b64(fig)


# ─────────────────────────── Bivariate charts ────────────────────────────────

def plot_heatmap(df, num_cols):
    if len(num_cols) < 2: return None
    corr = df[num_cols].corr()
    fig, ax = plt.subplots(figsize=(max(6, len(num_cols)), max(5, len(num_cols)-1)))
    sns.heatmap(corr, annot=True, fmt='.2f', cmap='RdYlGn', center=0,
                square=True, ax=ax, linewidths=0.5, annot_kws={'size':9}, vmin=-1, vmax=1)
    ax.set_title('Correlation Heatmap', fontsize=11, fontweight='bold')
    return _b64(fig)

def plot_scatter(df, cx, cy):
    fig, ax = plt.subplots(figsize=(6,4))
    ax.scatter(df[cx], df[cy], color=TEAL, alpha=0.6, s=30, edgecolors='white', linewidth=0.5)
    ax.set_xlabel(cx); ax.set_ylabel(cy)
    ax.set_title(f'Scatter — {cx} vs {cy}', fontsize=11, fontweight='bold')
    ax.spines[['top','right']].set_visible(False)
    return _b64(fig)

def plot_regression(df, cx, cy):
    from scipy import stats as sp
    data = df[[cx, cy]].dropna()
    if len(data) < 3: return None
    slope, intercept, r, p, _ = sp.linregress(data[cx], data[cy])
    fig, ax = plt.subplots(figsize=(6,4))
    ax.scatter(data[cx], data[cy], color=TEAL, alpha=0.5, s=25)
    xl = np.linspace(data[cx].min(), data[cx].max(), 100)
    ax.plot(xl, slope*xl+intercept, color='#dc2626', linewidth=2, label=f'R²={r**2:.3f}')
    ax.set_xlabel(cx); ax.set_ylabel(cy)
    ax.set_title(f'Regression — {cx} vs {cy}', fontsize=11, fontweight='bold')
    ax.legend(fontsize=9); ax.spines[['top','right']].set_visible(False)
    return _b64(fig)

def plot_bubble(df, cx, cy, cs=None):
    fig, ax = plt.subplots(figsize=(6,4))
    sizes = df[cs].fillna(1)*20 if cs and cs in df.columns else 40
    ax.scatter(df[cx], df[cy], s=sizes, color=TEAL, alpha=0.5, edgecolors='white')
    ax.set_xlabel(cx); ax.set_ylabel(cy)
    ax.set_title(f'Bubble — {cx} vs {cy}', fontsize=11, fontweight='bold')
    ax.spines[['top','right']].set_visible(False)
    return _b64(fig)

def plot_pairplot(df, num_cols):
    if len(num_cols) < 2: return None
    g = sns.pairplot(df[num_cols[:5]].dropna(), diag_kind='kde',
                     plot_kws={'alpha':0.5, 'color':TEAL},
                     diag_kws={'color':TEAL, 'fill':True})
    g.fig.suptitle('Pair Plot', y=1.02, fontsize=11, fontweight='bold')
    return _b64(g.fig)


# ─────────────────────────── Cat vs Num charts ───────────────────────────────

def plot_boxplot_by_cat(df, nc, cc):
    cats_series = _normalize_category_series(df[cc])
    cats = cats_series.value_counts().head(8).index.tolist()
    data = [df[cats_series == c][nc].dropna().values for c in cats]
    fig, ax = plt.subplots(figsize=(7,4))
    bp = ax.boxplot(data, labels=cats, patch_artist=True)
    for i, b in enumerate(bp['boxes']):
        b.set_facecolor(COLORS[i % len(COLORS)]); b.set_alpha(0.7)
    ax.set_xticklabels(cats, rotation=25, ha='right', fontsize=9)
    ax.set_title(f'Boxplot by Category — {nc} by {cc}', fontsize=11, fontweight='bold')
    ax.spines[['top','right']].set_visible(False)
    return _b64(fig)

def plot_violin_by_cat(df, nc, cc):
    cats_series = _normalize_category_series(df[cc])
    cats = cats_series.value_counts().head(6).index.tolist()
    data = [df[cats_series == c][nc].dropna().values for c in cats]
    fig, ax = plt.subplots(figsize=(7,4))
    parts = ax.violinplot(data, showmedians=True)
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(COLORS[i % len(COLORS)]); pc.set_alpha(0.65)
    ax.set_xticks(range(1, len(cats)+1))
    ax.set_xticklabels(cats, rotation=25, ha='right', fontsize=9)
    ax.set_title(f'Violin by Category — {nc} by {cc}', fontsize=11, fontweight='bold')
    ax.spines[['top','right']].set_visible(False)
    return _b64(fig)

def plot_grouped_bar(df, cc, nc):
    grp = df.groupby(_normalize_category_series(df[cc]))[nc].mean().head(10)
    fig, ax = plt.subplots(figsize=(7,4))
    bars = ax.bar(range(len(grp)), grp.values, color=COLORS[:len(grp)], edgecolor='white')
    ax.set_xticks(range(len(grp)))
    ax.set_xticklabels(grp.index, rotation=25, ha='right', fontsize=9)
    for b in bars:
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.01*grp.max(),
                f'{b.get_height():.1f}', ha='center', va='bottom', fontsize=8)
    ax.set_title(f'Grouped Bar — Mean {nc} by {cc}', fontsize=11, fontweight='bold')
    ax.spines[['top','right']].set_visible(False)
    return _b64(fig)

def plot_strip(df, nc, cc):
    cats_series = _normalize_category_series(df[cc])
    cats = cats_series.value_counts().head(6).index.tolist()
    fig, ax = plt.subplots(figsize=(7,4))
    for i, cat in enumerate(cats):
        vals   = df[cats_series == cat][nc].dropna()
        jitter = np.random.uniform(-0.2, 0.2, len(vals))
        ax.scatter(np.full(len(vals), i)+jitter, vals,
                   color=COLORS[i % len(COLORS)], alpha=0.5, s=18)
    ax.set_xticks(range(len(cats)))
    ax.set_xticklabels(cats, rotation=25, ha='right', fontsize=9)
    ax.set_title(f'Strip Plot — {nc} by {cc}', fontsize=11, fontweight='bold')
    ax.spines[['top','right']].set_visible(False)
    return _b64(fig)


# ─────────────────────────── Safe wrapper ─────────────────────────────────────

def _safe(fn, label, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        logger.warning(f"Chart '{label}' gagal: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# ADAPTIVE CHART TYPE SELECTION
# ══════════════════════════════════════════════════════════════════════════════

def _classify_numerical(series: pd.Series) -> str:
    """Classify a numerical column for best default chart selection."""
    s = series.dropna()
    n_unique = s.nunique()
    if n_unique <= 2:
        return 'binary'
    # Check if all values are integers
    is_integer = np.array_equal(s, s.astype(int, errors='ignore'))
    if is_integer and n_unique <= 15:
        return 'discrete'
    return 'continuous'


def _classify_categorical(series: pd.Series) -> str:
    """Classify a categorical column for best default chart selection."""
    n_unique = series.dropna().nunique()
    if n_unique <= 2:
        return 'binary'
    elif n_unique <= 8:
        return 'low'
    elif n_unique <= 20:
        return 'medium'
    else:
        return 'high'


def _default_num_charts(col: str, col_type: str, col_index: int = 0) -> list:
    """
    Return ordered chart list. The FIRST item = default shown chart.
    Each column gets a DIFFERENT default so the dashboard looks varied,
    while still being appropriate for the data type.

    Logic per type:
      binary     → always histogram (values 0/1, distribution is most informative)
      discrete   → rotate: boxplot → histogram → violin → qqplot → density → ...
      continuous → rotate: histogram → density → boxplot → violin → qqplot → ...
    """
    if col_type == 'binary':
        return ['histogram', 'boxplot', 'density', 'qqplot', 'violin']

    elif col_type == 'discrete':
        rotations = [
            ['boxplot',   'histogram', 'violin',   'density',  'qqplot'],
            ['histogram', 'boxplot',   'density',  'violin',   'qqplot'],
            ['violin',    'boxplot',   'histogram','density',  'qqplot'],
            ['qqplot',    'histogram', 'boxplot',  'density',  'violin'],
            ['density',   'histogram', 'boxplot',  'violin',   'qqplot'],
        ]
        return rotations[col_index % len(rotations)]

    else:  # continuous
        rotations = [
            ['histogram', 'density', 'boxplot',   'violin', 'qqplot'],
            ['density',   'boxplot', 'histogram', 'violin', 'qqplot'],
            ['boxplot',   'histogram','density',  'violin', 'qqplot'],
            ['violin',    'histogram','density',  'boxplot','qqplot'],
            ['qqplot',    'histogram','density',  'boxplot','violin'],
        ]
        return rotations[col_index % len(rotations)]


def _default_cat_charts(col: str, col_type: str, col_index: int = 0) -> list:
    """
    Return ordered chart list with varied defaults per column.

    binary  → pie or donut alternating
    low     → rotate: bar → donut → countplot → pie → pareto
    medium  → rotate: bar → countplot → pareto → donut → pie
    high    → always pareto first (best for high-cardinality), then countplot
    """
    if col_type == 'binary':
        rotations = [
            ['pie',   'donut', 'bar', 'countplot', 'pareto'],
            ['donut', 'pie',   'bar', 'countplot', 'pareto'],
        ]
        return rotations[col_index % 2]

    elif col_type == 'low':
        rotations = [
            ['bar',       'donut',    'countplot', 'pie',    'pareto'],
            ['donut',     'bar',      'countplot', 'pie',    'pareto'],
            ['countplot', 'bar',      'donut',     'pie',    'pareto'],
            ['pie',       'bar',      'donut',     'countplot','pareto'],
            ['pareto',    'bar',      'donut',     'countplot','pie'],
        ]
        return rotations[col_index % len(rotations)]

    elif col_type == 'medium':
        rotations = [
            ['bar',       'countplot', 'pareto', 'donut', 'pie'],
            ['countplot', 'bar',       'pareto', 'donut', 'pie'],
            ['pareto',    'bar',       'countplot','donut','pie'],
            ['donut',     'bar',       'countplot','pareto','pie'],
        ]
        return rotations[col_index % len(rotations)]

    else:  # high cardinality
        return ['pareto', 'countplot', 'bar', 'donut', 'pie']


def get_column_chart_recommendations(df) -> dict:
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
    recs = {'numerical': {}, 'categorical': {}}

    for i, col in enumerate(num_cols):
        ctype = _classify_numerical(df[col])
        order = _default_num_charts(col, ctype, col_index=i)
        recs['numerical'][col] = {
            'col_type':   ctype,
            'default':    order[0],
            'all_charts': order,
            'label': {
                'binary':     f'{col} — Binary Numeric',
                'discrete':   f'{col} — Discrete Integer',
                'continuous': f'{col} — Continuous',
            }.get(ctype, col)
        }

    for i, col in enumerate(cat_cols):
        ctype    = _classify_categorical(df[col])
        order    = _default_cat_charts(col, ctype, col_index=i)
        n_unique = df[col].dropna().nunique()
        recs['categorical'][col] = {
            'col_type':   ctype,
            'n_unique':   n_unique,
            'default':    order[0],
            'all_charts': order,
            'label': {
                'binary': f'{col} — Binary ({n_unique} values)',
                'low':    f'{col} — Low Cardinality ({n_unique} values)',
                'medium': f'{col} — Medium Cardinality ({n_unique} values)',
                'high':   f'{col} — High Cardinality ({n_unique} values)',
            }.get(ctype, col)
        }

    return recs


# ══════════════════════════════════════════════════════════════════════════════
# MAIN GENERATORS
# ══════════════════════════════════════════════════════════════════════════════

def generate_interactive_data(df):
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
    payload  = {'numerical': {}, 'categorical': {}, 'bivariate': {}, 'cat_vs_num': {}, 'correlation_matrix': None}

    for col in num_cols[:5]:
        values = df[col].dropna().astype(float)
        if values.empty: continue
        counts, edges = np.histogram(values, bins='auto')
        payload['numerical'][col] = {
            'labels': [f"{edges[i]:.2f}–{edges[i+1]:.2f}" for i in range(len(counts))],
            'counts': counts.astype(int).tolist(),
            'mean':   float(values.mean()),
            'std':    float(values.std()),
            'min':    float(values.min()),
            'max':    float(values.max()),
            'col_type': _classify_numerical(values),
        }

    for col in cat_cols[:5]:
        vc = _normalize_category_series(df[col]).value_counts().head(8)
        payload['categorical'][col] = {
            'labels':   vc.index.tolist(),
            'counts':   vc.values.astype(int).tolist(),
            'total':    int(vc.sum()),
            'n_unique': int(df[col].dropna().nunique()),
            'col_type': _classify_categorical(df[col]),
        }

    if len(num_cols) >= 2:
        x, y = num_cols[0], num_cols[1]
        data  = df[[x, y]].dropna()
        payload['bivariate'] = {
            'x_col': x, 'y_col': y,
            'points': data.head(500).to_dict(orient='records')  # cap for perf
        }
        # Real correlation matrix (not random!) — used for heatmap rendering
        try:
            corr_cols = num_cols[:6]
            corr_df = df[corr_cols].corr().round(3)
            payload['correlation_matrix'] = {
                'columns': corr_cols,
                'matrix':  corr_df.values.tolist(),
            }
        except Exception:
            payload['correlation_matrix'] = None

    if num_cols and cat_cols:
        nc, cc = num_cols[0], cat_cols[0]
        grp = df.groupby(_normalize_category_series(df[cc]))[nc].mean().head(8)
        payload['cat_vs_num'] = {
            'category_col': cc, 'numeric_col': nc,
            'labels': grp.index.tolist(),
            'values': grp.values.astype(float).round(2).tolist()
        }

    # Include chart recommendations for frontend adaptive rendering
    payload['recommendations'] = get_column_chart_recommendations(df)

    return payload


def generate_all_charts(df):
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
    charts   = {'numerical': {}, 'categorical': {}, 'bivariate': {}, 'cat_vs_num': {}}

    FNUM = {
        'histogram': plot_histogram,
        'boxplot':   plot_boxplot,
        'density':   plot_density,
        'qqplot':    plot_qqplot,
        'violin':    plot_violin,
    }
    FCAT = {
        'bar':       plot_bar,
        'donut':     plot_donut,
        'countplot': plot_countplot,
        'pie':       plot_pie,
        'pareto':    plot_pareto,
    }

    for i, col in enumerate(num_cols[:8]):
        ctype   = _classify_numerical(df[col])
        ordered = _default_num_charts(col, ctype, col_index=i)
        charts['numerical'][col] = {
            '_meta': {'col_type': ctype, 'default': ordered[0], 'order': ordered}
        }
        for k in ordered:
            if k not in FNUM: continue
            result = _safe(FNUM[k], f"num/{k}/{col}", df, col)
            if result:
                charts['numerical'][col][k] = result

    for i, col in enumerate(cat_cols[:8]):
        ctype   = _classify_categorical(df[col])
        ordered = _default_cat_charts(col, ctype, col_index=i)
        charts['categorical'][col] = {
            '_meta': {'col_type': ctype, 'default': ordered[0], 'order': ordered,
                      'n_unique': int(df[col].dropna().nunique())}
        }
        for k in ordered:
            if k not in FCAT: continue
            result = _safe(FCAT[k], f"cat/{k}/{col}", df, col)
            if result:
                charts['categorical'][col][k] = result

    # Bivariate — only if ≥2 numeric cols
    if len(num_cols) >= 2:
        cx, cy = num_cols[0], num_cols[1]
        cs     = num_cols[2] if len(num_cols) > 2 else None
        for key, fn, args in [
            ('scatter',    plot_scatter,    (df, cx, cy)),
            ('regression', plot_regression, (df, cx, cy)),
            ('heatmap',    plot_heatmap,    (df, num_cols)),
            ('pairplot',   plot_pairplot,   (df, num_cols)),
            ('bubble',     plot_bubble,     (df, cx, cy, cs)),
        ]:
            result = _safe(fn, f"biv/{key}", *args)
            if result:
                charts['bivariate'][key] = result

    # Cat vs Num — only if both exist
    if num_cols and cat_cols:
        nc, cc = num_cols[0], cat_cols[0]
        for key, fn, args in [
            ('boxplot_by_cat', plot_boxplot_by_cat, (df, nc, cc)),
            ('grouped_bar',    plot_grouped_bar,    (df, cc, nc)),
            ('violin_by_cat',  plot_violin_by_cat,  (df, nc, cc)),
            ('strip',          plot_strip,           (df, nc, cc)),
        ]:
            result = _safe(fn, f"cvn/{key}", *args)
            if result:
                charts['cat_vs_num'][key] = result

    return charts