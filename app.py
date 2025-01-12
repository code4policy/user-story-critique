import os
import json
from flask import Flask, render_template, request, jsonify
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import logging
import requests

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Move static files to static folder
app.static_folder = 'static'
app.template_folder = 'templates'

# Print service account email for setup
service_account_email = os.environ.get('GOOGLE_CLIENT_EMAIL')
logger.info(f"To enable Google Sheets integration, please share your Google Sheet with this email: {service_account_email}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_story():
    try:
        data = request.json
        api_key = data.get('apiKey')
        user_story = data.get('userStory')
        definition_of_done = data.get('definitionOfDone')

        # Load prompts
        with open('static/prompts.json', 'r') as f:
            prompts = json.load(f)

        feedback = []
        for prompt in prompts:
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}'
                },
                json={
                    'model': "gpt-4-turbo-preview",
                    'messages': [
                        {
                            'role': "system",
                            'content': "You are an expert in agile methodologies and user story writing. Provide specific, actionable feedback."
                        },
                        {
                            'role': "user",
                            'content': f"User Story: {user_story}\nDefinition of Done: {definition_of_done}\n\n{prompt['prompt']}"
                        }
                    ],
                    'temperature': 0.7,
                    'max_tokens': 1000
                }
            )

            if not response.ok:
                error = response.json()
                raise Exception(error.get('error', {}).get('message', 'Failed to get feedback'))

            result = response.json()
            feedback.append({
                'title': prompt['title'],
                'content': result['choices'][0]['message']['content']
            })

        # Save to Google Sheets
        row = [datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_story, definition_of_done]
        for item in feedback:
            row.extend([item['title'], item['content']])

        append_to_sheet(row)

        return jsonify({"success": True, "feedback": feedback})

    except Exception as e:
        error_message = str(e)
        if "The caller does not have permission" in error_message:
            error_message = f"Permission denied. Please share the Google Sheet with this service account email: {service_account_email}"
        logger.error(f"Error analyzing story: {error_message}", exc_info=True)
        return jsonify({"success": False, "message": error_message}), 500

def append_to_sheet(row):
    """Append a row to the Google Sheet"""
    try:
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        SPREADSHEET_ID = os.environ.get('GOOGLE_SHEET_ID')

        # Load credentials from environment
        creds_info = {
            "type": "service_account",
            "project_id": os.environ.get('GOOGLE_PROJECT_ID'),
            "private_key_id": os.environ.get('GOOGLE_PRIVATE_KEY_ID'),
            "private_key": os.environ.get('GOOGLE_PRIVATE_KEY', '').replace('\\n', '\n'),
            "client_email": os.environ.get('GOOGLE_CLIENT_EMAIL'),
            "client_id": os.environ.get('GOOGLE_CLIENT_ID'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.environ.get('GOOGLE_CLIENT_CERT_URL')
        }

        logger.debug("Initializing Google Sheets credentials")
        credentials = service_account.Credentials.from_service_account_info(
            creds_info, scopes=SCOPES)

        service = build('sheets', 'v4', credentials=credentials)
        sheet = service.spreadsheets()

        # First, try to get the spreadsheet to verify permissions
        sheet.get(spreadsheetId=SPREADSHEET_ID).execute()

        range_name = 'Sheet1!A:Z'  # Adjust based on your sheet structure
        value_input_option = 'USER_ENTERED'
        insert_data_option = 'INSERT_ROWS'

        value_range_body = {
            'values': [row]
        }

        logger.debug(f"Attempting to append data to sheet: {SPREADSHEET_ID}")
        request = sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption=value_input_option,
            insertDataOption=insert_data_option,
            body=value_range_body
        )
        response = request.execute()
        logger.debug(f"Successfully appended data to sheet: {response}")

        return response

    except Exception as e:
        logger.error(f"Error in append_to_sheet: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)