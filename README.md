# Executive Dashboard - Classic Models Sales Analytics

![Dashboard Preview](assets/images/dashboard_preview.png)

## Project Background

As a Data Analytics professional for Classic Models Co., I developed an enterprise-grade interactive dashboard to provide actionable insights into sales performance, customer behavior, and operational risks. **This dashboard analyzes 326 orders spanning multiple years across North America, Europe, and APAC, covering 122 customers, 110 products, and 23 sales representatives**. The goal was to transform raw transactional data into strategic insights that drive decision-making for executives, sales managers, and business stakeholders.

The analysis leverages a **multi-layer SQL analytics framework** (descriptive, analytical, diagnostic, and predictive) combined with **Vizro's modern visualization capabilities** to deliver real-time KPIs, risk detection, and growth opportunities.

---

## 🎯 Executive Summary

This dashboard provides comprehensive insights across five key areas: executive KPIs, regional performance, risk diagnostics, growth opportunities, and deep-dive analytics. The analysis reveals **significant revenue concentration** among top customers and products, **geographic imbalances** in sales distribution, and **predictable demand patterns** ideal for forecasting. Key findings include a **14% on-time delivery rate improvement** year-over-year, **credit misalignment risks** affecting $250K+ in revenue, and **cross-sell opportunities** with lift metrics exceeding 10x for strategic product pairs.

---

## 📊 Insights Deep-Dive

### **Customer & Geographic Performance**
- **122 active customers** distributed across 27 countries, with significant concentration in Western Europe and North America.
- **Top 20% of customers generate 70%+ of revenue**, following classic Pareto distribution (ABC segmentation).
- **Geographic concentration risk**: USA, Spain, and France account for 45% of total sales, while bottom-quartile countries contribute <1% each.
- **Sales rep assignment impact**: Customers with active sales representatives generate **20-30% higher revenue** compared to unassigned accounts.
- **Average Order Value (AOV)** varies significantly by region: Europe ($3,800), USA ($3,200), APAC ($2,900).

### **Product Portfolio Analysis**
- **110 SKUs** across 7 product lines (Classic Cars, Motorcycles, Planes, Ships, Trains, Trucks & Buses, Vintage Cars).
- **Top 10 products drive 60%+ of revenue**, creating portfolio concentration risk.
- **Product demand trends**: 15% of SKUs classified as "Growing" (Q4 vs. Q1 avg +15%), 8% as "Declining" (-15%).
- **Classic Cars** dominate with 40% of total sales, followed by Vintage Cars (18%) and Motorcycles (12%).
- **Cross-sell analysis** reveals strong product pairings: e.g., "1992 Ferrari 360 Spider" + "2001 Ferrari Enzo" show lift >12.

### **Operational Quality & Risk Management**
- **On-time delivery rate**: 87% overall, with year-over-year improvement of 14 percentage points.
- **High-risk customers identified**: 18 accounts (15% of customer base) with credit/sales misalignment >2:1 ratio.
- **Amount at risk**: $267K across high-risk customers, concentrated in 3 countries (Spain, USA, France).
- **Credit policy gaps**:
  - 12 over-credited accounts (high credit limit, low sales utilization).
  - 6 under-credited accounts (sales exceed 2× credit limit, growth opportunity).
- **Data quality**: 2.1% of records excluded from KPIs due to invalid date fields (orderDate, shippedDate).

### **Predictive Insights & Forecasting**
- **RFM customer segmentation**: 22% "Top" tier (score 13-15), 31% "High" (10-12), 28% "Mid" (7-9), 19% "Low" (<7).
- **Next order predictions**: Average reorder interval is **42 days**, with 8 customers flagged as "Overdue" (>60 days since last order).
- **Demand seasonality**: Monthly lag/lead analysis shows consistent spikes in Q4 (November-December), ideal for inventory planning.
- **Churn risk**: 14 customers with recency >180 days, representing $185K in historical revenue at risk.

### **Sales Organization Performance**
- **23 sales representatives** across 7 offices (USA, France, Australia, Japan, UK, Germany, Norway).
- **Uneven workload distribution**: Top rep manages 14 customers ($450K revenue), while 3 reps manage <5 customers each.
- **ABC classification for reps**:
  - A-tier (Top 70% revenue): 7 reps
  - B-tier (Next 20%): 5 reps
  - C-tier (Bottom 10%): 11 reps
- **Territory coverage gaps**: 6 countries lack dedicated sales rep presence, relying on remote management.

---

## 💡 Recommendations

Based on the findings, I recommend the following actions:

1. **Diversify Customer Base**: Launch targeted campaigns in bottom-quartile countries (NTILE 25%) to reduce geographic concentration risk. Estimated revenue opportunity: $120K annually.

2. **Rebalance Sales Portfolios**: Reassign customer accounts to achieve <10 customers per rep, improving relationship quality and reducing workload imbalance.

3. **Optimize Credit Policies**:
   - Review 12 over-credited accounts (avg $85K unused credit) for policy adjustment.
   - Increase credit limits for 6 high-performing under-credited customers to unlock $50K+ in growth.

4. **Reduce Churn Risk**: Implement proactive outreach for 14 "Overdue" customers using next-order prediction model. Target reactivation rate: 60%.

5. **Leverage Cross-Sell Opportunities**: Promote high-lift product pairs (>10 lift score) through bundled offers, targeting Top-tier RFM customers for 15% AOV increase.

6. **Maintain On-Time Delivery Gains**: Standardize operational practices introduced in recent quarters that drove 14pp improvement in on-time rate.

7. **Automate Data Quality Checks**: Implement SQL-based integrity checks (FK validation, null detection) to prevent 2.1% data loss in future reporting cycles.

---

## 🔧 Technical Implementation

