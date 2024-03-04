import os
import json
from dotenv import load_dotenv

# Flask
from flask import Flask, jsonify, render_template, request, redirect, session

# QuickBooks
from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
from quickbooks import QuickBooks
from quickbooks.objects.invoice import Invoice
from quickbooks.objects.customer import Customer 

app = Flask(__name__)
# Load the stored environment variables
load_dotenv()

app.secret_key = os.getenv("SECRET_KEY")


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

##########################################
#                                        #
#  Authentication and Authorization      #
#                                        #
##########################################

@app.route('/login')
def login():
    url = auth_client.get_authorization_url([Scopes.ACCOUNTING])
    return redirect(url)
@app.route('/logout')
def logout():
    # Clear the access token from the session
    session.pop('access_token', None)
    return redirect('/')

@app.route('/callback')
def callback():
    auth_code = request.args.get('code')
    auth_client.get_bearer_token(auth_code, realm_id=realm_id)
    # Store the access token, refresh token, and token expiration time in session
    session['access_token'] = auth_client.access_token  
    session['refresh_token'] = auth_client.refresh_token
    session['token_expires_at'] = auth_client.expires_in
    session['realm_id'] = auth_client.realm_id
    return redirect('/')

##########################################
#                                        #
#  Authentication and Authorization      #
#                                        #
##########################################

@app.route('/test')
def test():
    refresh_token = session.get('refresh_token')
    access_token = session.get('access_token')
    
    print(refresh_token)
    print(access_token)
    print(realm_id)
    return auth_client.access_token


@app.route('/invoice', methods=['POST'])
def invoice():
    client = QuickBooks(
        auth_client=auth_client,
        # refresh_token=auth_client.refresh_token,
        refresh_token=session.get('refresh_token'),
        company_id=realm_id    
    )

    invoice_number = request.form['invoice_number']
    print(invoice_number)
    invoices = Invoice.filter(DocNumber=invoice_number, qb=client)
    invoice_dicts = [invoice.to_dict() for invoice in invoices]
    print(invoice_dicts)
    invoice_data = invoice_dicts[0]

    customers = Customer.filter(Id=invoice_data['CustomerRef']['value'], qb=client)
    customer_dicts = [customer.to_dict() for customer in customers]
    customer_data = customer_dicts[0]

    return render_template('print.html', invoice_data=invoice_data, customer_data=customer_data)


def extract_key_value(json_data, key):
        """Extracts a specific key-value pair from a JSON data"""
        if json_data:
            data = json.loads(json_data)
            value = data.get(key)
            return value
        return None

if __name__ == '__main__':
    app.run()