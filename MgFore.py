from prophet import Prophet
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import os
from pymongo import MongoClient

def run_forecast_mongo(mongo_uri, db_name, product_id, output_dir="forecast_outputs"):
    # Connect to MongoDB
    client = MongoClient(mongo_uri)
    db = client[db_name]
    supply_data = db['supply_data']

    # Load data from MongoDB for specific product_id
    cursor = supply_data.find({"product_id": product_id}, {"_id": 0, "date": 1, "units_sold": 1})
    df = pd.DataFrame(list(cursor))

    if df.empty:
        raise Exception("No data found for the given product_id.")

    df.rename(columns={'date': 'ds', 'units_sold': 'y'}, inplace=True)
    df['ds'] = pd.to_datetime(df['ds'])

    # Forecasting using Prophet
    model = Prophet()
    model.fit(df)

    future = model.make_future_dataframe(periods=30)
    forecast = model.predict(future)

    # Merge predictions with actuals for metrics
    df_merged = pd.merge(df, forecast[['ds', 'yhat']], on='ds', how='left').dropna()
    mae = mean_absolute_error(df_merged['y'], df_merged['yhat'])
    mse = mean_squared_error(df_merged['y'], df_merged['yhat'])
    r2 = r2_score(df_merged['y'], df_merged['yhat'])

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Line Chart
    plt.figure(figsize=(10, 5))
    plt.plot(df_merged['ds'], df_merged['y'], label='Actual', marker='o')
    plt.plot(df_merged['ds'], df_merged['yhat'], label='Predicted', linestyle='--', marker='x')
    plt.title(f'Forecast for {product_id}')
    plt.xlabel('Date')
    plt.ylabel('Units Sold')
    plt.legend()
    line_path = os.path.join(output_dir, f"{product_id}_line_chart.png")
    plt.savefig(line_path)
    plt.close()

    # Bar Chart
    plt.figure(figsize=(6, 4))
    plt.bar(['MAE', 'MSE', 'R²'], [mae, mse, r2], color=['blue', 'orange', 'green'])
    plt.title('Forecast Accuracy Metrics')
    bar_path = os.path.join(output_dir, f"{product_id}_bar_chart.png")
    plt.savefig(bar_path)
    plt.close()

    # Heatmap from all data
    df_all = pd.DataFrame(list(supply_data.find({}, {"_id": 0})))
    numeric_data = df_all.select_dtypes(include=[np.number])
    plt.figure(figsize=(8, 6))
    sns.heatmap(numeric_data.corr(), annot=True, cmap='coolwarm', fmt=".2f")
    plt.title('Feature Correlation Heatmap')
    heatmap_path = os.path.join(output_dir, f"{product_id}_heatmap.png")
    plt.savefig(heatmap_path)
    plt.close()

    # Store forecast results in MongoDB
    forecast_data = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_dict(orient='records')
    db.forecast_results.delete_many({'product_id': product_id})
    for record in forecast_data:
        record['product_id'] = product_id
    db.forecast_results.insert_many(forecast_data)

    # Store metrics
    db.forecast_metrics.delete_many({'product_id': product_id})
    db.forecast_metrics.insert_one({
        'product_id': product_id,
        'mae': mae,
        'mse': mse,
        'r2_score': r2
    })

    client.close()

    return {
        "forecast": forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']],
        "metrics": {
            "mae": mae,
            "mse": mse,
            "r2_score": r2
        },
        "graphs": {
            "line_chart": line_path,
            "bar_chart": bar_path,
            "heatmap": heatmap_path
        }
    }
