# utils/pages.py
import pandas as pd
import vizro.models as vm
import vizro.actions as va
from vizro.tables import dash_ag_grid
from vizro.figures import kpi_card_reference

from utils._charts import bar, pie, choropleth


# ---------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------
def build_kpi_banner(df_kpi_cards, current_year: int, previous_year: int) -> vm.Container:
    return vm.Container(
        layout=vm.Flex(direction="row"),
        components=[
            vm.Figure(
                figure=kpi_card_reference(
                    df_kpi_cards,
                    value_column=f"Total_Revenue_{current_year}",
                    reference_column=f"Total_Revenue_{previous_year}",
                    title="Total Revenue",
                    value_format="${value:,.0f}",
                    reference_format="{delta_relative:+.1%} vs. {reference:,.0f}",
                    icon="attach_money",
                )
            ),
            vm.Figure(
                figure=kpi_card_reference(
                    df_kpi_cards,
                    value_column=f"Total_Orders_{current_year}",
                    reference_column=f"Total_Orders_{previous_year}",
                    title="Total Orders",
                    value_format="{value:,.0f}",
                    reference_format="{delta_relative:+.1%} vs. {reference:,.0f}",
                    icon="shopping_cart",
                )
            ),
            vm.Figure(
                figure=kpi_card_reference(
                    df_kpi_cards,
                    value_column=f"AOV_{current_year}",
                    reference_column=f"AOV_{previous_year}",
                    title="Avg Order Value",
                    value_format="${value:,.0f}",
                    reference_format="{delta_relative:+.1%} vs. ${reference:,.0f}",
                    icon="local_atm",
                )
            ),
            vm.Figure(
                figure=kpi_card_reference(
                    df_kpi_cards,
                    value_column=f"OnTimeRate_{current_year}",
                    reference_column=f"OnTimeRate_{previous_year}",
                    title="On-Time Delivery",
                    value_format="{value:.1f}%",
                    reference_format="{delta:+.1f}pp vs. {reference:.1f}%",
                    icon="local_shipping",
                )
            ),
            vm.Figure(
                figure=kpi_card_reference(
                    df_kpi_cards,
                    value_column=f"ProductConcentration_{current_year}",
                    reference_column=f"ProductConcentration_{previous_year}",
                    title="Top 10 Products Share",
                    value_format="{value:.1f}%",
                    reference_format="{delta:+.1f}pp vs. prev",
                    icon="inventory_2",
                )
            ),
        ],
    )


def build_page_exec(d: dict) -> vm.Page:
    df_monthly = d["monthly"]
    df_customers = d["customers"]
    df_products = d["products"]
    df_salesreps = d["salesreps"]
    df_regions = d["regions"]
    dq = d["data_quality"]

    years = sorted(df_monthly["year"].unique()) if "year" in df_monthly.columns else []
    if not years:
        years = sorted(pd.to_datetime(df_monthly["salesMonth"] + "-01").dt.year.unique())

    current_year = years[-1] if years else 2024
    previous_year = years[-2] if len(years) > 1 else current_year - 1

    kpi_banner = build_kpi_banner(d["kpi_cards"], current_year, previous_year)

    top_countries = (
        df_regions.groupby("country", as_index=False)["total_sales"]
        .sum()
        .rename(columns={"country": "label", "total_sales": "value"})
    )
    top_countries["view"] = "Top Countries"

    top_products = (
        df_products.groupby("productName", as_index=False)["total_sales"]
        .sum()
        .rename(columns={"productName": "label", "total_sales": "value"})
    )
    top_products["view"] = "Top Products"

    top_salesreps = (
        df_salesreps.groupby("employeeName", as_index=False)["total_sales"]
        .sum()
        .rename(columns={"employeeName": "label", "total_sales": "value"})
    )
    top_salesreps["view"] = "Top Sales Reps"

    top_lines = (
        d["base"].groupby("productLine", as_index=False)["lineSales"]
        .sum()
        .rename(columns={"productLine": "label", "lineSales": "value"})
    )
    top_lines["view"] = "Top Product Lines"

    df_top_views = pd.concat([top_countries, top_products, top_salesreps, top_lines], ignore_index=True)

    top_switch_graph = vm.Graph(
        id="exec-top-switch-graph",
        title="Top view",
        figure=bar(data_frame=df_top_views, y="label", x="value", agg="sum", top_n=12),
    )

    df_customers_abc = df_customers[["abc_class"]].copy()
    df_customers_abc["n"] = 1
    abc_pie = vm.Graph(
        title="Customer ABC classes",
        figure=pie(data_frame=df_customers_abc, names="abc_class", values="n", agg="sum"),
    )

    context = d["context"]
    context_footer = vm.Container(
        layout=vm.Grid(grid=[[0, 1]]),
        components=[
            vm.Card(
                text=(
                    f"**Organizational Context** • Offices: {context['offices']} • "
                    f"Sales Reps: {context['sales_reps']} • Countries: {context['countries_served']} • "
                    f"Customers: {context['customers']}"
                )
            ),
            vm.Card(
                text=(
                    f"**Data Quality** • Invalid date rows excluded from KPIs: "
                    f"{dq['invalid_date_rows']} ({dq['invalid_date_pct']}%)"
                )
            ),
        ],
    )

    return vm.Page(
        title="Executive View",
        layout=vm.Grid(grid=[[0, 0], [1, 2], [1, 2], [3, 3]]),
        components=[kpi_banner, top_switch_graph, abc_pie, context_footer],
        controls=[
            vm.Filter(
                column="view",
                selector=vm.RadioItems(
                    options=[
                        {"label": "Top Countries", "value": "Top Countries"},
                        {"label": "Top Products", "value": "Top Products"},
                        {"label": "Top Sales Reps", "value": "Top Sales Reps"},
                        {"label": "Top Product Lines", "value": "Top Product Lines"},
                    ]
                ),
            )
        ],
    )


