"""
tests/test_stable_api.py
========================
Phase 1 — Regression tests for the frozen public API.

These tests guard against accidental breakage of:
  - load_data / clean_column / prepare_by_kpi_all_countries
  - Column contract: countryname | year | kpi | value
  - KPI_LABELS keys and facet_chart_by_country signature

Run with:  pytest tests/test_stable_api.py -v
"""

import pytest
import numpy as np
import pandas as pd

from sp_analysis.static_dashboard import (
    KPI_LABELS,
    STATUS_DOMAIN,
    STATUS_RANGE,
    clean_column,
    prepare_by_kpi_all_countries,
    facet_chart_by_country,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def raw_df() -> pd.DataFrame:
    """Minimal synthetic dataframe that mimics sp_data.csv structure."""
    return pd.DataFrame({
        'countryname': ['Alpha', 'Alpha', 'Beta', 'Beta', 'Gamma'],
        'year':        [2022,    2023,    2022,    2023,    2023  ],
        'SP':          ['SP1',   'SP1',   'SP2',   'SP2',   'SP1' ],
        'c1_visits':   ['100',   '200',   '150',   'n/a',   '300' ],
        'c2_user':     ['10',    '20',    '15',    '25',    '5'   ],
        'c13_staff':   ['5',     '6',     '7',     '8',     '4'   ],
    })


# ── KPI_LABELS ─────────────────────────────────────────────────────────────────

class TestKpiLabels:
    EXPECTED_KEYS = {
        'c1_visits', 'c2_user', 'c3_pdoDeliver_pid', 'c4_events',
        'c6_eAttendees', 'c8_allEvent', 'c10_pdoStored_pid',
        'c13_staff', 'c14_nfunds', 'c15_cstaff', 'c16_cfunds', 'c19_pub',
    }

    def test_all_keys_present(self):
        assert self.EXPECTED_KEYS == set(KPI_LABELS.keys()), \
            'KPI_LABELS keys changed — this is a breaking change!'

    def test_values_are_strings(self):
        for k, v in KPI_LABELS.items():
            assert isinstance(v, str), f'KPI_LABELS[{k!r}] must be a string'


# ── clean_column ───────────────────────────────────────────────────────────────

class TestCleanColumn:
    def test_coerces_to_numeric(self, raw_df):
        result = clean_column(raw_df, 'c1_visits')
        assert result['c1_visits'].dtype in (float, int, 'float64', 'int64')

    def test_non_numeric_becomes_nan(self, raw_df):
        result = clean_column(raw_df, 'c1_visits')
        assert pd.isna(result.loc[3, 'c1_visits']), \
            "String 'n/a' should become NaN"

    def test_does_not_mutate_input(self, raw_df):
        original_dtype = raw_df['c1_visits'].dtype
        clean_column(raw_df, 'c1_visits')
        assert raw_df['c1_visits'].dtype == original_dtype, \
            'clean_column must not mutate the input dataframe'


# ── prepare_by_kpi_all_countries ───────────────────────────────────────────────

class TestPrepareByKpiAllCountries:
    """Guards the canonical data contract: countryname | year | kpi | value"""

    def test_required_columns_present(self, raw_df):
        result = prepare_by_kpi_all_countries(raw_df, ['c1_visits'])
        assert set(result.columns) >= {'countryname', 'year', 'kpi', 'value'}, \
            'Canonical columns missing — breaking change!'

    def test_no_extra_ambiguous_column_renames(self, raw_df):
        result = prepare_by_kpi_all_countries(raw_df, ['c1_visits'])
        assert 'c1_visits' not in result.columns, \
            'Original column name should be renamed to "value"'

    def test_kpi_column_uses_kpi_labels_values(self, raw_df):
        result = prepare_by_kpi_all_countries(raw_df, ['c1_visits'])
        assert (result['kpi'] == KPI_LABELS['c1_visits']).all()

    def test_value_column_is_numeric(self, raw_df):
        result = prepare_by_kpi_all_countries(raw_df, ['c1_visits'])
        assert pd.api.types.is_numeric_dtype(result['value'])

    def test_nan_preserved_for_missing(self, raw_df):
        result = prepare_by_kpi_all_countries(raw_df, ['c1_visits'])
        beta_2023 = result[
            (result['countryname'] == 'Beta') & (result['year'] == 2023)
        ]['value']
        # Beta 2023 c1_visits was 'n/a' → NaN
        assert beta_2023.isna().all(), 'NaN must be preserved in value column'

    def test_multiple_kpis(self, raw_df):
        result = prepare_by_kpi_all_countries(raw_df, ['c1_visits', 'c2_user'])
        assert set(result['kpi'].unique()) == {'c1_visits', 'c2_user'}

    def test_aggregates_per_country_year(self, raw_df):
        # Two rows for Alpha+2022+c1_visits → should aggregate to one
        dup = pd.concat([raw_df, raw_df.iloc[[0]]], ignore_index=True)
        result = prepare_by_kpi_all_countries(dup, ['c1_visits'])
        alpha_2022 = result[
            (result['countryname'] == 'Alpha') & (result['year'] == 2022)
        ]
        assert len(alpha_2022) == 1, 'Should produce one row per (country, year, kpi)'

    def test_returns_dataframe(self, raw_df):
        result = prepare_by_kpi_all_countries(raw_df, ['c1_visits'])
        assert isinstance(result, pd.DataFrame)


# ── facet_chart_by_country ─────────────────────────────────────────────────────

class TestFacetChartByCountry:
    """Smoke-tests the chart function signature — does not assert rendering details."""

    def test_returns_altair_object(self, raw_df):
        import altair as alt
        long = prepare_by_kpi_all_countries(raw_df, ['c1_visits', 'c2_user'])
        chart = facet_chart_by_country(long, country='Alpha', title='Test')
        assert isinstance(chart, (alt.FacetChart, alt.Chart, alt.LayerChart))

    def test_accepts_columns_kwarg(self, raw_df):
        import altair as alt
        long = prepare_by_kpi_all_countries(raw_df, ['c1_visits'])
        chart = facet_chart_by_country(long, country='Alpha', title='T', columns=2)
        assert chart is not None

    def test_unknown_country_returns_chart(self, raw_df):
        """Empty data should not raise — Altair renders an empty chart gracefully."""
        long = prepare_by_kpi_all_countries(raw_df, ['c1_visits'])
        chart = facet_chart_by_country(long, country='Nonexistent', title='T')
        assert chart is not None
