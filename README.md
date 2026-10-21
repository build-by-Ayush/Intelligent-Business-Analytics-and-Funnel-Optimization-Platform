# Intelligent Business Analytics & Funnel Optimization Platform

An e-commerce analytics application built to answer four business questions: **How are sales and profit performing? Where are potential buyers leaving? How much value is tied to returns? Which products deserve a closer look?**

**[🚀 Open the Live Demo](https://build-by-ayush-intelligent-business-analytics-and-fu-app-ndnyxy.streamlit.app/)**

## Project at a Glance

| | |
|---|---|
| **Dashboard pages** | Overview, Funnel Analysis, Returns, Product Analysis |
| **Tools** | Python, Pandas, Plotly, Streamlit |
| **Main goal** | Bring sales, customer activity, product profitability, and returns together so a business user can see what happened and decide what to investigate next |

## Project Screenshots

<p align="center">
  <img src="Images/Overview 1.png" width="400" alt="Overview dashboard" />
  <img src="Images/Funnel 1.png" width="400" alt="Funnel analysis dashboard" />
  <img src="Images/Return 1.png" width="400" alt="Returns analysis dashboard" />
  <img src="Images/Product 1.png" width="400" alt="Product analysis dashboard" />
</p>

## Key Findings

The figures below reflect the current validation run, with orders and return requests recorded through **20 April 2026**.

| Measure | Current result | What it tells the business |
|---|---:|---|
| Visit sessions | **116,017** | Sessions entering the buying journey |
| Completed orders | **9,716** | Sessions that reached purchase |
| Visit-to-purchase conversion | **8.37%** | Share of visit sessions that resulted in a purchase |
| View-to-add-to-cart drop-off | **67.49%** | Share of view sessions that did not reach add-to-cart |
| Checkout-start-to-purchase drop-off | **74.24%** | Share of checkout-start sessions that did not end in purchase |
| Net merchandise sales | **₹10.66 crore** | Sales after discounts, before refunds; tax and shipping are excluded |
| Product gross profit | **₹3.24 crore** | Net merchandise sales after product costs are accounted for |
| Units sold | **19,829** | Total quantity purchased |
| Return requests | **1,842** | Distinct return request IDs in the current report |
| Units requested for return | **1,870** | Quantity covered by return requests |
| Return-request unit rate | **9.43%** | Requested return units divided by units sold |
| Approved refund value | **₹51.92 lakh** | Adjusted merchandise value of approved return units |
| Pending refund exposure | **₹9.84 lakh** | Estimated merchandise value tied to pending return requests |

### What stands out?

- **The biggest loss by session count happens before add-to-cart.** The funnel goes from 116,017 view sessions to 37,714 add-to-cart sessions. That is 78,303 fewer sessions reaching the cart.
- **Checkout still needs a closer look.** Of the 37,714 sessions that reached checkout start, 9,716 ended in a purchase. The current checkout-start-to-purchase drop-off is 74.24%, so only 25.76% of checkout-start sessions resulted in a purchase.
- **Sales and profit answer different questions.** Net merchandise sales were ₹10.66 crore and product gross profit was ₹3.24 crore. A product can bring in substantial sales without contributing the same level of profit.
- **Return requests affect the value at risk.** The current report records ₹51.92 lakh in adjusted approved refunds and ₹9.84 lakh in pending refund exposure. Approved and pending amounts are kept separate because they represent different stages of the return process.

These measures show where to investigate next. They do not, by themselves, prove why customers leave the buying journey or why products are returned.

## What Each Page Helps Answer

### 1. Overview - How is the business performing?

The Overview page brings sales, orders, product gross profit, and return measures together. Trends and regional comparisons help show where performance is changing and where a closer look may be needed.

**Use it to:** get an overall view before investigating a specific part of the business.

### 2. Funnel Analysis - Where are potential buyers leaving?

The current funnel follows these stages:

`Visit → View → Add to Cart → Checkout Start → Purchase`

| Stage | Sessions | Conversion from previous stage | Drop-off from previous stage |
|---|---:|---:|---:|
| Visit | 116,017 | 100.00% | 0.00% |
| View | 116,017 | 100.00% | 0.00% |
| Add to Cart | 37,714 | 32.51% | 67.49% |
| Checkout Start | 37,714 | 100.00% | 0.00% |
| Purchase | 9,716 | 25.76% | 74.24% |

The table points to two different areas for investigation. The biggest reduction in session count occurs between view and add-to-cart, while the largest percentage drop between consecutive stages occurs between checkout start and purchase. Device comparisons and median time between actions can help narrow down where to look further.

**Use it to:** choose whether to investigate product interest, cart progression, checkout completion, or differences across devices.

### 3. Returns - How much value is affected by return requests?

The Returns page examines return reasons, return-request rates, approved refunds, pending refund exposure, and differences across product groups and customer segments. It also examines the time taken to resolve requests when the required dates are available.

The current results show a **9.43% return-request unit rate**, **₹51.92 lakh in adjusted approved refund value**, and **₹9.84 lakh in pending refund exposure**.

**Use it to:** identify common return reasons, find where return activity is concentrated, and track approved amounts separately from requests still awaiting a decision.

### 4. Product Analysis - Which products contribute value?

Products are compared using sales, gross profit, and return patterns. The four-quadrant view separates products with higher or lower sales from products with higher or lower profit:

- **Stars:** high sales and high profit.
- **Hidden Gems:** lower sales and high profit.
- **Inefficient Products:** high sales and lower profit.
- **Low Sales / Low Profit:** products that may need a closer review.

Monthly comparisons and pricing scenarios help examine changes in product performance. Return patterns add another check, so products are not judged on sales alone.

**Use it to:** find products to grow, products that may need a pricing or cost review, and products that deserve attention because of their return patterns.

## Business Questions This Project Brings Together

| Business question | Where to look | What to check next |
|---|---|---|
| Are sales and profit moving together? | Overview and Product Analysis | Compare sales trends with product gross profit and product groups. |
| Where are potential buyers leaving? | Funnel Analysis | Compare stage drop-off, device groups, and time between actions. |
| Which return reasons appear most often? | Returns | Compare reasons across product groups and customer segments. |
| How much value is awaiting return decisions? | Returns | Review pending refund exposure alongside adjusted approved refund value. |
| Which products may need a closer review? | Product Analysis | Compare profit, sales, and return patterns before deciding on a change. |

## How the Main Measures Are Calculated

| Measure | Definition used in the project |
|---|---|
| **Net merchandise sales** | Transaction subtotal minus discounts. Tax and shipping are excluded, and refunds are not subtracted from this figure. |
| **Product gross profit** | Net merchandise sales allocated to each product, minus product cost multiplied by quantity sold. |
| **Visit-to-purchase conversion** | Purchase sessions divided by visit sessions. |
| **Stage drop-off** | Sessions reaching a stage but not the next stage, divided by sessions reaching the earlier stage. For checkout, this is checkout-start sessions without a purchase divided by checkout-start sessions. |
| **Return-request unit rate** | Requested return units across request statuses divided by units sold. |
| **Adjusted approved refund value** | Discounted merchandise value for approved return units. |
| **Pending refund exposure** | Discounted merchandise value associated with pending return units. |

The calculations keep sales before refunds separate from refund measures, and distinguish order counts from item quantities.

## Data Checks

The current validation run confirmed that transaction sales totals reconcile with order-item line totals, order quantities reconcile with item quantities, and the checked event, order, item, and product identifiers have no duplicates. The return checks also flagged **18 duplicated return IDs** and **18 return rows without a matching order-item record**. Those return-record issues are marked for review and should be kept in mind when examining individual return records.

## Insight Engine

The Insight Engine applies set rules to highlight patterns worth checking. Depending on the page, it can flag large funnel drop-offs, gaps between device groups, delays between actions, changes in return activity, weak product profit, or sales declines.

The purpose is to point users toward the next useful question. An alert is not proof of cause; any business change should be checked against the details behind the finding.

## Tools Used

- **Python** - application logic and business calculations
- **Pandas** - data preparation and analysis
- **Plotly** - interactive charts
- **Streamlit** - dashboard pages and live deployment
- **Git and GitHub** - version control

## Run Locally

```bash
git clone https://github.com/build-by-Ayush/Intelligent-Business-Analytics-and-Funnel-Optimization-Platform.git
cd Intelligent-Business-Analytics-and-Funnel-Optimization-Platform
pip install -r requirements.txt
streamlit run app.py
```

## Repository Layout

```text
app.py                  # Overview page
pages/
  1_Funnel.py           # Customer funnel analysis
  2_Returns.py          # Return and refund analysis
  3_Products.py         # Product performance analysis
src/
  data_loader.py        # Shared loading and date handling
  metrics.py            # Shared business calculations
  navigation.py         # Shared page navigation
Images/                 # Dashboard screenshots
```

## Project Outcome

The platform brings the buying journey and what happens after purchase into one place. A business user can start with overall performance, locate customer drop-off, review return exposure, and examine product sales and profit. It connects the questions **“What happened?”**, **“Where did we lose potential buyers?”**, and **“Which products need attention?”** in one application.