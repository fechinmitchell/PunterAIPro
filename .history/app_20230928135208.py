import os
from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import openai
import xml.etree.ElementTree as ET
import json
import shutil

app = Flask(__name__, static_url_path='/static')

# Initialize OpenAI API
openai.api_key = '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'

predictions_db = {}

def predict_horse_winners(df, race_info):
    readable_df = df.to_string()
    race_details = f"Race ID: {race_info['id']}, Name: {race_info['name']}, Distance: {race_info['distance']}, Class: {race_info['class']}, Total Prize: {race_info['totalprize']}"

    try:
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
    except Exception as e:
        return f"An error occurred: {e}"


@app.route('/api/predict', methods=['POST'])
def predict():
    uploaded_file = request.files['file']
    rename_file = request.form.get('rename', None)

    if uploaded_file.filename != '':
        original_filename = uploaded_file.filename
        uploaded_file.save(original_filename)

        if rename_file:
            renamed_file_path = f"{rename_file}.xml"
            shutil.move(original_filename, renamed_file_path)
            xml_file_path = renamed_file_path
        else:
            xml_file_path = original_filename

        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
        except Exception as e:
            return jsonify({'error': str(e)})

        all_predictions = []

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

            df = pd.DataFrame(nominations)
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
    app.run(debug=True, port=5000)




