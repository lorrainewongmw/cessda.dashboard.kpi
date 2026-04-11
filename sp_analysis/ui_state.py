"""
kpi_engine/ui_state.py
======================
Layer 2 — Reactive UI state for the NiceGUI dashboard.

Centralises all user-driven selections so the dashboard has a single source
of truth.  Any component that changes the state calls ``notify_listeners``
and every registered callback is invoked.

No NiceGUI-specific imports here — this module is framework-agnostic so it
can be tested in isolation and reused in other UIs if needed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .registry import OBJECTIVES, KPI_IDS, get_kpis_for_objective


# ── State dataclass ────────────────────────────────────────────────────────────

@dataclass
class DashboardState:
    """All user-controllable filters for the KPI dashboard.

    Attributes
    ----------
    selected_countries:
        Set of country names currently selected.  Empty set means "all".
    selected_objective:
        Thematic objective filter.  ``'All'`` means no filtering.
    year_range:
        Inclusive (start_year, end_year) window.
    agg_mode:
        Aggregation mode across countries: ``'sum'`` or ``'median'``.
    reference_year:
        Year shown in the stats table.  ``None`` → latest year with data.

    Internal
    --------
    _listeners:
        Registered callbacks invoked on every state change.
    """

    selected_countries: list[str] = field(default_factory=list)
    selected_objective: str = 'All'
    year_range: tuple[int, int] = (2018, 2025)
    agg_mode: str = 'sum'
    reference_year: int | None = None

    _listeners: list[Callable[[], None]] = field(default_factory=list, repr=False)

    # ── Derived accessors ──────────────────────────────────────────────────

    @property
    def active_kpis(self) -> list[str]:
        """KPI ids matching the current objective filter."""
        return get_kpis_for_objective(self.selected_objective)

    @property
    def countries_filter(self) -> list[str] | None:
        """Returns the country list or None (= "all") for compute helpers."""
        return self.selected_countries if self.selected_countries else None

    # ── Mutation helpers ───────────────────────────────────────────────────

    def set_countries(self, countries: list[str]) -> None:
        self.selected_countries = list(countries)
        self._notify()

    def set_objective(self, objective: str) -> None:
        self.selected_objective = objective
        self._notify()

    def set_year_range(self, start: int, end: int) -> None:
        self.year_range = (start, end)
        self._notify()

    def set_agg_mode(self, mode: str) -> None:
        if mode not in ('sum', 'median'):
            raise ValueError(f"agg_mode must be 'sum' or 'median', got {mode!r}")
        self.agg_mode = mode
        self._notify()

    def set_reference_year(self, year: int | None) -> None:
        self.reference_year = year
        self._notify()

    def reset(self) -> None:
        """Restore all filters to their defaults."""
        self.selected_countries = []
        self.selected_objective = 'All'
        self.year_range = (2018, 2025)
        self.agg_mode = 'sum'
        self.reference_year = None
        self._notify()

    # ── Listener registration ──────────────────────────────────────────────

    def on_change(self, callback: Callable[[], None]) -> None:
        """Register *callback* to be called whenever state changes."""
        self._listeners.append(callback)

    def _notify(self) -> None:
        for cb in self._listeners:
            cb()
