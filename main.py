from flask import Flask, request, flash, redirect, url_for, send_from_directory, render_template, make_response, send_file
from werkzeug.utils import secure_filename
import os
import pandas as pd
from mindee import Client, documents
from io import StringIO
import csv

# Init a new client
mindee_client = Client(api_key="f83b4a6fce2000c20bafc281a907fcfc")

UPLOAD_FOLDER = 'flask_Druidot/static/uploads'  # Folder path
OUTPUT_FOLDER = 'static/outputs' # Folder path
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}  # Extensions supported.
csrf_token = "fiuh42fuo3htijfm2"  # Token used for CSRF protection.

app = Flask(__name__)

# Application configuration:
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # Folder path.
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['SECRET_KEY'] = csrf_token  # Secret key used for CSRF protection.
app.config['MAX_CONTENT_LENGTH'] = 32 * 1000 * 1000  # File size limit 32 mb.


# Methods:
def allowed_file(filename):
    """This method returns if the given file extension is allowed. Returns true if allowed else false."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_df(img_path):
    """This function returns the csv file."""

    input_doc = mindee_client.doc_from_path(img_path)

    result = input_doc.parse(documents.TypeInvoiceV4)

    data = result.http_response['document']['inference']['pages'][0]['prediction']

    addr = data['customer_address']['value']
    c_name = data['customer_name']['value']
    c_date = data['date']['value']
    d_type = data['document_type']['value']
    i_number = data['invoice_number']['value']
    items = data['line_items']
    sup_add = data['supplier_address']['value']
    sup_name = data['supplier_name']['value']
    ttl_amt = data['total_amount']['value']
    ttl_val = data['total_net']['value']

    gen_dta = [d_type, i_number, addr, c_name, c_date, sup_add, sup_name, ttl_amt, ttl_val]
    items_dta = {
        "Description": [i['description'] for i in items], 
        "Quantity": [i['quantity'] for i in items], 
        "Tax Amount": [i['tax_amount'] for i in items], 
        "Tax rate": [i['tax_rate'] for i in items], 
        "Unit Price": [i['unit_price'] for i in items], 
        "Item Total Amount": [i['total_amount'] for i in items]
    }



    df1 = pd.DataFrame([gen_dta], columns=["Doc-Type", "Doc-Number", "Customer Address", "Customer Name", "Date", "Supplier Address", "Supplier Name", "Total Amt", "Total Value"])
    df1.reset_index(drop=True)
    df2 = pd.DataFrame(items_dta, index=None)
    df2.reset_index(drop=True)

    merged_data = [df1, df2]

    merged_dataframe = pd.concat(merged_data, keys=["Information", "Items"])

    return merged_dataframe


# Routes:
@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["OUTPUT_FOLDER"], name)
    


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            print('No file part')
            return redirect('/')
        
        file = request.files['file']
        print(file.filename)

        if file.filename == '':
            flash('No selected file')
            print('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'img.png'))

            output_file = get_df(os.path.join(app.config['UPLOAD_FOLDER'], 'img.png'))


            return render_template('ui.html', tables=[output_file.to_html(classes='data')], titles=output_file.columns.values, get_data=True)




    return render_template('ui.html', tables =[], titles = None, get_data=False)


with app.app_context():
    if __name__ == '__main__':
        app.run(debug=True)