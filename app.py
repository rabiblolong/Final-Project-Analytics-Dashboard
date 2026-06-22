from flask import Flask, request, jsonify, render_template, send_file, session, redirect, url_for, Response
from backend.data_loader          import load_file, SUPPORTED_EXTENSIONS
from backend.preprocessing        import detect_column_types, get_preview
from backend.descriptive_stats    import compute_numerical_stats
from backend.categorical_analysis import compute_categorical_stats
from backend.insight_generator    import generate_insights, generate_smart_insights
from backend.visualization        import generate_all_charts, generate_interactive_data, get_column_chart_recommendations
from backend.time_series          import analyze_timeseries
from backend.export_report        import export_csv, export_excel, export_html, export_pdf
from backend.data_cleaning.cleaning import clean_dataset
from backend.auth                 import register_user, login_user, get_user_by_id
import io, os, logging, pandas as pd
from flask_caching import Cache

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'frontend', 'templates'),
            static_folder=os.path.join(BASE_DIR, 'frontend', 'static'))

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-ganti-di-production')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 3600
cache = Cache(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _key(suffix):
    sid = session.get('uid')
    if not sid:
        import uuid; sid = str(uuid.uuid4()); session['uid'] = sid
    return f"{sid}:{suffix}"


def _require_auth():
    """Return user dict if logged in, else None."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return get_user_by_id(user_id)


def _compute_quality(df, nc):
    miss = df.isnull().sum()
    total_miss = int(miss.sum())
    dups = int(df.duplicated().sum())
    out_count, out_cols = 0, {}
    for col in nc:
        try:
            q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
            iqr = q3 - q1
            n = int(((df[col] < q1 - 1.5*iqr) | (df[col] > q3 + 1.5*iqr)).sum())
            if n: out_cols[col] = n; out_count += n
        except: pass
    return {
        'total_missing':   total_miss,
        'missing_pct':     round(total_miss / max(df.size, 1) * 100, 2),
        'missing_per_col': {k: int(v) for k, v in miss[miss > 0].items()},
        'duplicates':      dups,
        'outliers':        out_count,
        'outlier_cols':    out_cols,
        'is_clean':        (total_miss == 0 and dups == 0 and out_count == 0),
    }


# ─── Auth routes ─────────────────────────────────────────────────────────────

@app.route('/auth/register', methods=['POST'])
def auth_register():
    data = request.json or {}
    result = register_user(
        email    = data.get('email', ''),
        password = data.get('password', ''),
        name     = data.get('name', '')
    )
    if result['ok']:
        session['user_id'] = result['user']['id']
        session['user_name'] = result['user']['name']
        return jsonify({'ok': True, 'user': result['user']})
    return jsonify({'ok': False, 'error': result['error']}), 400


@app.route('/auth/login', methods=['POST'])
def auth_login():
    data = request.json or {}
    result = login_user(
        email    = data.get('email', ''),
        password = data.get('password', '')
    )
    if result['ok']:
        session['user_id'] = result['user']['id']
        session['user_name'] = result['user']['name']
        return jsonify({'ok': True, 'user': result['user']})
    return jsonify({'ok': False, 'error': result['error']}), 401


@app.route('/auth/logout', methods=['POST'])
def auth_logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    return jsonify({'ok': True})


@app.route('/auth/me')
def auth_me():
    user = _require_auth()
    if user:
        return jsonify({'ok': True, 'user': user})
    return jsonify({'ok': False}), 401


# ─── Main app ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if not _require_auth():
        return jsonify({'error': 'Login dulu.'}), 401
    if 'file' not in request.files:
        return jsonify({'error': 'Tidak ada file.'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nama file kosong.'}), 400
    ext = ('.' + file.filename.rsplit('.', 1)[-1].lower()) if '.' in file.filename else ''
    if ext not in SUPPORTED_EXTENSIONS:
        return jsonify({'error': f"Format '{ext}' tidak didukung."}), 400
    try:
        df, fi = load_file(file)
        df = df.copy(deep=True)
        ct = detect_column_types(df)
        nc, cc = ct['numerical'], ct['categorical']

        insights = ''
        try:
            insights = generate_insights(df, nc, cc)
        except Exception as ex:
            logger.warning(f"generate_insights gagal: {ex}")
            insights = 'Analisis insight gagal, tetapi data berhasil diproses.'

        quality = _compute_quality(df, nc)

        # Get adaptive chart recommendations
        chart_recs = {}
        try:
            chart_recs = get_column_chart_recommendations(df)
        except Exception as ex:
            logger.warning(f"chart recommendations gagal: {ex}")

        result = {
            'meta': {
                'total_rows': int(df.shape[0]), 'total_cols': int(df.shape[1]),
                'numeric_cols': int(len(nc)), 'categorical_cols': int(len(cc)),
                'has_datetime': len(ct['datetime']) > 0,
                'filename': fi.get('filename', ''),
            },
            'preview_data':        get_preview(df, 10),
            'preview_5':           get_preview(df, 5),
            'numeric_summary':     compute_numerical_stats(df, nc),
            'categorical_summary': compute_categorical_stats(df, cc),
            'insights':            insights,
            'file_info':           fi,
            'quality':             quality,
            'all_columns':         df.columns.tolist(),
            'chart_recommendations': chart_recs,  # <-- adaptive chart metadata
        }
        cache.set(_key('df'), df)
        cache.set(_key('df_original'), df.copy(deep=True))
        cache.set(_key('stats'), result)
        cache.set(_key('info'), fi)
        cache.delete(_key('viz')); cache.delete(_key('viz_data'))
        cache.delete(_key('smart_id')); cache.delete(_key('smart_en'))
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.exception("Error upload"); return jsonify({'error': 'Gagal memproses file.'}), 500


@app.route('/preview')
def preview():
    if not _require_auth(): return jsonify({'error': 'Login dulu.'}), 401
    df = cache.get(_key('df'))
    if df is None: return jsonify({'error': 'Upload file dulu.'}), 400
    try:
        page = max(1, int(request.args.get('page', 1)))
        size = 10; start, end = (page-1)*size, page*size
        total_pages = max(1, -(-len(df)//size))
        from backend.preprocessing import clean_for_json
        chunk = clean_for_json(df.iloc[start:end])
        return jsonify({'rows': chunk.to_dict(orient='records'), 'columns': df.columns.tolist(),
                        'page': page, 'total_pages': total_pages, 'total_rows': len(df)})
    except Exception as e:
        logger.exception("Error preview"); return jsonify({'error': 'Gagal preview.'}), 500


@app.route('/data-quality')
def data_quality():
    if not _require_auth(): return jsonify({'error': 'Login dulu.'}), 401
    df = cache.get(_key('df'))
    if df is None: return jsonify({'error': 'Upload file dulu.'}), 400
    try:
        ct = detect_column_types(df); nc = ct['numerical']
        miss = df.isnull().sum()
        out_cols = {}
        for col in nc:
            try:
                q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75); iqr = q3-q1
                n = int(((df[col]<q1-1.5*iqr)|(df[col]>q3+1.5*iqr)).sum())
                if n: out_cols[col] = n
            except: pass
        return jsonify({'total_rows': int(len(df)), 'total_cols': int(len(df.columns)),
                        'total_missing': int(miss.sum()),
                        'missing_per_col': {k: int(v) for k,v in miss[miss>0].items()},
                        'duplicates': int(df.duplicated().sum()),
                        'outlier_cols': out_cols, 'outliers_total': sum(out_cols.values()),
                        'dtypes': {col: str(df[col].dtype) for col in df.columns}})
    except Exception as e:
        logger.exception("Error data-quality"); return jsonify({'error': 'Gagal.'}), 500


@app.route('/clean/preview-issues')
def clean_preview_issues():
    """Return only rows that have missing values or outliers, for focused review."""
    if not _require_auth(): return jsonify({'error': 'Login dulu.'}), 401
    df = cache.get(_key('df'))
    if df is None: return jsonify({'error': 'Upload file dulu.'}), 400
    try:
        ct = detect_column_types(df)
        nc = ct['numerical']

        # Rows with any missing value
        missing_mask = df.isnull().any(axis=1)
        missing_rows = df[missing_mask].head(50)

        # Rows with any outlier (IQR) in any numeric column
        outlier_mask = pd.Series([False] * len(df), index=df.index)
        outlier_cols_detail = {}
        for col in nc:
            try:
                q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
                iqr = q3 - q1
                col_mask = (df[col] < q1 - 1.5*iqr) | (df[col] > q3 + 1.5*iqr)
                if col_mask.any():
                    outlier_cols_detail[col] = int(col_mask.sum())
                outlier_mask |= col_mask.fillna(False)
            except Exception:
                pass
        outlier_rows = df[outlier_mask].head(50)

        from backend.preprocessing import clean_for_json
        missing_clean  = clean_for_json(missing_rows)
        outlier_clean  = clean_for_json(outlier_rows)

        return jsonify({
            'columns':          df.columns.tolist(),
            'numeric_cols':     nc,
            'categorical_cols': ct['categorical'],
            'missing_rows':     missing_clean.to_dict(orient='records'),
            'missing_total':    int(missing_mask.sum()),
            'missing_per_col':  {k: int(v) for k, v in df.isnull().sum()[df.isnull().sum() > 0].items()},
            'outlier_rows':     outlier_clean.to_dict(orient='records'),
            'outlier_total':    int(outlier_mask.sum()),
            'outlier_per_col':  outlier_cols_detail,
        })
    except Exception as e:
        logger.exception("Error preview-issues"); return jsonify({'error': str(e)}), 500


@app.route('/clean', methods=['POST'])
def clean():
    if not _require_auth(): return jsonify({'error': 'Login dulu.'}), 401
    df = cache.get(_key('df'))
    if df is None: return jsonify({'error': 'Upload file dulu.'}), 400
    data = request.json or {}
    ops = data.get('ops', [])
    target_cols = data.get('columns', [])  # if empty/None -> apply to all relevant columns
    if not ops: return jsonify({'error': 'Tidak ada operasi.'}), 400
    try:
        df = df.copy(deep=True); log = []

        def _scope(cols_all):
            """Restrict to user-selected columns if provided, else use all relevant columns."""
            if target_cols:
                return [c for c in cols_all if c in target_cols]
            return cols_all

        for op in ops:
            if op == 'drop_duplicates':
                b = len(df); df = df.drop_duplicates(); log.append(f"Duplikat dihapus: {b-len(df)} baris")
            elif op == 'drop_missing_rows':
                b = len(df)
                cols_to_check = _scope(df.columns.tolist())
                df = df.dropna(subset=cols_to_check) if target_cols else df.dropna()
                log.append(f"Baris missing dihapus: {b-len(df)} baris" + (f" (kolom: {', '.join(cols_to_check)})" if target_cols else ""))
            elif op == 'fill_missing_mean':
                ct = detect_column_types(df)
                for col in _scope(ct['numerical']):
                    n = int(df[col].isnull().sum())
                    if n: df[col] = df[col].fillna(df[col].mean()); log.append(f"'{col}': {n} diisi mean")
            elif op == 'fill_missing_median':
                ct = detect_column_types(df)
                for col in _scope(ct['numerical']):
                    n = int(df[col].isnull().sum())
                    if n: df[col] = df[col].fillna(df[col].median()); log.append(f"'{col}': {n} diisi median")
            elif op == 'fill_missing_mode':
                ct = detect_column_types(df)
                for col in _scope(ct['categorical']):
                    n = int(df[col].isnull().sum()); mv = df[col].mode()
                    if n and not mv.empty: df[col] = df[col].fillna(mv[0]); log.append(f"'{col}': {n} diisi mode")
            elif op == 'fill_missing_unknown':
                ct = detect_column_types(df)
                for col in _scope(ct['categorical']):
                    n = int(df[col].isnull().sum())
                    if n: df[col] = df[col].fillna('Unknown'); log.append(f"'{col}': {n} diisi 'Unknown'")
            elif op == 'remove_outliers_iqr':
                ct = detect_column_types(df); b = len(df)
                mask = pd.Series([True]*len(df), index=df.index)
                cols_to_check = _scope(ct['numerical'])
                for col in cols_to_check:
                    try:
                        q1,q3 = df[col].quantile(0.25),df[col].quantile(0.75); iqr=q3-q1
                        mask &= (df[col]>=q1-1.5*iqr)&(df[col]<=q3+1.5*iqr)
                    except: pass
                df = df[mask]; log.append(f"Outlier IQR dihapus: {b-len(df)} baris" + (f" (kolom: {', '.join(cols_to_check)})" if target_cols else ""))
            elif op == 'cap_outliers_iqr':
                ct = detect_column_types(df)
                for col in _scope(ct['numerical']):
                    try:
                        q1,q3 = df[col].quantile(0.25),df[col].quantile(0.75); iqr=q3-q1
                        df[col] = df[col].clip(lower=q1-1.5*iqr, upper=q3+1.5*iqr)
                        log.append(f"'{col}': outlier di-cap IQR")
                    except: pass
            elif op == 'normalize_strings':
                from backend.data_cleaning.cleaning import normalize_string_series
                ct = detect_column_types(df)
                for col in _scope(ct['categorical']):
                    df[col] = normalize_string_series(df[col])
                log.append("String dinormalisasi" + (f" (kolom: {', '.join(_scope(ct['categorical']))})" if target_cols else ""))
        ct = detect_column_types(df); nc = ct['numerical']
        quality = _compute_quality(df, nc)
        cache.set(_key('df'), df)
        cache.delete(_key('viz')); cache.delete(_key('viz_data'))
        cache.delete(_key('smart_id')); cache.delete(_key('smart_en'))
        return jsonify({'success': True, 'rows_after': int(len(df)), 'log': log,
                        'quality': quality, 'preview': get_preview(df, 10)})
    except Exception as e:
        logger.exception("Error clean"); return jsonify({'error': str(e)}), 500


@app.route('/clean/reset', methods=['POST'])
def clean_reset():
    if not _require_auth(): return jsonify({'error': 'Login dulu.'}), 401
    df_orig = cache.get(_key('df_original'))
    if df_orig is None:
        return jsonify({'error': 'Tidak ada data awal tersimpan.'}), 400
    try:
        df = df_orig.copy(deep=True)
        ct = detect_column_types(df); nc, cc = ct['numerical'], ct['categorical']
        quality = _compute_quality(df, nc)
        insights = ''
        try: insights = generate_insights(df, nc, cc)
        except: pass
        meta = {'total_rows': int(df.shape[0]), 'total_cols': int(df.shape[1]),
                'numeric_cols': int(len(nc)), 'categorical_cols': int(len(cc)),
                'has_datetime': len(ct['datetime']) > 0}
        cache.set(_key('df'), df)
        cache.delete(_key('viz')); cache.delete(_key('viz_data'))
        cache.delete(_key('smart_id')); cache.delete(_key('smart_en'))
        return jsonify({'success': True, 'rows_after': int(len(df)), 'quality': quality,
                        'preview': get_preview(df, 10), 'meta': meta,
                        'numeric_summary': compute_numerical_stats(df, nc),
                        'categorical_summary': compute_categorical_stats(df, cc),
                        'insights': insights,
                        'message': 'Data berhasil dikembalikan ke kondisi awal.'})
    except Exception as e:
        logger.exception("Error reset"); return jsonify({'error': str(e)}), 500


@app.route('/visualize')
def visualize():
    if not _require_auth(): return jsonify({'error': 'Login dulu.'}), 401
    df = cache.get(_key('df'))
    if df is None: return jsonify({'error': 'Upload file dulu.'}), 400
    cv = cache.get(_key('viz')); ci = cache.get(_key('viz_data'))
    if cv and ci: return jsonify({'charts': cv, 'interactive': ci})
    try:
        charts = cv or generate_all_charts(df)
        inter  = ci or generate_interactive_data(df)
        cache.set(_key('viz'), charts); cache.set(_key('viz_data'), inter)
        return jsonify({'charts': charts, 'interactive': inter})
    except Exception as e:
        logger.exception("Error visualize"); return jsonify({'error': 'Gagal generate chart.'}), 500


@app.route('/chart-recommendations')
def chart_recommendations():
    """Endpoint to get adaptive chart recommendations for current dataset."""
    if not _require_auth(): return jsonify({'error': 'Login dulu.'}), 401
    df = cache.get(_key('df'))
    if df is None: return jsonify({'error': 'Upload file dulu.'}), 400
    try:
        recs = get_column_chart_recommendations(df)
        return jsonify(recs)
    except Exception as e:
        logger.exception("Error chart-recs"); return jsonify({'error': 'Gagal.'}), 500


@app.route('/timeseries')
def timeseries():
    if not _require_auth(): return jsonify({'error': 'Login dulu.'}), 401
    df = cache.get(_key('df'))
    if df is None: return jsonify({'error': 'Upload file dulu.'}), 400
    try: return jsonify(analyze_timeseries(df))
    except Exception as e:
        logger.exception("Error timeseries"); return jsonify({'error': 'Gagal analisis time series.'}), 500


@app.route('/insights')
def insights():
    if not _require_auth(): return jsonify({'error': 'Login dulu.'}), 401
    df = cache.get(_key('df'))
    if df is None: return jsonify({'error': 'Upload file dulu.'}), 400
    lang = request.args.get('lang', 'id')
    ck   = _key(f'smart_{lang}')
    cached = cache.get(ck)
    if cached: return jsonify(cached)
    try:
        ct = detect_column_types(df)
        nc, cc, dt = ct['numerical'], ct['categorical'], ct['datetime']
        stats  = cache.get(_key('stats'))
        quality = stats.get('quality', {}) if stats else _compute_quality(df, nc)
        result = generate_smart_insights(df, nc, cc, dt_cols=dt, quality=quality, lang=lang)
        cache.set(ck, result)
        return jsonify(result)
    except Exception as e:
        logger.exception("Error insights"); return jsonify({'error': 'Gagal generate insights.'}), 500


@app.route('/insights/status')
def insights_status():
    """Tell frontend whether Claude API is configured."""
    has_key = bool(os.environ.get('ANTHROPIC_API_KEY', ''))
    return jsonify({'claude_available': has_key})


@app.route('/export/<fmt>')
def export(fmt):
    if not _require_auth(): return jsonify({'error': 'Login dulu.'}), 401
    df    = cache.get(_key('df'))
    stats = cache.get(_key('stats'))
    info  = cache.get(_key('info'))
    if df is None: return jsonify({'error': 'Upload file dulu.'}), 400
    lang = request.args.get('lang', 'id')
    try:
        if stats:
            ct = detect_column_types(df); nc, cc = ct['numerical'], ct['categorical']
            stats = dict(stats)
            stats['quality'] = _compute_quality(df, nc)
            stats['numeric_summary']     = compute_numerical_stats(df, nc)
            stats['categorical_summary'] = compute_categorical_stats(df, cc)
            stats['meta'] = dict(stats.get('meta', {}))
            stats['meta']['total_rows'] = int(len(df))
        if fmt == 'csv':
            return send_file(io.BytesIO(export_csv(df)), mimetype='text/csv',
                             as_attachment=True, download_name='dataset.csv')
        if fmt == 'excel':
            return send_file(io.BytesIO(export_excel(df, stats)),
                             mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             as_attachment=True, download_name='report.xlsx')
        if fmt in ('html', 'pdf', 'preview'):
            viz_charts = cache.get(_key('viz'))
            if not viz_charts:
                try: viz_charts = generate_all_charts(df); cache.set(_key('viz'), viz_charts)
                except: viz_charts = None
            smart = cache.get(_key(f'smart_{lang}'))
            if not smart:
                try:
                    ct = detect_column_types(df)
                    nc, cc, dt = ct['numerical'], ct['categorical'], ct['datetime']
                    quality = stats.get('quality', {}) if stats else {}
                    smart = generate_smart_insights(df, nc, cc, dt_cols=dt, quality=quality, lang=lang)
                    cache.set(_key(f'smart_{lang}'), smart)
                except: smart = None
            html_bytes = export_html(df, stats or {}, info, viz_charts, smart, lang=lang)
            if fmt == 'html':
                return send_file(io.BytesIO(html_bytes), mimetype='text/html',
                                 as_attachment=True, download_name='report.html')
            if fmt == 'preview':
                return Response(html_bytes, mimetype='text/html')
            data, mime, ext_out = export_pdf(df, stats or {}, info, viz_charts, smart, lang=lang)
            return send_file(io.BytesIO(data), mimetype=mime,
                             as_attachment=True, download_name=f'report{ext_out}')
        return jsonify({'error': 'Format tidak dikenali.'}), 400
    except Exception as e:
        logger.exception("Error export"); return jsonify({'error': 'Gagal export.'}), 500


@app.route('/filter', methods=['POST'])
def apply_filter():
    if not _require_auth(): return jsonify({'error': 'Login dulu.'}), 401
    df = cache.get(_key('df'))
    if df is None: return jsonify({'error': 'Upload file dulu.'}), 400
    data = request.json or {}; filters = data.get('filters', {})
    if not filters: return jsonify({'error': 'Tidak ada filter.'}), 400
    filtered = df.copy(); applied = []
    for col, val in filters.items():
        if col not in filtered.columns: return jsonify({'error': f"Kolom '{col}' tidak ditemukan."}), 400
        filtered = filtered[filtered[col].astype(str).str.lower() == str(val).lower()]
        applied.append(f"{col}={val}")
    return jsonify({'rows_after_filter': int(len(filtered)), 'filters_applied': applied,
                    'message': f'{len(filtered)} baris tersisa setelah filter: {", ".join(applied)}'})


@app.errorhandler(413)
def too_large(e): return jsonify({'error': 'File melebihi 50MB.'}), 413

@app.errorhandler(Exception)
def handle_error(e):
    logger.exception("Unhandled error"); return jsonify({'error': 'Terjadi kesalahan server.'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=8000, host='0.0.0.0')