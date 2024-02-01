import datetime
import json
from flask import Flask, render_template, request, redirect
from intuitlib.client import AuthClient
from intuitlib.enums import Scopes

import os
from dotenv import load_dotenv
from quickbooks import QuickBooks
from quickbooks.objects.invoice import Invoice


app = Flask(__name__)

# Load the stored environment variables
load_dotenv()

auth_client = AuthClient(
    client_id     = os.getenv("CLIENT_ID"),
    client_secret = os.getenv("CLIENT_SECRET"),
    environment   = os.getenv("ENVIRONMENT"),
    redirect_uri  = os.getenv("REDIRECT_URI"),
)

@app.route('/')
def index():    
    url = auth_client.get_authorization_url([Scopes.ACCOUNTING])
    return redirect(url)

@app.route('/callback')
def callback():
    auth_code = request.args.get('code')
    auth_client.get_bearer_token(auth_code, realm_id='9130357842152386')
    # print(auth_client.access_token)

    client = QuickBooks(
        auth_client=auth_client,
        refresh_token=auth_client.refresh_token,
        company_id='9130357842152386'
    )

    # invoices = Invoice.all(qb=client, max_results=100)
    # invoices = Invoice.filter(CustomerRef='16', order_by='TxnDate DESC', qb=client)
    # date_after = datetime(2022, 1, 1)
    # invoices = Invoice.filter(MetaData_CreateTime__gt=date_after, qb=client)
    invoice_number = '1010'
    invoices = Invoice.filter(DocNumber=invoice_number, qb=client)

    for invoice in invoices:
        invoice_dict = invoice.to_dict()
        invoice_json = json.dumps(invoice_dict)
        print(invoice_json)

    # for invoice in invoices:
    #     print(dir(invoice))
    #     print(invoice.BillAddr.Line1)
    #     print(invoice.BillAddr.Line2)
    #     print(invoice.BillAddr.City)
    #     print(invoice.BillAddr.Country)
    #     print(invoice.BillAddr.PostalCode)
    #     print(invoice.TxnTaxDetail)
    #     # print(invoice.Line)
        
    #     for line in invoice.Line:
    #         print('====')
    #         print(dir(line))
    #         print(line.Id)
    #         print(line.Description)
    #         print(line.Amount)
    #         print(line.SalesItemLineDetail())

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)