import datetime
import json
from flask import Flask, render_template, request, redirect, session
from intuitlib.client import AuthClient
from intuitlib.enums import Scopes

import os
from dotenv import load_dotenv
from quickbooks import QuickBooks
from quickbooks.objects.invoice import Invoice


app = Flask(__name__)
app.secret_key = 'your secret key'

# Load the stored environment variables
load_dotenv()

auth_client = AuthClient(
    client_id     = os.getenv("CLIENT_ID"),
    client_secret = os.getenv("CLIENT_SECRET"),
    environment   = os.getenv("ENVIRONMENT"),
    redirect_uri  = os.getenv("REDIRECT_URI"),    
)

realm_id = os.getenv("REALM_ID")

@app.route('/')
def index():        
    return render_template('index.html')

@app.route('/login')
def login():
    url = auth_client.get_authorization_url([Scopes.ACCOUNTING])
    return redirect(url)

@app.route('/test')
def test():
    refresh_token = session.get('refresh_token')
    access_token = session.get('access_token')
    
    print(refresh_token)
    print(access_token)
    print(realm_id)
    return auth_client.access_token

@app.route('/callback')
def callback():
    auth_code = request.args.get('code')
    auth_client.get_bearer_token(auth_code, realm_id=realm_id)

    # Store the access token, refresh token, and token expiration time in session
    session['access_token'] = auth_client.access_token  
    session['refresh_token'] = auth_client.refresh_token
    # session['token_expires_at'] = auth_client.token_expires_at
    # print(auth_client.access_token)

    client = QuickBooks(
        auth_client=auth_client,
        refresh_token=auth_client.refresh_token,
        company_id='9130357842152386'
    )

    invoice_number = '1010'
    invoices = Invoice.filter(DocNumber=invoice_number, qb=client)

    for invoice in invoices:
        invoice_dict = invoice.to_dict()
        invoice_json = json.dumps(invoice_dict)
        print(invoice_json)

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)