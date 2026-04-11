"""
dashboard.py
============
ESFRI KPI Dashboard — NiceGUI entry point.

Run:
    python dashboard.py

Layout:
    ┌──────────────┬───────────────────────────────────────────┐
    │   Sidebar    │            KPI Table                      │
    │              │  KPI name │ Sum │ Median │ Trend          │
    │  Objectives  │  ─────────┼─────┼────────┼────────        │
    │  Countries   │  ...                                      │
    │  Year range  │                                           │
    │  Agg mode    │                                           │
    └──────────────┴───────────────────────────────────────────┘
"""

from __future__ import annotations

import pandas as pd
from nicegui import ui

from sp_analysis import (
    load_data,
    prepare_by_kpi_all_countries,
    KPI_IDS,
    OBJECTIVES,
    get_entry,
    DashboardState,
    compute_dashboard_data,
    build_sparkline,
)

# ── Bootstrap data ─────────────────────────────────────────────────────────────

raw = load_data()
long_df: pd.DataFrame = prepare_by_kpi_all_countries(raw, KPI_IDS)

ALL_COUNTRIES: list[str] = sorted(long_df['countryname'].dropna().unique().tolist())
ALL_YEARS: list[int] = sorted(long_df['year'].dropna().unique().tolist())
YEAR_MIN, YEAR_MAX = min(ALL_YEARS), max(ALL_YEARS)

state = DashboardState(year_range=(YEAR_MIN, YEAR_MAX))

# ── Helpers ────────────────────────────────────────────────────────────────────

def _fmt_number(v: float | None) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return '—'
    return f'{v:,.0f}'


def _recompute() -> dict:
    return compute_dashboard_data(
        long_df,
        countries=state.countries_filter,
        kpis=state.active_kpis,
        year_range=state.year_range,
        agg_mode=state.agg_mode,
        reference_year=state.reference_year,
    )


# ── UI ─────────────────────────────────────────────────────────────────────────

