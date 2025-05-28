# 📊 NBP Currency & Gold Forecasting — Big Data Final Project

## 🔍 Overview

This project focuses on analyzing and forecasting financial time series — specifically, **currency exchange rates** and **gold prices in PLN** — while evaluating the **influence of environmental factors such as daily temperatures in Warsaw**.
We use **BigQuery ML** to build two machine learning models:

- `fx_arima`: An ARIMA model for forecasting currency exchange rates.
- `gold_temp_reg`: A linear regression model to predict gold prices based on weather data.

---

## 🛠️ Methodology

Data was collected from public APIs provided by the Polish National Bank (NBP) and Open-Meteo. All storage and processing were performed in the **BigQuery environment**, while results were visualized using **BI Engine** and **Looker Studio**. Except for the initial API sources, all tools used are Google Cloud services, allowing seamless integration across the data pipeline.

### 📥 Data Ingestion

We began by extracting data from the APIs and uploading it to BigQuery.

#### 💱 Exchange Rates

The [`fetch_exchange_rates.py`](scripts/fetch_exchange_rates.py) script retrieves historical exchange rates from 2015 to the present via the [NBP API](https://api.nbp.pl/en.html). The data is uploaded to BigQuery under the table `nbp_data_raw.fx_history`.

#### 🪙 Gold Prices

The [`fetch_gold_history.py`](scripts/fetch_gold_history.py) script fetches gold prices for the same period and uploads them to `nbp_data_raw.gold_history_raw`.

#### 🌡️ Weather Data

Weather data for Warsaw (2015–2025) was manually downloaded from [Open-Meteo](https://open-meteo.com/en/docs) and uploaded to `nbp_data_raw.weather_warsaw_raw` (TODO: Automate this process via a script).

API configuration:

- Date range: `2015-01-01` to `today`
- Location: `latitude=52.23`, `longitude=21.01` (Warsaw)
- Metric: Daily average temperature (`temperature_2m_mean`)
- Format: CSV
- EU-hosted → No cross-region charges

### 🧹 Data Cleaning

Most datasets were clean and required minimal preprocessing.

- **Exchange and gold price data:** Only required sorting by date for easier inspection and modeling. Cleaned versions are stored as:

  - `nbp_data.fx_history`
  - `nbp_data.fx_today`
  - `nbp_data.gold_history`

- **Weather data:** Required aggregation from hourly to daily averages. We also converted timestamps to date format, removed null entries, and sorted the data. The cleaned version is saved as `nbp_data.weather_warsaw`.

### 🧾 Intermediate Tables

We created a combined view `nbp_data.gold_temp` (TODO: Rename for clarity) to serve as training data for the regression model. It joins gold price and temperature by date:

```sql
SELECT
  g.effective_date,
  g.price        AS gold_pln,
  w.avg_celsius
FROM   nbp_data.gold_history g
JOIN   nbp_data.weather_warsaw w
USING  (effective_date)
WHERE  g.price IS NOT NULL
  AND  w.avg_celsius IS NOT NULL
```

### 🤖 Model Training

#### Linear Regression — Gold vs. Temperature

```sql
CREATE OR REPLACE MODEL nbpcurrencyratesbdfinalproject.nbp_data_models.gold_temp_reg_model
OPTIONS (
  model_type='linear_reg',
  input_label_cols=['gold_pln'],
  data_split_method='NO_SPLIT'
) AS
SELECT
  avg_celsius,
  gold_pln
FROM nbpcurrencyratesbdfinalproject.nbp_data.gold_temp
WHERE gold_pln IS NOT NULL AND avg_celsius IS NOT NULL;
```

#### ARIMA — Currency Forecasting

```sql
CREATE OR REPLACE MODEL nbpcurrencyratesbdfinalproject.nbp_data_models.fx_arima_model
OPTIONS (
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

### 📈 Evaluation

Predictions were generated from both models for evaluation.

#### Predicting Gold Price

```sql
CREATE OR REPLACE TABLE nbpcurrencyratesbdfinalproject.nbp_data_models.gold_temp_predictions AS
SELECT
  avg_celsius,
  gold_pln,
  predicted_gold_pln
FROM ML.PREDICT(
  MODEL nbpcurrencyratesbdfinalproject.nbp_data_models.gold_temp_reg_model,
  (
    SELECT
      avg_celsius,
      gold_pln
    FROM nbpcurrencyratesbdfinalproject.nbp_data.gold_temp
    WHERE gold_pln IS NOT NULL AND avg_celsius IS NOT NULL
  )
);
```

#### Forecasting Exchange Rates

```sql
CREATE OR REPLACE TABLE nbpcurrencyratesbdfinalproject.nbp_data_models.fx_arima_forecast AS
SELECT *
FROM ML.FORECAST(
  MODEL nbpcurrencyratesbdfinalproject.nbp_data_models.fx_arima_model,
  STRUCT(30 AS horizon) -- 30-day forecast
);
```

### 📊 Visualization

The behavior and accuracy of both models are visualized in **Looker Studio**, with **BI Engine** enabling faster data processing.

- 📈 **Linear Regression Model Report**: [View Report](https://lookerstudio.google.com/reporting/497d4408-2666-422f-98af-ea6c3e93e39c)
- 📉 **ARIMA Model Report**: [View Report](https://lookerstudio.google.com/reporting/594abe36-34f3-47ea-9fc6-c36573f43415)

---

## 🧪 Reproducing Results

1. Ensure Python is installed.
2. Clone the repository.
3. Install dependencies with:

   ```bash
   pip install -r /path/to/requirements.txt
   ```

4. Follow the steps in the [Methodology](#%EF%B8%8F-methodology) section.
   **Note:** A Google BigQuery account is required.

---

## 📌 Results and Conclusions

TODO: Discuss and draw conclusions from the visualization results.
