"""Vectorized date parsing and period assignment for visualization scripts."""

import pandas as pd
import numpy as np


def parse_dates_vectorized(ser):
    """Parse dates with common formats (vectorized)."""
    out = pd.to_datetime(ser, format='%d.%m.%Y %H:%M', errors='coerce')
    if out.isna().any():
        out = out.fillna(pd.to_datetime(ser, format='%d.%m.%Y', errors='coerce'))
    if out.isna().any():
        out = out.fillna(pd.to_datetime(ser, dayfirst=True, errors='coerce'))
    return out


def assign_period_vectorized(dates):
    """Assign period labels from dates (vectorized)."""
    d = pd.to_datetime(dates)
    pre = d < pd.Timestamp('2014-01-01')
    post = (d >= pd.Timestamp('2014-01-01')) & (d < pd.Timestamp('2017-02-01'))
    covid = (d >= pd.Timestamp('2017-02-01')) & (d < pd.Timestamp('2022-02-24'))
    war = d >= pd.Timestamp('2022-02-24')
    out = np.full(len(d), None, dtype=object)
    out[pre] = 'Pre-Crimea'
    out[post] = 'Post-Crimea'
    out[covid] = 'COVID'
    out[war] = 'War'
    return out
