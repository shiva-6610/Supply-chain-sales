# pip install prophet
from prophet import Prophet
import pandas as pd
import sqlite3
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def run_forecast(db_name, product_id, output_dir="forecast_outputs"):
    conn = sqlite3.connect(db_name)
    query = """
        SELECT date, units_sold 
        FROM supply_data 
        WHERE product_id = ?
        ORDER BY date
    """
    df = pd.read_sql(query, conn, params=(product_id,))
    
    if df.empty:
        conn.close()
        raise Exception("No data found for the given product_id.")
    
    df.rename(columns={'date': 'ds', 'units_sold': 'y'}, inplace=True)
    df['ds'] = pd.to_datetime(df['ds'])

    model = Prophet()
    model.fit(df)

    future = model.make_future_dataframe(periods=30)
    forecast = model.predict(future)


    df_merged = pd.merge(df, forecast[['ds', 'yhat']], on='ds', how='left').dropna()


    mae = mean_absolute_error(df_merged['y'], df_merged['yhat'])
    mse = mean_squared_error(df_merged['y'], df_merged['yhat'])
    r2 = r2_score(df_merged['y'], df_merged['yhat'])

    os.makedirs(output_dir, exist_ok=True)

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

    plt.figure(figsize=(6, 4))
    plt.bar(['MAE', 'MSE', 'R²'], [mae, mse, r2], color=['blue', 'orange', 'green'])
    plt.title('Forecast Accuracy Metrics')
    bar_path = os.path.join(output_dir, f"{product_id}_bar_chart.png")
    plt.savefig(bar_path)
    plt.close()

    df_all = pd.read_sql("SELECT * FROM supply_data", conn)
    numeric_data = df_all.select_dtypes(include=[np.number])
    plt.figure(figsize=(8, 6))
    sns.heatmap(numeric_data.corr(), annot=True, cmap='coolwarm', fmt=".2f")
    plt.title('Feature Correlation Heatmap')
    heatmap_path = os.path.join(output_dir, f"{product_id}_heatmap.png")
    plt.savefig(heatmap_path)
    plt.close()

    forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_sql(
        'forecast_results', conn, if_exists='replace', index=False
    )

    metrics_df = pd.DataFrame([{
        'product_id': product_id,
        'mae': mae,
        'mse': mse,
        'r2_score': r2
    }])
    metrics_df.to_sql('forecast_metrics', conn, if_exists='replace', index=False)

    conn.close()

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




