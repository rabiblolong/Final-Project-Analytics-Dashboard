import pandas as pd
import numpy as np

def detect_column_types(df):
    """Perbaikan: Lebih aman + copy independen untuk deteksi datetime"""
    if df is None or df.empty:
        return {'numerical': [], 'categorical': [], 'datetime': []}
    
    try:
        # Selalu gunakan salinan independen di dalam fungsi ini
        df_local = df.copy()
        
        num = df_local.select_dtypes(include=[np.number]).columns.tolist()
        cat = df_local.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()
        dt  = df_local.select_dtypes(include=['datetime64']).columns.tolist()

        # Cek kolom yang bisa dijadikan datetime
        for col in cat[:]:
            try:
                # Perbaikan: Buat copy dari series agar tidak mengunci array utama
                series_copy = df_local[col].copy()
                p = pd.to_datetime(series_copy, errors='coerce')
                
                if p.notna().sum() / len(df_local) > 0.6:  # threshold lebih longgar
                    dt.append(col)
                    cat.remove(col)
            except:
                pass

        return {
            'numerical': num,
            'categorical': cat,
            'datetime': dt
        }
    except Exception as e:
        print(f"Warning: detect_column_types gagal: {e}")
        # Fallback aman
        return {
            'numerical': df.select_dtypes(include=[np.number]).columns.tolist(),
            'categorical': df.select_dtypes(exclude=[np.number]).columns.tolist(),
            'datetime': []
        }

def clean_for_json(df):
    df = df.copy(deep=True)
    for col in df.columns:
        # Perbaikan: Konversi tipe data object secara aman sebelum fillna
        if df[col].dtype in ['int64', 'float64']:
            df[col] = df[col].fillna(0)
        else:
            df[col] = df[col].astype(object).fillna("")
    return df

def get_preview(df, n=5):
    return clean_for_json(df.head(n)).to_dict(orient='records')