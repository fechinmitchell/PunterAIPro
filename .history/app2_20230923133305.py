import os
from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import openai
import xml.etree.ElementTree as ET
import json

app = Flask(__name__, static_url_path='/static')

# Initialize OpenAI API
openai.api_key = os.environ.get('OPENAI_API_KEY')  # Fetch the API key from environment variable

predictions_db = {}  # This dictionary will act as a simple database

# Function to make predictions with GPT-4
def predict_horse_winners(df, race_info):
    readable_df = df.to_string()
    race_details = f"Race ID: {race_info['id']}, Name: {race_info['name']}, Distance: {race_info['distance']}, Class: {race_info['class']}, Total Prize: {race_info['totalprize']}"

    # Use the chat-based API
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a skilled AI trained to analyze horse racing data and predict winners."
            },
            {
                "role": "user",
                "content": f"{race_details}\nHere's the data for the upcoming race:\n{readable_df}"
            },
            {
                "role": "assistant",
                "content": "Please analyze it and give your top pick along with a detailed summary."
            }
        ]
    )

    return response['choices'][0]['message']['content']

@app.route('/api/predict', methods=['POST'])
def predict():
    # ... existing code ...

    return jsonify(all_predictions)

@app.route('/api/save', methods=['POST'])
def save_prediction():
    data = request.json
    predictions_db[data['id']] = {"name": data['name'], "data": data['data']}
    return jsonify({'message': 'Prediction saved successfully!'})

@app.route('/api/get_predictions', methods=['GET'])
def get_saved_predictions():
    return jsonify(predictions_db)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