def build_page_risks(d: dict) -> vm.Page:
    df_high_risk = d["high_risk"].copy()
    df_risk_by_country = d["risk_by_country"].copy()
    diag = d["diagnostic_summary"]

    MAP_ID = "risk-map-country"
    BAR_ID = "risk-bar-amount"

    if "amount_at_risk" not in df_high_risk.columns:
        df_high_risk["amount_at_risk"] = (
            df_high_risk.get("totalSales", 0) - df_high_risk.get("creditLimit", 0)
        ).clip(lower=0)

    bar_top_risk = vm.Graph(
        id=BAR_ID,
        title="Top high-risk customers ($ at risk)",
        figure=bar(data_frame=df_high_risk, y="customerName", x="amount_at_risk", agg="sum", top_n=10),
    )

    try:
        action_filter = va.filter_interaction(targets=[BAR_ID])
    except Exception:
        from vizro.actions import filter_interaction
        action_filter = vm.Action(function=filter_interaction(targets=[BAR_ID]))

    map_risk = vm.Graph(
        id=MAP_ID,
        title="Amount at risk by country (click to filter)",
        figure=choropleth(
            data_frame=df_risk_by_country,
            locations="country",
            color="risk_amount",
            custom_data=["country"],
        ),
        actions=[action_filter],
    )

    risk_footer = vm.Container(
        layout=vm.Grid(grid=[[0, 1, 2]]),
        components=[
            vm.Card(text=f"🔴 High-Risk: **{diag['high_risk_customers_count']}** • ${diag['amount_at_risk']:,.0f}"),
            vm.Card(
                text=(
                    f"🟡 Misalignment: **{diag['misalignment_count']}** "
                    f"• Over {diag['over_credited_count']} • Under {diag['under_credited_count']}"
                )
            ),
            vm.Card(text="🟢 Data Quality: OK"),
        ],
    )

    return vm.Page(
        title="Risks & Diagnostics",
        layout=vm.Grid(grid=[[0, 0, 1], [0, 0, 1], [2, 2, 2]]),
        components=[map_risk, bar_top_risk, risk_footer],
        controls=[],
    )


def build_page_opportunities(d: dict) -> vm.Page:
    df_products = d["products"]
    df_customer_rfm = d["customer_rfm"].copy()

    # Crear rfm_segment si el SQL no lo trae
    if "rfm_segment" not in df_customer_rfm.columns:
        if "rfm_score" in df_customer_rfm.columns:
            df_customer_rfm["rfm_segment"] = pd.cut(
                df_customer_rfm["rfm_score"],
                bins=[-float("inf"), 6, 9, 12, float("inf")],
                labels=["Low", "Mid", "High", "Top"],
            ).astype(str)
        else:
            df_customer_rfm["rfm_segment"] = "Unknown"

    rfm_counts = df_customer_rfm[["rfm_segment"]].copy()
    rfm_counts["n"] = 1

    return vm.Page(
        title="Opportunities",
        layout=vm.Grid(grid=[[0, 1], [0, 1]]),
        components=[
            vm.Graph(
                title="Top Products by Sales",
                figure=bar(data_frame=df_products, y="productName", x="total_sales", agg="sum", top_n=15),
            ),
            vm.Graph(
                title="RFM Segments",
                figure=pie(data_frame=rfm_counts, names="rfm_segment", values="n", agg="sum"),
            ),
        ],
    )




