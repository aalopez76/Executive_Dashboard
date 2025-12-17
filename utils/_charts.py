"""
utils/_charts.py

Contains custom components and charts used inside the dashboard.
Adaptado del demo de Vizro para Classic Models Sales Analytics.

Cambios:
- bar(): agregación flexible (sum/mean/count/nunique)
- area_sales_trend(): serie temporal real por mes
- pie_abc_sales(): pie para ABC
- choropleth_world(): mapa por país (Plotly country names)
- choropleth(): wrapper compatible (SIN colorbar, mapa grande y vista global estable)
"""

from __future__ import annotations

from typing import List, Optional, Literal

import pandas as pd
import plotly.graph_objects as go
import vizro.plotly.express as px
from vizro.models.types import capture

AggFunc = Literal["sum", "mean", "count", "nunique"]

PRIMARY_BLUE = "#1A85FF"


# ---------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------
def _apply_dark_layout(fig: go.Figure, title: Optional[str] = None, height: int = 340) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        title=title,
        height=height,
        margin={"l": 20, "r": 20, "t": 50 if title else 20, "b": 20},
        legend={"orientation": "h", "y": -0.2},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    return fig


def _apply_world_geos(fig: go.Figure) -> go.Figure:
    """
    Fuerza vista global estable (evita recortes raros y mantiene LatAm visible).
    Nota: NO usamos fitbounds="locations" para que no “reencuadre” según países presentes.
    """
    fig.update_geos(
        showframe=False,
        showcoastlines=False,
        projection_type="natural earth",
        scope="world",
        bgcolor="rgba(0,0,0,0)",
        # mundo completo
        lonaxis=dict(range=[-180, 180]),
        lataxis=dict(range=[-90, 90]),
        # centro suave hacia LatAm (opcional pero ayuda visualmente)
        center=dict(lat=-10, lon=-30),
    )

    # Asegura que geo ocupe todo el lienzo disponible
    fig.update_layout(geo=dict(domain=dict(x=[0, 1], y=[0, 1])))

    return fig


