import os
import json
from dotenv import load_dotenv

import inflect

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

p = inflect.engine()

auth_client = AuthClient(
    client_id     = os.getenv("CLIENT_ID"),
    client_secret = os.getenv("CLIENT_SECRET"),
    environment   = os.getenv("ENVIRONMENT"),
    redirect_uri  = os.getenv("REDIRECT_URI"),    
)

realm_id = os.getenv("REALM_ID")

@app.route('/')
def index():        
    return render_template('home.html')

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
    # print(invoice_number)
    invoices = Invoice.filter(DocNumber=invoice_number, qb=client)
    invoice_dicts = [invoice.to_dict() for invoice in invoices]
    # print(invoice_dicts)
    invoice_data = invoice_dicts[0]

    customers = Customer.filter(Id=invoice_data['CustomerRef']['value'], qb=client)
    customer_dicts = [customer.to_dict() for customer in customers]
    customer_data = customer_dicts[0]
    # print(customer_data)

    page_data = {}
    page_data['TotalAmt'] = invoice_data['TotalAmt']
    page_data['TotalAmtInWords'] = p.number_to_words(invoice_data['TotalAmt'])
    page_data['TxnDate'] = invoice_data['TxnDate']
    page_data['CustomerName'] = invoice_data['CustomerRef']['name']
    page_data['Addr1'] = invoice_data['BillAddr']['Line1']
    page_data['Addr2'] = return_dot(invoice_data['BillAddr']['Line2'])
    page_data['BusinessStyle'] = "Commissary | Others"
    
    services = []
    ctr = 0
    for service in invoice_data['Line']:        
        if service['Id'] != None:
            data = {}            
            data['Id'] = ctr
            data['Description'] = service['Description']
            data['Qty'] = service['SalesItemLineDetail']['Qty']
            data['UnitPrice'] = service['SalesItemLineDetail']['UnitPrice']
            services.append(data)
        ctr += 1

    if len(services) < 18:
        ctr = len(services)
        print(ctr)
        for i in range(18 - len(services)):
            data = {}
            data['Id'] = ctr
            data['Description'] = ""
            data['Qty'] = ""
            data['UnitPrice'] = ""
            services.append(data)
            ctr += 1
    
    for service in services:
        print(service)

    page_data['Services'] = services
    page_data['TotalTax'] = invoice_data['TxnTaxDetail']['TotalTax']
    page_json_data = json.loads(json.dumps(page_data))        

    return render_template('print.html', page_json_data=page_json_data, )

def return_dot(str):
    if len(str) == 0:
        return "."
    else:
        return str

def extract_key_value(json_data, key):
        """Extracts a specific key-value pair from a JSON data"""
        if json_data:
            data = json.loads(json_data)
            value = data.get(key)
            return value
        return None

if __name__ == '__main__':
    y = 102345.00
    y_str = str(y)
    y_str2 = str(int(y))
    print(y_str)
    print(y_str2)
    last_two_digits = y_str[-2:]
    print(last_two_digits)
    # decimal_point = round(y - int(y), 2)
    # print(decimal_point)
    x = p.number_to_words(10123).upper()
    x = x.replace("POINT ZERO", "")
    x = x.replace(",", "")
    print(x)
    # app.run()