def build_page_deep_dive(d: dict) -> vm.Page:
    def _money_col(field: str, header: str, pinned: bool = False, width: int = 150):
        return {
            "field": field,
            "headerName": header,
            "type": "rightAligned",
            "width": width,
            **({"pinned": "left"} if pinned else {}),
            "valueFormatter": {"function": "d3.format('$,.0f')(params.value)"},
        }

    def _num_col(field: str, header: str, pinned: bool = False, width: int = 130, fmt: str = ",.0f"):
        return {
            "field": field,
            "headerName": header,
            "type": "rightAligned",
            "width": width,
            **({"pinned": "left"} if pinned else {}),
            "valueFormatter": {"function": f"d3.format('{fmt}')(params.value)"},
        }

    def _pct_col(field: str, header: str, width: int = 130):
        return {
            "field": field,
            "headerName": header,
            "type": "rightAligned",
            "width": width,
            "valueFormatter": {"function": "d3.format(',.2f')(params.value) + '%'"},
        }

    def _base_grid_opts(column_defs: list[dict], page_size: int = 25) -> dict:
        return {
            "pagination": True,
            "paginationPageSize": page_size,
            "columnDefs": column_defs,
            "defaultColDef": {"sortable": True, "filter": True, "resizable": True},
        }

    # Customers
    df_customers = d["customers"].copy()
    cust_cols = [
        "customerNumber", "customerName", "country",
        "total_sales", "num_orders", "num_products",
        "avg_sales_per_order", "pct_of_global_sales",
        "sales_rank", "abc_class",
    ]
    cust_cols = [c for c in cust_cols if c in df_customers.columns]
    df_customers_v = df_customers[cust_cols]

    customers_column_defs = [
        {"field": "customerNumber", "headerName": "ID", "width": 90, "pinned": "left"},
        {"field": "customerName", "headerName": "Customer", "width": 240, "pinned": "left"},
        {"field": "country", "headerName": "Country", "width": 140},
        _money_col("total_sales", "Total Sales", width=160),
        _num_col("num_orders", "Orders", width=110),
        _num_col("num_products", "Products", width=120),
        _money_col("avg_sales_per_order", "Avg / Order", width=150),
        _pct_col("pct_of_global_sales", "% Global Sales", width=150),
        _num_col("sales_rank", "Rank", width=90),
        {
            "field": "abc_class",
            "headerName": "ABC",
            "width": 90,
            "cellClassRules": {
                "cell-abc-a": "params.value === 'A'",
                "cell-abc-b": "params.value === 'B'",
                "cell-abc-c": "params.value === 'C'",
            },
        },
    ]
    customers_grid_opts = _base_grid_opts(customers_column_defs, page_size=25)

    # Products
    df_products = d["products"].copy()
    prod_cols = [
        "productCode", "productName", "productLine",
        "total_sales", "num_orders", "num_customers",
        "pct_of_global_sales", "sales_rank", "abc_class",
    ]
    prod_cols = [c for c in prod_cols if c in df_products.columns]
    df_products_v = df_products[prod_cols]

    products_column_defs = [
        {"field": "productCode", "headerName": "Code", "width": 110, "pinned": "left"},
        {"field": "productName", "headerName": "Product", "width": 260, "pinned": "left"},
        {"field": "productLine", "headerName": "Line", "width": 170},
        _money_col("total_sales", "Total Sales", width=160),
        _num_col("num_orders", "Orders", width=110),
        _num_col("num_customers", "Customers", width=120),
        _pct_col("pct_of_global_sales", "% Global Sales", width=150),
        _num_col("sales_rank", "Rank", width=90),
        {
            "field": "abc_class",
            "headerName": "ABC",
            "width": 90,
            "cellClassRules": {
                "cell-abc-a": "params.value === 'A'",
                "cell-abc-b": "params.value === 'B'",
                "cell-abc-c": "params.value === 'C'",
            },
        },
    ]
    products_grid_opts = _base_grid_opts(products_column_defs, page_size=25)

    # Sales Reps
    df_salesreps = d["salesreps"].copy()
    rep_cols = [
        "employeeNumber", "employeeName", "jobTitle", "officeCode",
        "total_sales", "num_orders", "num_customers",
        "pct_of_global_sales", "sales_rank", "abc_class",
    ]
    rep_cols = [c for c in rep_cols if c in df_salesreps.columns]
    df_salesreps_v = df_salesreps[rep_cols]

    reps_column_defs = [
        {"field": "employeeNumber", "headerName": "ID", "width": 90, "pinned": "left"},
        {"field": "employeeName", "headerName": "Sales Rep", "width": 220, "pinned": "left"},
        {"field": "jobTitle", "headerName": "Title", "width": 170},
        {"field": "officeCode", "headerName": "Office", "width": 110},
        _money_col("total_sales", "Total Sales", width=160),
        _num_col("num_orders", "Orders", width=110),
        _num_col("num_customers", "Customers", width=120),
        _pct_col("pct_of_global_sales", "% Global Sales", width=150),
        _num_col("sales_rank", "Rank", width=90),
        {
            "field": "abc_class",
            "headerName": "ABC",
            "width": 90,
            "cellClassRules": {
                "cell-abc-a": "params.value === 'A'",
                "cell-abc-b": "params.value === 'B'",
                "cell-abc-c": "params.value === 'C'",
            },
        },
    ]
    reps_grid_opts = _base_grid_opts(reps_column_defs, page_size=25)

    # Next Orders
    df_next = d["next_orders"].copy()
    next_cols = [
        "customerNumber", "customerName", "country",
        "last_order_date", "avg_gap_days", "expected_next_order_date",
    ]
    if "next_order_status" in df_next.columns:
        next_cols.append("next_order_status")
    
    next_cols = [c for c in next_cols if c in df_next.columns]
    df_next_v = df_next[next_cols].copy()

    next_column_defs = [
        {"field": "customerNumber", "headerName": "ID", "width": 90, "pinned": "left"},
        {"field": "customerName", "headerName": "Customer", "width": 240, "pinned": "left"},
        {"field": "country", "headerName": "Country", "width": 140},
        {"field": "last_order_date", "headerName": "Last Order", "width": 150},
        _num_col("avg_gap_days", "Avg Gap (days)", width=140, fmt=",.0f"),
        {"field": "expected_next_order_date", "headerName": "Expected Next", "width": 160},
    ]
    
    if "next_order_status" in df_next_v.columns:
        next_column_defs.append(
            {
                "field": "next_order_status",
                "headerName": "Status",
                "width": 150,
                "cellClassRules": {
                    "cell-status-overdue": "params.value === 'Overdue'",
                    "cell-status-duesoon": "params.value === 'Due Soon'",
                    "cell-status-ontrack": "params.value === 'On Track'",
                },
            }
        )
    
    next_grid_opts = _base_grid_opts(next_column_defs, page_size=25)

    # Cross Sell - CON EMOJIS (solución definitiva)
    df_cross = d["cross_sell"].copy()
    
    def format_lift_visual(lift):
        if pd.isna(lift):
            return ""
        if lift > 10:
            return f"🔵 {lift:.2f}"
        elif lift >= 5:
            return f"⚪ {lift:.2f}"
        else:
            return f"🔴 {lift:.2f}"
    
    df_cross["lift_formatted"] = df_cross["lift"].apply(format_lift_visual)
    
    cross_cols = [
        "productName_1", "productName_2",
        "cooccurrence_count", "support", "confidence_from_p1", 
        "lift_formatted"
    ]
    cross_cols = [c for c in cross_cols if c in df_cross.columns]
    df_cross_v = df_cross[cross_cols].copy()
    
    cross_column_defs = [
        {"field": "productName_1", "headerName": "Product A", "width": 220, "pinned": "left"},
        {"field": "productName_2", "headerName": "Product B", "width": 220, "pinned": "left"},
        _num_col("cooccurrence_count", "Co-occur", width=100),
        {
            "field": "support",
            "headerName": "Support",
            "width": 100,
            "type": "rightAligned",
            "valueFormatter": {"function": "d3.format(',.3f')(params.value)"},
        },
        {
            "field": "confidence_from_p1",
            "headerName": "Conf(A→B)",
            "width": 110,
            "type": "rightAligned",
            "valueFormatter": {"function": "d3.format(',.3f')(params.value)"},
        },
        {
            "field": "lift_formatted",
            "headerName": "Lift",
            "width": 130,
            "cellDataType": "text",
        },
    ]
    cross_grid_opts = _base_grid_opts(cross_column_defs, page_size=25)

    return vm.Page(
        title="Deep Dive",
        layout=vm.Grid(grid=[[0]]),
        components=[
            vm.Tabs(
                tabs=[
                    vm.Container(
                        title="Customers",
                        components=[
                            vm.AgGrid(
                                figure=dash_ag_grid(
                                    df_customers_v,
                                    dashGridOptions=customers_grid_opts,
                                    dangerously_allow_code=True,
                                )
                            )
                        ],
                    ),
                    vm.Container(
                        title="Products",
                        components=[
                            vm.AgGrid(
                                figure=dash_ag_grid(
                                    df_products_v,
                                    dashGridOptions=products_grid_opts,
                                    dangerously_allow_code=True,
                                )
                            )
                        ],
                    ),
                    vm.Container(
                        title="Sales Reps",
                        components=[
                            vm.AgGrid(
                                figure=dash_ag_grid(
                                    df_salesreps_v,
                                    dashGridOptions=reps_grid_opts,
                                    dangerously_allow_code=True,
                                )
                            )
                        ],
                    ),
                    vm.Container(
                        title="Next Orders",
                        components=[
                            vm.AgGrid(
                                figure=dash_ag_grid(
                                    df_next_v,
                                    dashGridOptions=next_grid_opts,
                                    dangerously_allow_code=True,
                                )
                            )
                        ],
                    ),
                    vm.Container(
                        title="Cross Sell",
                        components=[
                            vm.AgGrid(
                                figure=dash_ag_grid(
                                    df_cross_v,
                                    dashGridOptions=cross_grid_opts,
                                    dangerously_allow_code=True,
                                )
                            )
                        ],
                    ),
                ]
            )
        ],
    )


