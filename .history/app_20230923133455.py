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
    uploaded_file = request.files['file']

    if uploaded_file.filename != '':
        uploaded_file.save(uploaded_file.filename)
        xml_file_path = uploaded_file.filename

        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
        except FileNotFoundError:
            return jsonify({'error': f"File not found at {xml_file_path}"})
        except ET.ParseError:
            return jsonify({'error': "Error parsing the XML file. Please check its format."})

        all_predictions = []

        # Extract race and horse information for each race
        for race in root.findall('.//race'):
            race_info = {
                'id': race.attrib['id'],
                'name': race.attrib['name'],
                'distance': race.attrib['distance'],
                'class': race.attrib['class'],
                'totalprize': race.attrib['totalprize'],
                'nominations': []
            }

            nominations = []
            for nom in race.findall('.//nomination'):
                nomination = {
                    'number': nom.attrib.get('number', 'Unknown'),
                    'horse': nom.attrib.get('horse', 'Unknown'),
                    'trainer': nom.attrib.get('rsbtrainername', 'Unknown'),
                    'jockey': f"{nom.attrib.get('jockeyfirstname', 'Unknown')} {nom.attrib.get('jockeysurname', 'Unknown')}",
                    'barrier': nom.attrib.get('barrier', 'Unknown'),
                    'weight': nom.attrib.get('weight', 'Unknown'),
                    'rating': nom.attrib.get('rating', 'Unknown'),
                    'career': nom.attrib.get('career', 'Unknown'),
                    'thistrack': nom.attrib.get('thistrack', 'Unknown'),
                    'thisdistance': nom.attrib.get('thisdistance', 'Unknown'),
                    'goodtrack': nom.attrib.get('goodtrack', 'Unknown'),
                    'heavytrack': nom.attrib.get('heavytrack', 'Unknown')
                }
                nominations.append(nomination)

            # Convert to DataFrame
            df = pd.DataFrame(nominations)

            # Use OpenAI API to predict top pick and generate summary for the race
            prediction = predict_horse_winners(df, race_info)

            all_predictions.append({
                'race_id': race_info['id'],
                'race_name': race_info['name'],
                'prediction': prediction
            })

        return jsonify(all_predictions)

    return jsonify({'error': 'No file uploaded'})

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




