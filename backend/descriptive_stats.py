import pandas as pd, numpy as np

def compute_numerical_stats(df, num_cols):
    if not num_cols: return {}
    metrics = ['count','mean','std','min','50%','max','mode','skewness','missing_count','missing_pct']
    result  = {m:{} for m in metrics}
    base    = df[num_cols].describe()
    for col in num_cols:
        miss = int(df[col].isna().sum())
        for m in metrics:
            if m in base.index:
                v = base.loc[m,col]
                result[m][col] = float(v) if not pd.isna(v) else 0.0
            elif m=='mode':
                try: result[m][col]=float(df[col].mode()[0])
                except: result[m][col]=0.0
            elif m=='skewness':
                try:
                    s = float(df[col].dropna().skew())
                    result[m][col] = s if not pd.isna(s) else 0.0
                except:
                    result[m][col] = 0.0
            elif m=='missing_count': result[m][col]=miss
            elif m=='missing_pct':   result[m][col]=round(miss/len(df)*100,2) if len(df)>0 else 0.0
    return result