def build_page_regional(d: dict) -> vm.Page:
    df_base = d["base"].copy()

    required = ["country", "productLine", "employeeName"]
    missing = [c for c in required if c not in df_base.columns]
    if missing:
        raise ValueError(
            f"[Regional View] Missing columns in d['base']: {missing}. "
            f"Available: {list(df_base.columns)}"
        )

    if "totalSales" not in df_base.columns:
        if "lineSales" in df_base.columns:
            df_base["totalSales"] = df_base["lineSales"]
        else:
            df_base["totalSales"] = 0

    df_country = (
        df_base.groupby("country", as_index=False)["totalSales"]
        .sum()
        .rename(columns={"totalSales": "sales"})
    )

    MAP_ID = "regional-map"
    BAR_PL_ID = "regional-bar-productline"
    BAR_SR_ID = "regional-bar-salesrep"

    map_sales = vm.Graph(
        id=MAP_ID,
        title="Sales by country (click to filter)",
        figure=choropleth(data_frame=df_country, locations="country", color="sales", custom_data=["country"]),
        actions=[va.filter_interaction(targets=[BAR_PL_ID, BAR_SR_ID])],
    )

    df_by_productline = (
        df_base.groupby(["country", "productLine"], as_index=False)["totalSales"]
        .sum()
        .rename(columns={"productLine": "label", "totalSales": "value"})
    )
    bar_by_productline = vm.Graph(
        id=BAR_PL_ID,
        title="By Product Line",
        figure=bar(data_frame=df_by_productline, y="label", x="value", agg="sum", top_n=12),
    )

    df_by_salesrep = (
        df_base.groupby(["country", "employeeName"], as_index=False)["totalSales"]
        .sum()
        .rename(columns={"employeeName": "label", "totalSales": "value"})
    )
    bar_by_salesrep = vm.Graph(
        id=BAR_SR_ID,
        title="By Sales Rep",
        figure=bar(data_frame=df_by_salesrep, y="label", x="value", agg="sum", top_n=12),
    )

    tabs_right = vm.Tabs(
        tabs=[
            vm.Container(title="By Product Line", components=[bar_by_productline]),
            vm.Container(title="By Sales Rep", components=[bar_by_salesrep]),
        ]
    )

    return vm.Page(
        title="Regional View",
        layout=vm.Grid(grid=[[0, 1, 1], [0, 1, 1]]),
        components=[map_sales, tabs_right],
        controls=[vm.Filter(column="country")],
    )