import pandas as pd
import altair as alt

# def _theme():
#     return {
#         'config': {
#             'view': {
#                 'continuousWidth': 220,
#                 'continuousHeight': 160,
#             }
#         }
#     }

# alt.themes.register('sp_analysis', _theme)
# alt.themes.enable('sp_analysis')
# ─────────────────────────────────────────
# DATA
# ─────────────────────────────────────────

def load_data() -> pd.DataFrame:
    sheet_id = '1sREWbJdEYFjckWHcgAaUTnb6uQIuyM-bs-Un12ZmVaA'
    gid = '598429315'
    url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}'
    df = pd.read_csv(url)
    df.dropna(subset=['c1_visits'], inplace=True)
    return df


# ─────────────────────────────────────────
# TRANSFORMS
# ─────────────────────────────────────────

def clean_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Coerce column to numeric and drop NaN rows."""
    df = df.copy()
    df[col] = pd.to_numeric(df[col], errors='coerce')
    return df.dropna(subset=[col])


def aggregate(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Aggregate by country + year, summing the target column."""
    return df.groupby(['countryname', 'year'])[col].sum().reset_index()


def pct_change_from_first(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Add a % change column relative to each country's first year."""
    df = df.copy()
    first = df.groupby('countryname')[col].transform('first')
    df[f'{col}_pct'] = ((df[col] - first) / first) * 100
    return df


def prepare(df: pd.DataFrame, col: str, pct: bool = False) -> pd.DataFrame:
    """Full pipeline: clean → aggregate → optionally compute % change."""
    agg = aggregate(clean_column(df, col), col)
    if pct:
        agg = pct_change_from_first(agg, col)
    return agg


# ─────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────

def facet_chart(
    data: pd.DataFrame,
    col: str,
    y_title: str,
    title: str,
    pct: bool = False,
) -> alt.FacetChart:
    """
    Steelblue line + dot facet chart, one panel per country.

    Parameters
    ----------
    data    : aggregated DataFrame
    col     : column to plot on Y axis
    y_title : Y-axis label
    title   : top-level chart title
    pct     : if True, format Y labels as percentages
    """
    axis_kwargs = dict(tickCount=3, grid=False)
    if pct:
        axis_kwargs['labelExpr'] = "datum.value + '%'"

    encode = dict(
        x=alt.X('year:O', title=None),
        y=alt.Y(f'{col}:Q', title=y_title, axis=alt.Axis(**axis_kwargs)),
    )

    line = alt.Chart(data).mark_line(color='steelblue').encode(**encode)
    dots = alt.Chart(data).mark_point(filled=True, size=50, color='steelblue').encode(**encode)

    return (
        (line + dots)
        .properties(title=title, width=200)
        .facet(
            facet=alt.Facet(
                'countryname:N',
                header=alt.Header(titleOrient='bottom', labelOrient='bottom'),
                title='Country Name',
            ),
            columns=5,
        )
        .resolve_scale(y='independent')
        .resolve_axis(x='independent')
        .properties(
            title=alt.TitleParams(
                text=title, fontSize=16, fontWeight='bold', anchor='middle'
            ),
            # autosize=alt.AutoSizeParams(type='fit-x')
        )
    )
