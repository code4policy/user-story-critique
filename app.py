from flask import Flask, render_template, request, jsonify
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

app = Flask(__name__)

# Move static files to static folder
app.static_folder = 'static'
app.template_folder = 'templates'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save-feedback', methods=['POST'])
def save_feedback():
    try:
        data = request.json
        
        # Extract data from the request
        user_story = data.get('userStory')
        definition_of_done = data.get('definitionOfDone')
        feedback = data.get('feedback')
        
        # Prepare row data
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        row = [timestamp, user_story, definition_of_done]
        
        # Add each feedback item
        for item in feedback:
            row.extend([item['title'], item['content']])
            
        # Save to Google Sheets
        result = append_to_sheet(row)
        
        return jsonify({"success": True, "message": "Feedback saved successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

def append_to_sheet(row):
    """Append a row to the Google Sheet"""
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    SPREADSHEET_ID = os.environ.get('GOOGLE_SHEET_ID')
    
    # Load credentials from environment
    creds_info = {
        "type": "service_account",
        "project_id": os.environ.get('GOOGLE_PROJECT_ID'),
        "private_key_id": os.environ.get('GOOGLE_PRIVATE_KEY_ID'),
        "private_key": os.environ.get('GOOGLE_PRIVATE_KEY').replace('\\n', '\n'),
        "client_email": os.environ.get('GOOGLE_CLIENT_EMAIL'),
        "client_id": os.environ.get('GOOGLE_CLIENT_ID'),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.environ.get('GOOGLE_CLIENT_CERT_URL')
    }
    
    credentials = service_account.Credentials.from_service_account_info(
        creds_info, scopes=SCOPES)
    
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()
    
    range_name = 'Sheet1!A:Z'  # Adjust based on your sheet structure
    value_input_option = 'USER_ENTERED'
    insert_data_option = 'INSERT_ROWS'
    
    value_range_body = {
        'values': [row]
    }
    
    request = sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption=value_input_option,
        insertDataOption=insert_data_option,
        body=value_range_body
    )
    response = request.execute()
    
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
