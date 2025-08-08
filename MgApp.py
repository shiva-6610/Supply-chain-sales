from flask import Flask, request, jsonify, send_from_directory
import os
import pandas as pd
from mongodb_utils import insert_data_from_csv_to_mongo,init_mongo_db
from MgFore import run_forecast_mongo
from flask_cors import CORS 

app = Flask(__name__)
UPLOAD_FOLDER = 'uploaddatas'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
CORS(app)
db = "SupplyDB"
collection = "supply_data"
init_mongo_db(db,collection)

@app.route('/')
def home():
    return jsonify({'message': 'Flask API Program with MongoDB'})

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
        db = "SupplyDB"
        collection = "supply_data"
        insert_data_from_csv_to_mongo(db,collection,filepath)
        return jsonify({'message': 'File uploaded and data stored in MongoDB successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/forecast', methods=['POST'])
def forecast():
    try:
        data = request.get_json()
        product_id = data.get('product_id')

        if not product_id:
            return jsonify({"error": "Missing 'product_id' in request"}), 400
        mongo_uri="mongodb://localhost:27017/"
        db_name="SupplyDB"
        result = run_forecast_mongo(mongo_uri,db_name,product_id)

        return jsonify({
            "metrics": result["metrics"],
            "graphs": result["graphs"]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
