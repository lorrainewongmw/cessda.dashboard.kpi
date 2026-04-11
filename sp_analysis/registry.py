"""
kpi_engine/registry.py
======================
Layer 2 — Additive KPI Registry.

Enriches KPI_LABELS with structured metadata (objectives, units, aggregations).
🔒 KPI ids MUST match existing KPI_LABELS keys — never rename them.
   KPI_LABELS is preserved for legacy callers.
"""

from dataclasses import dataclass, field
from typing import Literal

# ── Registry entry ─────────────────────────────────────────────────────────────

AggMode = Literal['sum', 'median']


@dataclass(frozen=True)
class KPIEntry:
    id: str                            # must match KPI_LABELS key
    label: str                         # human-readable display name
    objective: str                     # thematic grouping
    unit: str                          # e.g. "count", "FTE", "EUR"
    aggregations: list[AggMode] = field(default_factory=lambda: ['sum', 'median'])
    description: str = ''


# ── Registry definition ────────────────────────────────────────────────────────

_ENTRIES: list[KPIEntry] = [
    # ── Access & Use ───────────────────────────────────────────────────────
    KPIEntry(
        id='c1_visits',
        label='Total visits',
        objective='Access & Use',
        unit='count',
        aggregations=['sum', 'median'],
        description='Total number of visits to the research infrastructure.',
    ),
    KPIEntry(
        id='c2_user',
        label='Number of users',
        objective='Access & Use',
        unit='count',
        aggregations=['sum', 'median'],
        description='Number of distinct users granted access.',
    ),
    KPIEntry(
        id='c3_pdoDeliver_pid',
        label='Data objects delivered (PID)',
        objective='Access & Use',
        unit='count',
        aggregations=['sum', 'median'],
        description='Physical/digital objects delivered with persistent identifier.',
    ),
    # ── Scientific Output ──────────────────────────────────────────────────
    KPIEntry(
        id='c4_events',
        label='Training events',
        objective='Scientific Excellence',
        unit='count',
        aggregations=['sum', 'median'],
        description='Number of training and educational events organised.',
    ),
    KPIEntry(
        id='c6_eAttendees',
        label='Event attendees',
        objective='Scientific Excellence',
        unit='count',
        aggregations=['sum', 'median'],
        description='Total number of attendees across all events.',
    ),
    KPIEntry(
        id='c8_allEvent',
        label='All events',
        objective='Scientific Excellence',
        unit='count',
        aggregations=['sum', 'median'],
        description='All events including conferences, workshops, and outreach.',
    ),
    KPIEntry(
        id='c19_pub',
        label='Publications',
        objective='Scientific Excellence',
        unit='count',
        aggregations=['sum', 'median'],
        description='Peer-reviewed publications enabled by the infrastructure.',
    ),
    # ── Data Stewardship ───────────────────────────────────────────────────
    KPIEntry(
        id='c10_pdoStored_pid',
        label='Data objects stored (PID)',
        objective='Data Stewardship',
        unit='count',
        aggregations=['sum', 'median'],
        description='Physical/digital objects stored with persistent identifier.',
    ),
    # ── Human Capital ──────────────────────────────────────────────────────
    KPIEntry(
        id='c13_staff',
        label='Total staff (FTE)',
        objective='Human Capital',
        unit='FTE',
        aggregations=['sum', 'median'],
        description='Total full-time equivalent staff employed.',
    ),
    KPIEntry(
        id='c15_cstaff',
        label='Scientific staff (FTE)',
        objective='Human Capital',
        unit='FTE',
        aggregations=['sum', 'median'],
        description='Scientific and technical staff in FTE.',
    ),
    # ── Finance ────────────────────────────────────────────────────────────
    KPIEntry(
        id='c14_nfunds',
        label='National funding (EUR)',
        objective='Finance',
        unit='EUR',
        aggregations=['sum', 'median'],
        description='Total national public funding received.',
    ),
    KPIEntry(
        id='c16_cfunds',
        label='Competitive funding (EUR)',
        objective='Finance',
        unit='EUR',
        aggregations=['sum', 'median'],
        description='Funding obtained through competitive calls.',
    ),
]

# ── Public accessors ───────────────────────────────────────────────────────────

# Fast lookup dict: id → KPIEntry
KPI_REGISTRY: dict[str, KPIEntry] = {e.id: e for e in _ENTRIES}

# All distinct objectives, preserving insertion order
OBJECTIVES: list[str] = list(dict.fromkeys(e.objective for e in _ENTRIES))

# All KPI ids (same order as _ENTRIES)
KPI_IDS: list[str] = [e.id for e in _ENTRIES]


def get_kpis_for_objective(objective: str | None) -> list[str]:
    """Return KPI ids that belong to *objective*.

    If *objective* is None or 'All', return all KPI ids.
    """
    if not objective or objective == 'All':
        return KPI_IDS
    return [e.id for e in _ENTRIES if e.objective == objective]


def get_entry(kpi_id: str) -> KPIEntry | None:
    """Return the KPIEntry for *kpi_id*, or None if not registered."""
    return KPI_REGISTRY.get(kpi_id)
