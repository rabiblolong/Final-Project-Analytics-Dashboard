import numpy as np
import pandas as pd

COMMON_CATEGORY_MAP = {
    r'^(?:m|male|laki[-\s]?laki|pria)$': 'male',
    r'^(?:f|female|perempuan|wanita)$': 'female',
    r'^(?:ya|yes|y)$': 'yes',
    r'^(?:tidak|no|n)$': 'no'
}

INVALID_CATEGORY_PATTERN = r'^(?:nan|none|null|undefined|unknown|unk|n/?a|na|x|\?+|[-]+|999+|)$'


def normalize_string_series(series: pd.Series) -> pd.Series:
    cleaned = series.astype(object).str.strip().str.normalize('NFKC')
    cleaned = cleaned.where(cleaned.isna(), cleaned.str.casefold())
    cleaned = cleaned.where(cleaned.isna(), cleaned.str.replace(r'\s+', ' ', regex=True))
    cleaned = cleaned.where(cleaned.isna(), cleaned.str.replace(r'^[\-\._\s]+|[\-\._\s]+$', '', regex=True))
    cleaned = cleaned.replace([INVALID_CATEGORY_PATTERN], np.nan, regex=True)
    cleaned = cleaned.replace(COMMON_CATEGORY_MAP, regex=True)
    cleaned = cleaned.replace([INVALID_CATEGORY_PATTERN], np.nan, regex=True)
    return cleaned


def clean_dataset(df: pd.DataFrame):
    df = df.copy(deep=True)
    initial_len = len(df)
    df = df.drop_duplicates().copy(deep=True)

    for col in df.select_dtypes(include=['object', 'category']).columns:
        df[col] = normalize_string_series(df[col])

    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.drop_duplicates().copy(deep=True)
    duplicates_removed = int(initial_len - len(df))

    missing = df.isnull().sum()
    cleaning_info = {
        'duplicates_removed': duplicates_removed,
        'total_missing': int(missing.sum()),
        'missing_per_column': {k: int(v) for k, v in missing[missing > 0].items()}
    }
    return df, cleaning_info
