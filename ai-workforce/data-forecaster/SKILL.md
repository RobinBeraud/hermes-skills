---
name: data-forecaster
description: Forecast a metric from its history (sales, sign-ups, tickets, cash) with a dependency-free Python script that backtests five simple methods, keeps the most accurate one and gives an 80% range. Use when you need a defensible "what next quarter looks like", not a single magic number.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [forecasting, time-series, prediction, planning, backtesting, csv, ai-workforce]
    category: ai-workforce
    requires_toolsets: [terminal]
    related_skills: [data-visualizer, anomaly-detector, digital-simulation, trend-watcher]
---

# Data Forecaster

The Data Forecaster predicts future values from historical data, and is honest about how sure it is. Instead of trusting one model, it hides the last few periods, checks which method would have predicted them best, then forecasts with that method and an interval built from its real past errors.

## When to use

- Budget, hiring or stock planning needs a forecast for the next months.
- You want to know whether a target is realistic given the trend and the seasonality.
- A manager asks "when will we reach X?" and you want a range, not a promise.

## How the agent works

1. **Clarify the decision** the forecast serves and the horizon. Forecast what you can act on (weekly tickets for staffing, monthly revenue for budget).
2. **Load and aggregate** the CSV to day, week or month. Missing periods become zero; the agent reports them.
3. **Backtest** on the last `horizon` points: naive (last value), seasonal naive (same period last cycle), seasonal naive with drift (last cycle plus the average year-on-year change), linear trend, Holt smoothing. The lowest mean absolute error wins.
4. **Forecast** with the winner, with an 80% range from backtest errors.
5. **Explain** in plain words: method kept and why, accuracy in % of actuals, the range, and what would make the forecast wrong (a price change, a new channel, a one-off event). Chart history and forecast with `data-visualizer`.

## Usage

```bash
python3 scripts/forecast.py examples/monthly_sales.csv --date-col date --value-col sales --period month --horizon 6
python3 scripts/forecast.py tickets.csv --date-col created_at --value-col count --period week --horizon 8 --season 52 --json
```

Example output on the bundled file:

```
Method kept: seasonal_drift (backtest MAE 10.83, ~0.7% of actuals)
Backtest MAE by method: seasonal_drift 10.83, seasonal_naive 130.0, linear_trend 180.08, naive 470.0, holt 566.94

| month | forecast | 80% interval |
|---|---|---|
| 2026-07-01 | 1521.67 | 1504.17 to 1539.17 |
| 2026-08-01 | 1281.67 | 1264.17 to 1299.17 |
...
```

## Documented use cases

### 1. Staffing the support team
- **Ask Hermes:** "data-forecaster: weekly tickets for the next 8 weeks from tickets.csv, then how many agents we need at 60 tickets per agent per week."
- **What you get:** a weekly forecast with ranges, the staffing number for the median and for the top of the range, and a warning if the backtest error is high.

### 2. Is the annual target realistic?
- **Ask Hermes:** "We need 22k revenue in December. Forecast from the last 30 months and tell me the probability we get there."
- **What you get:** the December forecast and range, and a plain statement ("22k is above the top of the 80% range: it needs something new, not the current trend"). For a real probability, the agent hands over to `digital-simulation`.

### 3. Cash runway
- **Ask Hermes:** "Forecast monthly net cash burn for 6 months and tell me the month cash drops below 20k."
- **What you get:** burn forecast, cumulative cash per month, and the earliest and latest month across the range.

## Limits

- Simple methods on one series. No external drivers (price, marketing spend, weather): model those with `digital-simulation`.
- At least `horizon + 3` periods are required; two full seasons are needed for the seasonal drift method.
- The interval reflects backtest errors only; structural breaks (new product, crisis) are not in the data.

## Testing

`tests/test_ai_workforce.py` checks the backtest picks the seasonal method on the bundled seasonal series and that every interval contains its forecast. Tested locally with Python 3.12 on 2026-11-10.

## Works well with

`anomaly-detector` to remove one-off spikes before forecasting, `data-visualizer` to chart it, `digital-simulation` for what-if scenarios, `trend-watcher` to see what is changing behind the numbers.
