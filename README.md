# 💱📈 Currency Forecasting and Economic Indicators using BigQuery ML

## 📌 Project Description

This project demonstrates how to build and evaluate machine learning models in **Google BigQuery ML** to forecast financial metrics and uncover correlations between economic indicators. We collect, clean, and analyze exchange rate, gold price, and weather data using a fully integrated **Google Cloud Platform (GCP)** pipeline. Three main models are trained to forecast trends and identify cross-variable relationships.

---

## 🔍 Overview

We developed the following models using **BigQuery ML**:

* **`fx_arima`**: An ARIMA model used to forecast foreign exchange (FX) currency rates.
* **`gold_temp_reg`**: A linear regression model predicting gold prices based on daily temperature in Warsaw.
* **`usd_euro_arima_model`**: A regression model trained to quantify the influence of USD and EUR on other currencies. While we don’t use it for direct prediction, we analyze its learned weights to study cross-currency correlation.

---

## 🛠️ Methodology

### 🔗 Data Integration & Infrastructure

We collected data from the **Polish National Bank (NBP)** and **Open-Meteo** APIs using **Python scripts deployed in Cloud Run**. The processed data is stored in BigQuery and visualized in **Looker Studio** with **BI Engine** acceleration. All components (besides the APIs) are part of the Google Cloud ecosystem, providing seamless integration.

* 🔗 [BigQuery Project](https://console.cloud.google.com/bigquery?authuser=1&inv=1&invt=Aby-gw&project=nbpcurrencyratesbdfinalproject)
* 🗂️ [Trello Project Board](https://trello.com/b/uzcKV8q8/big-data)

---

## 🌐 Data Collection

Data is gathered through scheduled scripts in Cloud Run, using the `google.cloud` Python package to write directly into BigQuery.

### 🌡️ Weather Data

* Source: [Open-Meteo](https://open-meteo.com/en/docs)
* Location: Warsaw (`latitude=52.23`, `longitude=21.01`)
* Metric: Hourly average temperature (`temperature_2m`)
* Range: `2015-01-01` to present
* Table: `nbp_data_raw.weather_warsaw_raw`
* Script: `weatherwarsawfetchscript`

### 💱 Currency and Gold Prices

* Source: National Bank of Poland (NBP)
* Automatically fetched and written to:

  * `nbp_data.fx_history`
  * `nbp_data.fx_today`
  * `nbp_data.gold_history`

---

## 🧹 Data Cleaning

Minimal preprocessing was required. The `rawintoclean` function cleaned and sorted the datasets for consistency. Final cleaned tables include:

* `nbp_data.fx_history`
* `nbp_data.fx_today`
* `nbp_data.gold_history`
* `nbp_data.weather_warsaw`

### 📁 Intermediate Views

* **`nbp_data.gold_temp_daily`**: Joins daily temperature with gold prices for regression training.
* **`nbp_data.weather_daily_avg`**: Aggregates hourly temperatures into daily averages.
* **`nbp_data.fx_pct_returns_clean`**: Computes daily percentage returns for currency exchange rates.

---

## 🤖 Model Training

### 🔹 Gold Price Prediction — Linear Regression

Predicts gold prices using daily average temperature in Warsaw.

```sql
CREATE OR REPLACE MODEL
  nbpcurrencyratesbdfinalproject.nbp_data_models.gold_temp_reg_model
OPTIONS(
  model_type       = 'linear_reg',
  input_label_cols = ['gold_pln']
) AS

SELECT
  avg_temp,
  gold_pln
FROM
  nbpcurrencyratesbdfinalproject.nbp_data.gold_temp_daily;
```

---

### 🔹 Currency Forecasting — ARIMA Model

Forecasts currency exchange rates using time series modeling.

```sql
CREATE OR REPLACE MODEL nbpcurrencyratesbdfinalproject.nbp_data_models.fx_arima_model
OPTIONS(
  model_type='ARIMA_PLUS',
  time_series_timestamp_col='effective_date',
  time_series_data_col='mid',
  auto_arima=true,
  holiday_region='PL'
) AS
SELECT
  effective_date,
  mid
FROM nbpcurrencyratesbdfinalproject.nbp_data.fx_history
WHERE mid IS NOT NULL
ORDER BY effective_date;
```

---

### 🔹 Currency Correlation — Linear Regression

Analyzes the influence of USD and EUR on other currencies. The model is not used for forecasting, only to inspect weight coefficients.

```sql
CREATE OR REPLACE MODEL
  nbpcurrencyratesbdfinalproject.nbp_data_models.usd_euro_arima_domel
OPTIONS(
  model_type       = 'linear_reg',
  input_label_cols = ['label']
) AS

WITH base AS (
  ...
)

SELECT
  pct_return AS label,
  ...
FROM
  base;
```

---

## 📈 Evaluation

### 🔬 Forecasting Accuracy

* Predictions are generated using `arimaforecastmodel` and `automatitempgoldmodel` functions.
* Accuracy is validated against historical data.

### 🔄 Correlation Analysis (Model Weights)

* The USD/EUR model's weights reveal the strength of influence each currency has on others.
* Extracted and analyzed via `automateusdandeuro`.

### 📊 Correlation Analysis (Statistics)

* Traditional metrics (CORR and COVAR\_POP) are also computed by `automateusdandeuro` to compare with the ML model.

---

## 📊 Visualization Dashboards

Visualizations were created in **Looker Studio** with BigQuery's BI Engine for real-time rendering:

* **Gold-Temperature Regression**: [View Report](https://lookerstudio.google.com/reporting/041cbbbb-aa2b-404f-8d19-70d5d2996a1e)
* **ARIMA FX Forecasting**: [View Report](https://lookerstudio.google.com/reporting/594abe36-34f3-47ea-9fc6-c36573f43415)
* **Currency Correlation Analysis**: [View Report](https://lookerstudio.google.com/reporting/28bb2adc-945a-49ae-9023-74db97ca15c5)

---

## ✅ Results & Conclusions

* The **gold vs. temperature** linear regression model shows moderate predictive power. However, due to temperature's seasonal nature, its correlation with date makes it unclear whether it is temperature or time driving the prediction.

* The **ARIMA currency forecasting** model provides consistent short-term forecasts, indicating the presence of underlying trends and temporal stability in FX rates.

* The **currency correlation analysis** found that:

  * **48%** of examined currencies are significantly correlated with **USD**
  * **27%** show significant correlation with **EUR**
  * Model weight analysis supports this, showing, for example:

    * **CZK** is **12×** more influenced by EUR than USD
    * **HUF** is **4×** more influenced by EUR
    * **GBP** leans **1.6×** more toward EUR
    * **CAD** is **2.5×** more correlated with USD

---
