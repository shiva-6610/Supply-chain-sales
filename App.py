from flask import Flask, request, jsonify,send_from_directory
import os
import pandas as pd
from db_utils import init_db, insert_data_from_csv
from forecast import run_forecast
from flask_cors import CORS 

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
CORS(app)
DB_NAME = 'Supply.db'

init_db(DB_NAME)

@app.route('/')
def home():
    return jsonify({'message': 'Flak Api Program'})

OUTPUT_FOLDER = os.path.join(os.getcwd(), "forecast_outputs")

@app.route('/forecast_outputs/<path:filename>')
def serve_output(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

@app.route('/upload', methods=['POST'])
def upload_dataset():
    if 'file' not in request.files:
        return jsonify({'error': 'CSV file is missing'}), 400

    file = request.files['file']
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    try:
        insert_data_from_csv(DB_NAME, filepath)
        return jsonify({'message': 'File uploaded and data stored successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/forecast', methods=['POST'])
def forecast():
    try:
        data = request.get_json()
        product_id = data.get('product_id')

        if not product_id:
            return jsonify({"error": "Missing 'product_id' in request"}), 400

        result = run_forecast(DB_NAME, product_id)
        
        return jsonify({
            "metrics": result["metrics"],
            "graphs": result["graphs"]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
