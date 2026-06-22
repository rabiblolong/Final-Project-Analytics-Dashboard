import pandas as pd, numpy as np

def compute_categorical_stats(df, cat_cols):
    if not cat_cols: return {}
    metrics = ['unique','top','freq','missing_count','missing_pct']
    result  = {m:{} for m in metrics}
    desc    = df[cat_cols].astype(str).describe()
    for col in cat_cols:
        miss = int(df[col].isna().sum())
        for m in metrics:
            if m in desc.index:
                v = desc.loc[m,col]
                result[m][col] = int(v) if m in ['unique','freq'] else str(v)
            elif m=='missing_count': result[m][col]=miss
            elif m=='missing_pct':   result[m][col]=round(miss/len(df)*100,2) if len(df)>0 else 0.0
    return result