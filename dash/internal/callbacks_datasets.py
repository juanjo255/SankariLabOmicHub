"""Callbacks for the Data Sources tab (curated per-species dataset manifest)."""

from __future__ import annotations

import logging

import dash_bootstrap_components as dbc
from dash import Input, Output, State, dash_table, html, no_update

from .apis import get_datasets_api


def register(app, *, logger: logging.Logger) -> None:
    """Register Data Sources callbacks."""

    @app.callback(
        Output("datasets-content", "children"),
        Input("main-tabs", "value"),
        State("current-species-store", "data"),
    )
    def update_datasets_content(active_tab, species_key):
        if active_tab != "tab-data-sources":
            return no_update

        if not species_key:
            return dbc.Alert(
                "Select a species to see its data sources.", color="info", className="mt-4"
            )

        current_datasets_api = get_datasets_api(species_key)
        if current_datasets_api is None or not current_datasets_api.is_available():
            logger.info("No datasets manifest available for species_key=%s", species_key)
            return dbc.Alert(
                "No curated dataset manifest is available for this species yet.",
                color="info",
                className="mt-4",
            )

        records = current_datasets_api.get_records()
        columns = current_datasets_api.get_columns()

        table = dash_table.DataTable(
            id="datasets-table",
            data=records,
            columns=columns,
            sort_action="native",
            filter_action="native",
            page_size=15,
            style_table={"overflowX": "auto"},
            style_cell={
                "textAlign": "left",
                "padding": "8px",
                "fontFamily": "inherit",
                "fontSize": "0.9rem",
                "whiteSpace": "normal",
                "height": "auto",
            },
            style_header={"fontWeight": "bold", "backgroundColor": "#f8f9fa"},
            style_cell_conditional=[
                {"if": {"column_id": "description"}, "minWidth": "320px"},
            ],
        )

        return html.Div(
            [
                html.H4("Data Sources", className="mb-3"),
                html.P(
                    "Omics datasets produced and/or processed at Sankari Lab."
                    "Use the filter row below the headers to search, click a header to sort.",
                    className="text-muted",
                ),
                table,
            ]
        )