# ---------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------
@capture("graph")
def bar(
    x: str,
    y: str,
    data_frame: pd.DataFrame,
    agg: str = "count",
    top_n: int = 15,
    custom_data: Optional[List[str]] = None,
):
    df = data_frame.copy()

    if agg == "count":
        df_agg = (
            df.groupby(y, dropna=False)
            .agg({x: "count"})
            .rename(columns={x: "value"})
            .reset_index()
        )
    else:
        df_agg = (
            df.groupby(y, dropna=False)
            .agg({x: agg})
            .rename(columns={x: "value"})
            .reset_index()
        )

    df_agg = df_agg.sort_values("value", ascending=False).head(top_n)

    fig = px.bar(
        data_frame=df_agg,
        x="value",
        y=y,
        orientation="h",
        text="value",
        color_discrete_sequence=[PRIMARY_BLUE],
        custom_data=custom_data,
    )

    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
    fig.update_layout(
        showlegend=False,
        margin=dict(l=16, r=16, t=8, b=16),
        xaxis_title=None,
        yaxis_title=None,
        yaxis=dict(autorange="reversed"),
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


@capture("graph")
def area_sales_trend(x: str, y: str, data_frame: pd.DataFrame):
    df = data_frame.copy()

    if x in df.columns:
        df["__date"] = pd.to_datetime(df[x] + "-01", errors="coerce")
        df = df.dropna(subset=["__date"]).sort_values("__date")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["__date"],
            y=df[y],
            mode="lines",
            fill="tozeroy",
            name="Sales",
        )
    )

    fig.update_layout(
        margin=dict(l=16, r=16, t=8, b=16),
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


@capture("graph")
def area(
    data_frame: pd.DataFrame,
    x: str = "salesMonth",
    y: str = "totalSales",
    title: str = "Sales over time",
):
    # area_sales_trend no usa title
    return area_sales_trend(data_frame=data_frame, x=x, y=y)


@capture("graph")
def pie_abc_sales(
    data_frame: pd.DataFrame,
    names: str = "abc_class",
    values: str = "total_sales",
    agg: AggFunc = "sum",
    title: str = "ABC distribution",
):
    df = data_frame.copy()

    if agg == "count":
        df_agg = df.groupby(names, dropna=False).size().reset_index(name=values)
    else:
        df_agg = df.groupby(names, dropna=False).agg({values: agg}).reset_index()

    color_map = {"A": "#1a85ff", "B": "#7ea1ee", "C": "#d41159"}

    fig = px.pie(
        data_frame=df_agg,
        names=names,
        values=values,
        color=names,
        color_discrete_map=color_map,
        hole=0.55,
        title=title,
    )
    fig.update_layout(legend_x=1, legend_y=1)
    return _apply_dark_layout(fig, title=title, height=340)


@capture("graph")
def pie(
    names: str,
    values: str,
    data_frame: pd.DataFrame,
    agg: str = "count",
):
    df = data_frame.copy()

    if agg == "count":
        df_agg = (
            df.groupby(names, dropna=False)
            .agg({values: "count"})
            .rename(columns={values: "value"})
            .reset_index()
        )
    else:
        df_agg = (
            df.groupby(names, dropna=False)
            .agg({values: agg})
            .rename(columns={values: "value"})
            .reset_index()
        )

    fig = px.pie(
        data_frame=df_agg,
        names=names,
        values="value",
        hole=0.45,
    )
    fig.update_layout(
        margin=dict(l=16, r=16, t=8, b=16),
        legend=dict(orientation="h", y=-0.05),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


@capture("graph")
def choropleth_world(
    locations: str,
    color: str,
    data_frame: pd.DataFrame,
    title: str = "Sales by country",
    agg: AggFunc = "sum",
    custom_data: Optional[List[str]] = None,
):
    df = data_frame.copy()

    if agg == "count":
        df_agg = df.groupby(locations, dropna=False).size().reset_index(name=color)
    else:
        df_agg = df.groupby(locations, dropna=False).agg({color: agg}).reset_index()

    fig = px.choropleth(
        data_frame=df_agg,
        locations=locations,
        locationmode="country names",
        color=color,
        color_continuous_scale=[
            "#ded6d8", "#f3bdcb", "#f7a9be", "#f894b1",
            "#f780a3", "#f46b94", "#ee517f", "#e94777",
            "#e43d70", "#df3168", "#d92460", "#d41159",
        ],
        title=title,
        custom_data=custom_data,
    )

    fig.update_layout(coloraxis_showscale=False)
    fig = _apply_world_geos(fig)
    fig = _apply_dark_layout(fig, title=title, height=520)
    fig.update_layout(margin=dict(l=8, r=8, t=50, b=8))
    return fig


@capture("graph")
def choropleth(
    locations: str,
    color: str,
    data_frame: pd.DataFrame,
    title: Optional[str] = None,
    custom_data: Optional[List[str]] = None,
):
    df = data_frame.copy()
    df_agg = df.groupby(locations, dropna=False).agg({color: "sum"}).reset_index()

    fig = px.choropleth(
        data_frame=df_agg,
        locations=locations,
        color=color,
        locationmode="country names",
        color_continuous_scale=[
            "rgba(255,255,255,0.08)",
            "rgba(26,133,255,0.35)",
            "rgba(26,133,255,0.65)",
            "rgba(26,133,255,0.90)",
        ],
        custom_data=custom_data,
    )

    fig.update_layout(coloraxis_showscale=False)
    fig = _apply_world_geos(fig)
    fig = _apply_dark_layout(fig, title=title, height=520)
    fig.update_layout(margin=dict(l=8, r=8, t=50 if title else 20, b=8))
    return fig


# TABLE CONFIGURATIONS ---------------------------------------------------------

LIFT_CELL_STYLE_1 = {
    "styleConditions": [
        {
            "condition": "Number(params.value) >= 11",
            "style": {"backgroundColor": "#1a85ff", "fontWeight": "700", "color": "#ffffff"},
        },
        {
            "condition": "Number(params.value) >= 5 && Number(params.value) < 11",
            "style": {"backgroundColor": "rgba(255,255,255,0.12)", "fontWeight": "600"},
        },
        {
            "condition": "Number(params.value) < 5",
            "style": {"backgroundColor": "#d41159", "fontWeight": "600", "color": "#ffffff"},
        },
    ]
}

COLUMN_DEFS_CROSS_SELL = [
    {"field": "productName_1", "headerName": "Product A", "width": 260, "pinned": "left"},
    {"field": "productName_2", "headerName": "Product B", "width": 260, "pinned": "left"},
    {"field": "cooccurrence_count", "headerName": "Co-occur", "width": 120, "type": "rightAligned"},
    {
        "field": "support", "headerName": "Support", "width": 120, "type": "rightAligned",
        "valueFormatter": {"function": "d3.format(',.3f')(params.value)"},
    },
    {
        "field": "confidence_from_p1", "headerName": "Conf(A→B)", "width": 130, "type": "rightAligned",
        "valueFormatter": {"function": "d3.format(',.3f')(params.value)"},
    },
    {
        "field": "lift",
        "headerName": "Lift",
        "width": 110,
        "type": "rightAligned",
        "cellDataType": "number",
        "valueFormatter": {"function": "d3.format(',.2f')(params.value)"},
        "cellStyle": LIFT_CELL_STYLE_1,
    },
]