@ui.page('/')
def main_page():
    # ── Page-level style ───────────────────────────────────────────────────
    ui.add_head_html("""
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
      body { font-family: 'IBM Plex Sans', sans-serif; background: #f8fafc; }
      .sidebar { background: #ffffff; border-right: 1px solid #e2e8f0; min-height: 100vh; }
      .kpi-row:hover { background: #f1f5f9 !important; }
      .kpi-label { font-weight: 500; color: #1e293b; }
      .stat-cell { font-variant-numeric: tabular-nums; color: #334155; }
      .objective-chip { border-radius: 999px; padding: 2px 10px; font-size: 0.78rem; cursor: pointer; }
      .chip-active { background: #2563eb; color: #fff; }
      .chip-inactive { background: #e2e8f0; color: #475569; }
      .section-header { font-size: 0.7rem; font-weight: 600; letter-spacing: .08em;
                        text-transform: uppercase; color: #94a3b8; margin-bottom: 4px; }
      .dashboard-title { font-size: 1.4rem; font-weight: 600; color: #0f172a; }
      .dashboard-sub   { font-size: 0.85rem; color: #64748b; }
    </style>
    """)

    result = _recompute()

    # ── Layout: sidebar + main ─────────────────────────────────────────────
    with ui.row().classes('w-full gap-0'):

        # ── Sidebar ────────────────────────────────────────────────────────
        with ui.column().classes('sidebar w-64 p-5 gap-4 flex-shrink-0'):
            ui.label('ESFRI KPIs').classes('dashboard-title')
            ui.label('Research Infrastructure Monitor').classes('dashboard-sub')

            ui.separator()

            # Objective filter
            with ui.column().classes('gap-2'):
                ui.label('Objective').classes('section-header')

                objective_buttons: dict[str, ui.label] = {}

                def make_objective_handler(obj: str):
                    def handler():
                        state.set_objective(obj)
                        for o, btn in objective_buttons.items():
                            btn.classes(
                                'chip-active' if o == state.selected_objective else 'chip-inactive',
                                remove='chip-inactive' if o == state.selected_objective else 'chip-active',
                            )
                        refresh_table()
                    return handler

                for obj in ['All'] + OBJECTIVES:
                    is_active = obj == state.selected_objective
                    lbl = (
                        ui.label(obj)
                        .classes(f'objective-chip {"chip-active" if is_active else "chip-inactive"}')
                        .on('click', make_objective_handler(obj))
                    )
                    objective_buttons[obj] = lbl

            ui.separator()

            # Country selector
            with ui.column().classes('gap-2'):
                ui.label('Countries').classes('section-header')
                country_select = (
                    ui.select(
                        options=ALL_COUNTRIES,
                        multiple=True,
                        label='Filter countries',
                        value=[],
                    )
                    .classes('w-full')
                    .props('outlined dense use-chips')
                )

                def on_country_change():
                    state.set_countries(country_select.value or [])
                    refresh_table()

                country_select.on('update:model-value', on_country_change)

            ui.separator()

            # Year range
            with ui.column().classes('gap-2'):
                ui.label('Year range').classes('section-header')
                with ui.row().classes('gap-2 items-center'):
                    year_start = (
                        ui.number(
                            label='From', value=YEAR_MIN,
                            min=YEAR_MIN, max=YEAR_MAX, step=1,
                        )
                        .classes('w-24')
                        .props('outlined dense')
                    )
                    ui.label('–').classes('text-slate-400')
                    year_end = (
                        ui.number(
                            label='To', value=YEAR_MAX,
                            min=YEAR_MIN, max=YEAR_MAX, step=1,
                        )
                        .classes('w-24')
                        .props('outlined dense')
                    )

                def on_year_change(_e=None):
                    try:
                        s = int(year_start.value)
                        e = int(year_end.value)
                        if s <= e:
                            state.set_year_range(s, e)
                            refresh_table()
                    except (TypeError, ValueError):
                        pass

                year_start.on('update:model-value', on_year_change)
                year_end.on('update:model-value', on_year_change)

            ui.separator()

            # Aggregation mode
            with ui.column().classes('gap-2'):
                ui.label('Aggregation').classes('section-header')
                agg_toggle = ui.toggle(
                    options={'sum': 'Sum', 'median': 'Median'},
                    value=state.agg_mode,
                ).props('dense')

                def on_agg_change():
                    state.set_agg_mode(agg_toggle.value)
                    refresh_table()

                agg_toggle.on('update:model-value', on_agg_change)

            ui.separator()

            # Reset
            def on_reset():
                state.reset()
                country_select.set_value([])
                year_start.set_value(YEAR_MIN)
                year_end.set_value(YEAR_MAX)
                agg_toggle.set_value('sum')
                for o, btn in objective_buttons.items():
                    btn.classes(
                        'chip-active' if o == 'All' else 'chip-inactive',
                        remove='chip-inactive' if o == 'All' else 'chip-active',
                    )
                refresh_table()

            ui.button('Reset filters', on_click=on_reset).props('flat dense').classes('text-slate-500')

        # ── Main content ───────────────────────────────────────────────────
        with ui.column().classes('flex-1 p-6 gap-4'):

            # Top-bar info
            with ui.row().classes('items-center gap-4 mb-2'):
                reference_year_label = ui.label('').classes('text-slate-500 text-sm')

            # KPI Table
            table_container = ui.column().classes('w-full gap-0')

            def build_table_header():
                with ui.row().classes('w-full px-4 py-2 bg-slate-100 rounded-t gap-0'):
                    ui.label('KPI').classes('section-header flex-1')
                    ui.label('Sum').classes('section-header w-28 text-right')
                    ui.label('Median').classes('section-header w-28 text-right')
                    ui.label('Countries').classes('section-header w-20 text-right')
                    ui.label('Trend').classes('section-header w-32 text-right')

            def refresh_table():
                nonlocal result
                table_container.clear()
                result = _recompute()
                stats_df: pd.DataFrame = result['stats']
                ts_df: pd.DataFrame = result['time_series']

                ref_year = (
                    state.reference_year
                    if state.reference_year
                    else (int(stats_df['year'].iloc[0]) if not stats_df.empty else '—')
                )
                reference_year_label.set_text(f'Stats for year: {ref_year}')

                with table_container:
                    build_table_header()

                    kpis_to_show = state.active_kpis
                    stats_index = (
                        stats_df.set_index('kpi')
                        if not stats_df.empty
                        else pd.DataFrame(columns=['kpi', 'sum', 'median', 'n_countries']).set_index('kpi')
                    )

                    for kpi_id in kpis_to_show:
                        entry = get_entry(kpi_id)
                        label_text = entry.label if entry else kpi_id
                        unit_text  = entry.unit  if entry else ''

                        row_stats = stats_index.loc[kpi_id] if kpi_id in stats_index.index else None
                        sum_val    = row_stats['sum']        if row_stats is not None else None
                        median_val = row_stats['median']     if row_stats is not None else None
                        n_val      = row_stats['n_countries'] if row_stats is not None else None

                        with ui.row().classes('kpi-row w-full px-4 py-3 border-b border-slate-100 items-center gap-0'):
                            with ui.column().classes('flex-1 gap-0'):
                                ui.label(label_text).classes('kpi-label')
                                if entry and entry.description:
                                    ui.label(f'{unit_text}').classes('text-xs text-slate-400')

                            ui.label(_fmt_number(sum_val)).classes('stat-cell w-28 text-right')
                            ui.label(_fmt_number(median_val)).classes('stat-cell w-28 text-right')
                            ui.label(_fmt_number(n_val)).classes('stat-cell w-20 text-right text-slate-400')

                            # Sparkline
                            with ui.element('div').classes('w-32 flex justify-end'):
                                kpi_ts = ts_df[ts_df['kpi'] == kpi_id]
                                if not kpi_ts.dropna(subset=['value']).empty:
                                    spark = build_sparkline(ts_df, kpi_id, width=120, height=36)
                                    ui.altair(spark).classes('w-32')
                                else:
                                    ui.label('No data').classes('text-xs text-slate-300')

            # Initial render
            with table_container:
                build_table_header()

            reference_year_label.set_text(
                f"Stats for year: {int(result['stats']['year'].iloc[0]) if not result['stats'].empty else '—'}"
            )
            refresh_table()


ui.run(title='ESFRI KPI Dashboard', port=8888, reload=False)
