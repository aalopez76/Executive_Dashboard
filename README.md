# Classic Models Sales - KPI Report


<p align="center">
  <img src="assets/images/kpi-dashboard.png" alt="Dashboard Preview" width="400">
</p>



## Project Background

As a professional Data Scientist, the development of an executive dashboard provides the strategic bridge between raw data processing and high-level decision-making. For Toys & Models Co., I developed an enterprise-grade interactive dashboard to provide actionable insights into sales performance, customer behavior, and operational risks. **This dashboard analyzes 283 orders placed between 2018 and February 2020 across North America, Europe, and Asia-Pacific, covering 98 active customers, 110 products, and an organization of 23 employees (17 sales reps) in 7 offices**. The goal was to transform raw transactional data into strategic insights that drive decision-making for executives, sales managers, and business stakeholders.

> **Data note:** the database is a curated *subset* of the canonical *classicmodels* schema. All figures below are verified directly against this database (see the SQL portfolio in [SQL-Queries](https://github.com/aalopez76/SQL-Queries)); do not assume the canonical totals.

````Markdown
```
Raw Tables (SQLite)          SQL Analytics Layer              Dashboard Layer
─────────────────            ───────────────────              ───────────────
┌─────────────┐              ┌──────────────┐               ┌──────────────┐
│ customers   │──┐           │ Descriptive  │──┐            │ Executive    │
│ orders      │  │           │ (What?)      │  │            │ View         │
│ orderdetails│  ├─────────▶│              │  │            ├──────────────┤
│ products    │  │           │ Analytical   │  │            │ Regional     │
│ employees   │  │           │ (Why?)       │  ├──────────▶│ View         │
│ payments    │  │           │              │  │            ├──────────────┤
│ offices     │  │           │ Diagnostic   │  │            │ Risks &      │
│ productlines│──┘           │ (What wrong?)│  │            │ Diagnostics  │
└─────────────┘              │              │  │            ├──────────────┤
                             │ Predictive   │  │            │ Opportunities│
                             │ (What next?) │──┘            ├──────────────┤
                             └──────────────┘               │ Deep Dive    │
                                                            └──────────────┘
```
````

The analysis leverages a **multi-layer SQL analytics framework** (descriptive, analytical, diagnostic, and predictive) combined with **Vizro's modern visualization capabilities** to deliver real-time KPIs, risk detection, and growth opportunities.

### **Dashboard Key Features**
- **Real-Time KPIs**: 5 executive cards with YoY % change calculations
- **Interactive Filters**: Click-to-filter maps, radio button selectors, dropdown menus
- **Advanced Tables**: AG Grid with conditional formatting (ABC highlighting, status indicators, emoji lift scores)
- **Responsive Design**: Dark theme, mobile-compatible layouts
- **Modular Architecture**: Git submodules for SQL queries and database connectors

---

## Executive Summary

This dashboard provides comprehensive insights across five key areas: executive KPIs, regional performance, risk diagnostics, growth opportunities, and deep-dive analytics. The analysis reveals **moderate revenue concentration** among top customers and products, **geographic imbalance** in sales distribution, and **predictable demand patterns** ideal for forecasting. Key findings include **credit-misalignment risk of ~$3.05M** flagged across high-risk customers, **payment coverage of 94.7% by amount**, and **1,367 cross-sell product pairs** surfaced for bundling opportunities.

---

## Insights Deep-Dive

[![Hugging Face Space](https://img.shields.io/badge/HuggingFace-Live%20Dashboard-yellow?logo=huggingface)](https://huggingface.co/spaces/aalpzp/Executive_KPI_Dashboard)


### **Customer & Geographic Performance**
- **98 active customers** (122 registered) distributed across 22 countries, with significant concentration in North America and Western Europe.
- **Top 20% of customers generate ~39% of revenue** (ABC segmentation) — a meaningful but moderate concentration, not an extreme Pareto.
- **Geographic concentration**: USA, Spain, and France account for **~55% of total sales** (USA alone 34.7%), while many countries contribute under 1% each.
- **Sales-rep coverage**: a subset of customers have no assigned sales rep (all with a 0 credit limit) — a valid optional gap rather than a data error.

### **Product Portfolio Analysis**
- **110 SKUs** across 7 product lines (Classic Cars, Motorcycles, Planes, Ships, Trains, Trucks & Buses, Vintage Cars).
- **Top 10 products drive ~18% of revenue**; it takes ~47 SKUs to reach 60% — i.e. revenue is *spread*, not dominated by a few.
- **Classic Cars** lead with **40.5%** of sales, followed by **Vintage Cars (18.9%)** and **Motorcycles (11.2%)**.
- **Cross-sell analysis** surfaces **1,367 product pairs** (co-occurrence, support, confidence) for market-basket bundling.

### **Operational Quality & Risk Management**
- **High-risk customers identified**: **58 accounts** with credit/sales misalignment.
- **Amount at risk**: **~$3.05M** across those high-risk customers.
- **Credit policy gaps** (misalignment review): **1 over-credited** and **2 under-credited** accounts.
- **Referential integrity**: 0 orphan rows across the foreign keys (100% FK match) — the dataset is structurally sound.
- **Data quality**: **2.9% of rows** excluded from KPIs due to invalid date fields (orderDate/shippedDate/requiredDate).

### **Predictive Insights & Forecasting**
- **RFM customer segmentation** (122 scored customers): **Top ~25%**, **High ~20%**, **Mid ~23%**, **Low ~32%**.
- **Next-order prediction**: average reorder interval is **~204 days**; the dataset ends in **Feb 2020**, so recency-based churn signals are pronounced.
- **Demand seasonality**: monthly lag/lead features highlight recurring Q4 peaks, useful for inventory planning.
- **Payment coverage**: **94.7% by amount** — most invoiced revenue is collected.

### **Sales Organization Performance**
- **23 employees** (17 sales reps) across **7 offices** spanning North America, Europe, and Asia-Pacific.
- **Uneven workload distribution** across reps — an opportunity to rebalance portfolios.
- **Territory coverage**: several countries are served without a dedicated local rep, relying on remote management.

---

## Recommendations

Based on the findings, I recommend the following actions:

1. **Diversify the customer & geographic base**: target under-represented countries to reduce the ~55% top-3 concentration.
2. **Rebalance sales portfolios**: even out customers-per-rep to improve relationship quality and workload balance.
3. **Tighten credit policy**: review the 58 high-risk accounts (~$3.05M at risk) and the over/under-credited cases (1/2).
4. **Reduce churn risk**: prioritize outreach to customers well past their ~204-day reorder interval (recency-based).
5. **Leverage cross-sell**: promote high-confidence pairs from the 1,367 surfaced product pairs to top-RFM customers.
6. **Automate data-quality checks**: keep the FK/null integrity checks in CI to prevent the ~2.9% date-quality loss from growing.

---

### **Git Submodules**
This project uses 2 external repositories:
1. **[SQL-Queries](https://github.com/aalopez76/SQL-Queries)**: 39 production-grade SQL queries (descriptive, diagnostic, analytical, predictive, structural layers)
2. **[SQL-Connection-Module](https://github.com/aalopez76/SQL-Connection-Module)**: Multi-engine database connector (SQLite, PostgreSQL, MySQL, etc.), used by the dashboard's data engine

---

> Figures verified against the database. QA assisted by AI tooling.

-----
------
# Executive KPI Dashboard
### Turning transactional data into board-ready decisions.

[![Live demo](https://img.shields.io/badge/Live-Hugging%20Face%20Space-yellow?logo=huggingface)](https://huggingface.co/spaces/aalpzp/Executive_KPI_Dashboard)
[![Dashboard repo](https://img.shields.io/badge/Code-Executive__Dashboard-181717?logo=github)](https://github.com/aalopez76/Executive_Dashboard)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)](https://github.com/aalopez76/Executive_Dashboard/actions)

> **A deployed analytics product** — not a notebook — that consolidates sales performance, operational
> risk, and growth opportunities into a single executive view, backed by a production SQL layer,
> automated tests, and CI/CD.

<p align="center">
  <img src="assets/images/kpi-dashboard.png" alt="Executive KPI Dashboard — Executive View" width="720">
  <br><em>Executive view: real-time KPIs with year-over-year deltas, risk flags, and drill-downs.</em>
</p>

---

## Executive Summary

Leadership teams sit on transactional systems that record *what happened* but rarely answer *what to do
next*. I built an end-to-end analytics product that closes that gap: a five-layer SQL framework feeds an
interactive dashboard that lets executives, sales managers, and commercial teams **see performance,
catch risk early, and act on opportunities** — without waiting on manual reporting cycles.

The work spans the full stack of a modern data product: **production SQL**, a **reusable data connector**,
**automated testing & CI**, and a **reproducible cloud deployment** — engineered so the numbers can be
trusted and the product can be maintained.

### Key metrics at a glance *(all verified against the database)*

| Metric | Value | Note |
|---|---:|---|
| Orders analyzed | **283** | 2018 → Feb 2020 |
| Customers | **122** (98 active) | 18% without an assigned rep |
| Products / lines | **110 / 7** | catalog breadth |
| Countries with sales | **22** | NA · EU · APAC |
| Referential integrity | **100%** | 0 orphan rows, 0 duplicate PKs |
| Payment coverage | **94.7%** | of revenue, by amount |
| Credit risk flagged | **58 customers / ~$3.05M** | exposure surfaced for review |
| On-time delivery | **~100%** | 1 late of 278 shipped |
| Cross-sell pairs | **1,367** | market-basket (support/confidence) |
| Production SQL queries | **39** | across 5 analytical layers |

> **Rigor note:** the database is a curated **subset** of *Classic Models*. Every figure on this page is
> reproduced from a SQL query against the actual data — **not** the canonical reference totals.

---

## Business Problem

Transactional systems store records but rarely enable strategy. The objective was an analytics layer +
dashboard that:

- **consolidates** business-critical KPIs into one executive view,
- **detects** revenue, credit, and operational risk early,
- **surfaces** cross-sell and growth opportunities via association metrics,
- **enables** fast, self-service drill-down — no ad-hoc reporting cycles.

---

## Analytics Architecture

A three-layer data-product architecture, from raw tables to decisions:

```
Raw Tables (SQLite)          SQL Analytics Layer              Dashboard Layer
─────────────────            ───────────────────              ───────────────
┌─────────────┐              ┌──────────────┐               ┌──────────────┐
│ customers   │──┐           │ Descriptive  │──┐            │ Executive    │
│ orders      │  │           │ (What?)      │  │            │ View         │
│ orderdetails│  ├─────────▶│              │  │            ├──────────────┤
│ products    │  │           │ Analytical   │  │            │ Regional     │
│ employees   │  │           │ (Why?)       │  ├──────────▶│ View         │
│ payments    │  │           │              │  │            ├──────────────┤
│ offices     │  │           │ Diagnostic   │  │            │ Risks &      │
│ productlines│──┘           │ (What wrong?)│  │            │ Diagnostics  │
└─────────────┘              │ Predictive   │  │            ├──────────────┤
                             │ (What next?) │──┘            │ Opportunities│
                             └──────────────┘               │ Deep Dive    │
                                                            └──────────────┘
```

<p align="center">
  <img src="assets/images/toys_and_models-db.png" alt="Database schema (Classic Models / Toys & Models Co.)" width="640">
  <br><em>Relational schema — the single source of truth behind every metric.</em>
</p>

---

## Data Model & Dataset Quality

**Dataset summary (verified):** 283 orders · 2,649 order details · 249 payments · 122 customers
(98 with orders) · 110 products / 7 lines · 23 employees / 7 offices · 22 countries · dates **2018 → Feb 2020**.

**Quality checks** (nulls, duplicates, FK & hierarchy integrity):

| Check | Result |
|---|---|
| Referential integrity (all FKs) | ✅ **0 orphan rows** (100% match) |
| Duplicate primary keys | ✅ **0** |
| Customers without sales rep | ⚠️ **18%** (valid optional gap, 0 credit limit) |
| Rows with invalid dates (excluded from KPIs) | ⚠️ **2.9%** |
| Payment coverage (by amount) | ✅ **94.7%** |

---

## Key Findings *(verified)*

- **Revenue is diversified, not concentrated.** The top 10 products drive only ~**18%** of revenue
  (it takes ~47 SKUs to reach 60%) — low single-SKU dependency, a portfolio strength.
- **Moderate customer concentration.** Top 20% of customers ≈ **39%** of revenue (ABC/Pareto).
- **Geographic concentration risk.** USA, Spain, and France ≈ **55%** of sales (USA alone 34.7%).
- **Product mix.** Classic Cars **40.5%**, Vintage Cars **18.9%**, Motorcycles **11.2%**.
- **Credit exposure surfaced.** **58 high-risk customers**, ~**$3.05M** flagged for credit review.
- **Strong operations.** On-time delivery ≈ **100%**; payment coverage **94.7%**.
- **Retention signals.** RFM segmentation (Top 25% / High 20% / Mid 23% / Low 32%); avg reorder ≈ **204 days**.
- **Cross-sell upside.** Market-basket analysis across **1,367 product pairs**.

---

## SQL Analytics Framework — 39 production queries, 5 modules

| Layer | Question | Examples |
|---|---|---|
| **Descriptive / DQ** | What happened? | KPIs, completeness, uniqueness, FK integrity |
| **Analytical** | Why? | country/region/product/customer/rep deep-dives |
| **Diagnostic** | What went wrong? | credit anomalies, outliers, risk flags |
| **Predictive** | What's next? | RFM, seasonality, next-order, cross-sell |
| **Structural** | How is it organized? | recursive org hierarchy, office–territory coverage |

Each query is production-grade SQL with CTEs, window functions, and recursive logic. Two samples:

**RFM scoring** *(customer engagement / churn proxy)*

```sql
WITH CustomerRFM AS (
    SELECT  c.customerNumber, c.customerName,
            COUNT(DISTINCT o.orderNumber)                     AS freq_orders,
            COALESCE(SUM(od.quantityOrdered * od.priceEach),0) AS monetary,
            MAX(o.orderDate)                                  AS last_order_date
    FROM customers c
    LEFT JOIN orders       o  ON c.customerNumber = o.customerNumber
    LEFT JOIN orderdetails od ON o.orderNumber    = od.orderNumber
    GROUP BY c.customerNumber, c.customerName
)
-- Recency/Frequency/Monetary bucketed with NTILE() and combined into an RFM score.
```

**Recursive organizational hierarchy** *(reporting chain, any employee → CEO)*

```sql
WITH RECURSIVE EmployeeHierarchy AS (
    SELECT employeeNumber, reportsTo,
           firstName || ' ' || lastName AS employeeName, 1 AS level
    FROM employees
    WHERE employeeNumber = 1370          -- start node
    UNION ALL
    SELECT e.employeeNumber, e.reportsTo,
           e.firstName || ' ' || e.lastName, h.level + 1
    FROM employees e
    JOIN EmployeeHierarchy h ON e.employeeNumber = h.reportsTo   -- climb up
)
SELECT * FROM EmployeeHierarchy;
```

---

## Engineering & Reliability

What turns this analysis into a **maintainable product** — and demonstrates senior, full-lifecycle ownership:

| Area | Implementation |
|---|---|
| **Data engine** | Reads through my own multi-engine SQL connector (`SQL-Connection-Module`) — *dogfooding* a reusable component instead of ad-hoc `sqlite3`. |
| **Reproducibility** | Pinned dependency lockfile · Python 3.12 · deterministic builds. |
| **Testing** | Integration (data contract, query resolution, dashboard build) · unit (KPI math) · **end-to-end browser tests (Playwright)** · **data-regression snapshots** that catch silent metric drift. |
| **CI/CD** | **GitHub Actions** runs lint + tests + headless e2e on every push/PR. |
| **Deployment** | One-command bundle generator → self-contained Docker image, **live on Hugging Face Spaces** (gunicorn/WSGI) with a `/health` endpoint. |
| **Data trust** | Every published figure is query-backed; FK/integrity checks run in CI to prevent regressions. |
| **System design** | Three coordinated repos (dashboard + SQL layer + connector) wired via Git submodules. |

**Tech stack:** SQL (SQLite) · Python 3.12 · pandas · Vizro / Dash / Plotly · gunicorn · Docker ·
GitHub Actions · Playwright · pytest · ruff · Hugging Face Spaces.

---

## Links

- 🚀 **Live dashboard** — [Hugging Face Space](https://huggingface.co/spaces/aalpzp/Executive_KPI_Dashboard)
- 📊 **Dashboard** — [Executive_Dashboard](https://github.com/aalopez76/Executive_Dashboard)
- 🧮 **SQL analytics layer** — [SQL-Queries](https://github.com/aalopez76/SQL-Queries)
- 🔌 **Connection module** — [SQL-Connection-Module](https://github.com/aalopez76/SQL-Connection-Module)

<sub>Figures verified against the database on 2026-06-04. QA assisted by AI tooling.</sub>