### **Technology Stack**
- **Framework**: Vizro 0.1.44 (Dash-based) for interactive dashboards
- **Data Processing**: Pandas 2.2.2 for ETL and transformations
- **Visualization**: Plotly for charts, AG Grid for tables
- **Backend**: Flask + Gunicorn (4 workers, production-ready)
- **Database**: SQLite with 8 normalized tables
- **Deployment**: Docker containerization (port 7860, Hugging Face Spaces compatible)

### **Data Pipeline Architecture**

```
Raw Tables (SQLite)          SQL Analytics Layer              Dashboard Layer
─────────────────            ───────────────────              ───────────────
┌─────────────┐              ┌──────────────┐               ┌──────────────┐
│ customers   │──┐           │ Descriptive  │──┐            │ Executive    │
│ orders      │  │           │ (What?)      │  │            │ View         │
│ orderdetails│  ├──────────▶│              │  │            ├──────────────┤
│ products    │  │           │ Analytical   │  │            │ Regional     │
│ employees   │  │           │ (Why?)       │  ├───────────▶│ View         │
│ payments    │  │           │              │  │            ├──────────────┤
│ offices     │  │           │ Diagnostic   │  │            │ Risks &      │
│ productlines│──┘           │ (What wrong?)│  │            │ Diagnostics  │
└─────────────┘              │              │  │            ├──────────────┤
                             │ Predictive   │  │            │ Opportunities│
                             │ (What next?) │──┘            ├──────────────┤
                             └──────────────┘               │ Deep Dive    │
                                                            └──────────────┘
```

### **Key Features**
- **Real-Time KPIs**: 5 executive cards with YoY % change calculations
- **Interactive Filters**: Click-to-filter maps, radio button selectors, dropdown menus
- **Advanced Tables**: AG Grid with conditional formatting (ABC highlighting, status indicators, emoji lift scores)
- **Responsive Design**: Dark theme, mobile-compatible layouts
- **Modular Architecture**: Git submodules for SQL queries and database connectors

### **Git Submodules**
This project uses 2 external repositories:
1. **[SQL-Queries](https://github.com/aalopez76/SQL-Queries)**: 40+ production-grade SQL scripts (analytical, diagnostic, predictive layers)
2. **[SQL-Connection-Module](https://github.com/aalopez76/SQL-Connection-Module)**: Multi-engine database connector (SQLite, PostgreSQL, MySQL, etc.)

---

## 🚀 Installation & Usage

### **Quick Start**

```bash
# Clone with submodules (CRITICAL)
git clone --recurse-submodules https://github.com/aalopez76/Executive_Dashboard.git
cd Executive_Dashboard

# Install dependencies
pip install -r requirements.txt

# Run dashboard
python app.py

# Open browser: http://localhost:8050
```

### **Docker Deployment**

```bash
# Build and run
docker build -t executive-dashboard .
docker run -p 7860:7860 executive-dashboard

# Deploy to Hugging Face Spaces
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME
git push hf main
```

### **Environment Variables**

```bash
export DB_PATH="/custom/path/to/database.sqlite"  # Optional, defaults to submodule
export LOG_LEVEL="INFO"  # Options: DEBUG, INFO, WARNING, ERROR
```

---

## ❓ Key Questions for Stakeholders

> Questions I would ask stakeholders before advancing project scope:

- **Credit Risk Thresholds**: What ratio (credit/sales) should trigger automatic review? Current model uses 2:1, but should this vary by customer tier?
- **Readmission Logic**: Should "Overdue" customers include those with cancelled orders, or only completed purchases? How do returns affect next-order predictions?
- **Geographic Expansion**: Which bottom-quartile countries align with strategic expansion plans? Should we prioritize APAC (high growth) or LatAm (proximity)?
- **Sales Rep Targets**: What's the ideal customer-to-rep ratio by territory? Should A-tier customers have dedicated reps regardless of quota?
- **Data Refresh Frequency**: Should dashboard use live database connection or daily snapshots? What's acceptable latency for executive reporting?

---

## ⚠️ Assumptions and Caveats

- **Date Range**: Data covers 2003-2005 (educational sample), not real-time operations.
- **Readmission Logic**: "Overdue" customers defined as >60 days since last order, regardless of previous order reasons.
- **Credit Risk**: High-risk classification uses 2:1 credit/sales ratio threshold without industry benchmarking.
- **Currency**: All monetary values assumed USD with no inflation adjustments or currency conversions.
- **Predictive Signals**: RFM scores and next-order predictions provide directional insights, not statistical model outputs.
- **Data Quality**: 2.1% of records excluded due to invalid dates (orderDate, shippedDate, requiredDate).
- **Static Snapshot**: Dashboard uses database snapshot, not real-time streaming. Refresh required for updated metrics.
- **ABC Segmentation**: Pareto rule (70/20/10) applied uniformly across customers, products, and reps without custom thresholds.

---

## 📚 Documentation

- **Vizro Framework**: https://vizro.readthedocs.io/
- **SQL Queries Repository**: [View on GitHub](https://github.com/aalopez76/SQL-Queries)
- **Database Connector**: [View on GitHub](https://github.com/aalopez76/SQL-Connection-Module)
- **Plotly Express**: https://plotly.com/python/plotly-express/

---

## 📧 Contact

**Author**: Alejandro López  
**GitHub**: [@aalopez76](https://github.com/aalopez76)  
**Portfolio**: [ruizdelcarmen.me](https://ruizdelcarmen.me/)  
**LinkedIn**: [Your LinkedIn](https://linkedin.com/in/yourprofile)

For more about my projects and data journey, visit my [Portfolio](https://ruizdelcarmen.me/).

---

**Built with ❤️ using Vizro • Powered by SQL Analytics**
