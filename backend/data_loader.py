import pandas as pd
import numpy as np
import json
import io
import chardet
import logging
from backend.data_cleaning.cleaning import clean_dataset

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {'.csv', '.xlsx', '.xls', '.txt', '.tsv', '.json'}

def detect_encoding(b):
    r = chardet.detect(b)
    return r.get('encoding', 'utf-8') or 'utf-8'

def detect_delimiter(s):
    d = [',', ';', '\t', '|', ' ']
    c = {x: s.count(x) for x in d}
    return max(c, key=c.get)

def load_file(fs):
    fname = fs.filename.strip()
    ext = ('.' + fname.rsplit('.', 1)[-1].lower()) if '.' in fname else ''
    fb = fs.read()
    size = len(fb)

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Format '{ext}' tidak didukung.")

    try:
        if ext in ('.xlsx', '.xls'):
            engine = 'openpyxl' if ext == '.xlsx' else 'xlrd'
            df = pd.read_excel(io.BytesIO(fb), engine=engine)

        elif ext == '.csv':
            enc = detect_encoding(fb)
            delim = detect_delimiter(fb[:2048].decode(enc, errors='replace'))
            df = pd.read_csv(io.BytesIO(fb), sep=delim, encoding=enc, on_bad_lines='skip', low_memory=False)

        elif ext == '.tsv':
            enc = detect_encoding(fb)
            df = pd.read_csv(io.BytesIO(fb), sep='\t', encoding=enc, on_bad_lines='skip', low_memory=False)

        elif ext == '.txt':
            enc = detect_encoding(fb)
            delim = detect_delimiter(fb[:2048].decode(enc, errors='replace'))
            try:
                df = pd.read_csv(io.BytesIO(fb), sep=delim, encoding=enc, on_bad_lines='skip', low_memory=False)
            except:
                df = pd.read_csv(io.BytesIO(fb), sep=r'\s+', encoding=enc, on_bad_lines='skip', engine='python', low_memory=False)

        elif ext == '.json':
            enc = detect_encoding(fb)
            p = json.loads(fb.decode(enc, errors='replace'))
            if isinstance(p, list):
                df = pd.DataFrame(p)
            elif isinstance(p, dict):
                df = pd.DataFrame.from_dict(p)
            else:
                df = None

        if df is None or df.empty:
            raise ValueError("File tidak mengandung data.")

        # Paksa salin data baru ke memori sebelum modifikasi nama kolom
        df = df.copy(deep=True)
        df.columns = [str(c).strip().upper() for c in df.columns]

        # Jalankan fungsi pembersihan data yang sudah diperbaiki
        df, cleaning_info = clean_dataset(df)

        return df, {
            'filename': fname,
            'extension': ext.upper().replace('.', ''),
            'size_kb': round(size / 1024, 1),
            'cleaning': cleaning_info
        }

    except Exception as e:
        logger.exception(f"Error loading {fname}")
        raise ValueError(f"Gagal memproses file: {str(e)}")