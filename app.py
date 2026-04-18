from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = '12345'

def load_credit_data():
    return pd.read_csv('data/credit_data.csv')

def save_credit_data(df):
    df.to_csv('data/credit_data.csv', index=False)

def send_credit_email(customer_name, email, credit_amount, status):
    sender_email = "nayankhistariya345@gmail.com"
    sender_password = "xcdc ghdd vbfx kpvy"
    receiver_email = email

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = f"Credit Status Update - {customer_name}"

    body = f"""
    Dear {customer_name},

    This is to inform you about your credit status:

    Credit Amount: ₹{credit_amount}
    Status: {status}
    
    {"Your credit has been marked as paid. Thank you for your payment!" if status == 'paid' else ""}

    Thank you for your business!

    Best regards,
    Credit Manager Team
    """

    message.attach(MIMEText(body, "plain"))
    #try catuch for send eamil 
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Something went wrong while sending email: {str(e)}")
        return False


#website work
@app.route('/')
def dashboard():
    credit_data = load_credit_data()
    credit_data['credit_amount'] = pd.to_numeric(credit_data['credit_amount'], errors='coerce')
    
    total_credit = credit_data['credit_amount'].sum()
    active_credits = len(credit_data[credit_data['status'] == 'active'])
    total_customers = len(credit_data)
    
    return render_template('dashboard.html',credit_data=credit_data.to_dict('records'),total_credit=total_credit,
                         active_credits=active_credits,
                         total_customers=total_customers)

@app.route('/customers')
def customers():
    credit_data = load_credit_data()
    # Convert credit_amount to numeric values
    credit_data['credit_amount'] = pd.to_numeric(credit_data['credit_amount'], errors='coerce')
    
    customers_data = credit_data.groupby('customer_name').agg({
        'credit_amount': ['sum', 'count'],
        'status': lambda x: (x == 'active').sum(),
        'email': 'first',
        'mobile_number': 'first'
    }).reset_index()
    
    customers_data.columns = ['customer_name', 'total_credit', 'total_transactions', 'active_credits', 'email', 'mobile_number']
    return render_template('customers.html', customers=customers_data.to_dict('records'))

@app.route('/credits')
def credits():
    credit_data = load_credit_data()
    # Convert credit_amount to numeric values
    credit_data['credit_amount'] = pd.to_numeric(credit_data['credit_amount'], errors='coerce')
    return render_template('credits.html', credits=credit_data.to_dict('records'))

@app.route('/reports')
def reports():
    credit_data = load_credit_data()
    # Convert credit_amount to numeric values
    credit_data['credit_amount'] = pd.to_numeric(credit_data['credit_amount'], errors='coerce')
    
    # Calculate monthly statistics
    credit_data['date'] = pd.to_datetime(credit_data['date'])
    monthly_stats = credit_data.groupby(credit_data['date'].dt.strftime('%Y-%m')).agg({
        'credit_amount': ['sum', 'count'],
        'status': lambda x: (x == 'active').sum()
    }).reset_index()
    
    monthly_stats.columns = ['month', 'total_amount', 'total_transactions', 'active_credits']
    
    # Calculate status distribution
    status_distribution = credit_data['status'].value_counts().to_dict()
    
    return render_template('reports.html',
                         monthly_stats=monthly_stats.to_dict('records'),
                         status_distribution=status_distribution)

@app.route('/add_credit', methods=['POST'])
def add_credit():
    if request.method == 'POST':
        try:
            credit_data = load_credit_data()
            new_credit = {
                'customer_name': request.form['customer_name'],
                'email': request.form['email'],
                'mobile_number': request.form['mobile_number'],
                'credit_amount': float(request.form['credit_amount']),
                'date': datetime.now().strftime('%Y-%m-%d'),
                'status': 'active'
            }
            
            credit_data = pd.concat([credit_data, pd.DataFrame([new_credit])], ignore_index=True)
            save_credit_data(credit_data)
            return jsonify({'success': True, 'message': 'Added new credit!'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'Something went wrong: {str(e)}'}), 400

@app.route('/update_credit', methods=['POST'])
def update_credit():
    if request.method == 'POST':
        try:
            credit_data = load_credit_data()
            customer_name = request.form['customer_name']
            
            # Update the credit entry
            credit_data.loc[credit_data['customer_name'] == customer_name, 'email'] = request.form['email']
            credit_data.loc[credit_data['customer_name'] == customer_name, 'mobile_number'] = request.form['mobile_number']
            credit_data.loc[credit_data['customer_name'] == customer_name, 'credit_amount'] = float(request.form['credit_amount'])
            credit_data.loc[credit_data['customer_name'] == customer_name, 'status'] = request.form['status']
            
            save_credit_data(credit_data)
            return jsonify({'success': True, 'message': 'Credit updated successfully!'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/delete_credit', methods=['POST'])
def delete_credit():
    if request.method == 'POST':
        try:
            credit_data = load_credit_data()
            customer_name = request.form['customer_name']
            
            # Delete the credit entry
            credit_data = credit_data[credit_data['customer_name'] != customer_name]
            save_credit_data(credit_data)
            return jsonify({'success': True, 'message': 'Credit deleted successfully!'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/send_email', methods=['POST'])
def send_email():
    if request.method == 'POST':
        try:
            data = request.get_json()
            if send_credit_email(data['customer_name'], data['email'], float(data['credit_amount']), data['status']):
                return jsonify({'success': True, 'message': 'Email sent successfully!'})
            else:
                return jsonify({'success': False, 'message': 'Failed to send email.'}), 400
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True) 