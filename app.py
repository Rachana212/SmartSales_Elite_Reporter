from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
import os
import traceback
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

from scripts.google_sheets_reader import read_sheet
from scripts.save_to_db import save_to_db
from scripts.generate_report import generate_report
from scripts.email_sender import send_email
from scripts.generate_pdf import generate_pdf_with_chart

app = Flask(__name__)
app.secret_key = 'simplekey123'  # Secret key for session

REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

# Possible sales column names (case insensitive)
POSSIBLE_SALES_COLUMNS = ["Sales", "Amount", "Total", "Revenue"]

def find_sales_column(df):
    for col in df.columns:
        if col.strip().lower() in [name.lower() for name in POSSIBLE_SALES_COLUMNS]:
            return col
    raise ValueError(f"No sales column found. Expected one of: {POSSIBLE_SALES_COLUMNS}")

# --- Login page ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == "Rachana" and password == "Racchu":
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash(" Invalid username or password!", "error")
            return render_template('login.html')

    return render_template('login.html')

# --- Dashboard / main frontend page ---
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    try:
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        if not start_date or not end_date:
            flash("⚠ Please enter both start and end dates!", "error")
            return redirect(url_for('dashboard'))

        # Read and save data
        df = read_sheet()
        if df.empty:
            flash(" Failed to load data from Google Sheet.", "error")
            return redirect(url_for('dashboard'))

        save_to_db(df)

        # Generate report and chart path
        report_text, chart_path = generate_report(start_date, end_date)
        if not report_text.strip():
            flash(" Report is empty!", "error")
            return redirect(url_for('dashboard'))

        # Generate PDF with chart
        pdf_path = generate_pdf_with_chart(report_text, chart_path, f"{start_date}to{end_date}")

        flash(f" Report generated successfully! Saved as {os.path.basename(pdf_path)}", "success")
        return render_template('index.html', report=report_text, start_date=start_date, end_date=end_date)

    except Exception as e:
        traceback.print_exc()
        flash(f" An error occurred: {str(e)}", "error")
        return redirect(url_for('dashboard'))

@app.route('/send-mail', methods=['POST'])
def send_mail():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    try:
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        print(f"Send mail called for date range: {start_date} to {end_date}")

        if not start_date or not end_date:
            flash("⚠ Please enter both start and end dates to send mail!", "error")
            return redirect(url_for('dashboard'))

        report_text, chart_path = generate_report(start_date, end_date)
        if not report_text.strip():
            flash(" Cannot send email: Report is empty!", "error")
            return redirect(url_for('dashboard'))

        pdf_path = generate_pdf_with_chart(report_text, chart_path, f"{start_date}to{end_date}")

        success, message = send_email(report_text=report_text, chart_path=chart_path, pdf_path=pdf_path)

        if not success:
            flash(f" {message}", "error")
        else:
            flash(f" {message}", "success")

        return render_template('index.html', report=report_text, start_date=start_date, end_date=end_date)

    except Exception as e:
        traceback.print_exc()
        flash(f" An error occurred while sending email: {str(e)}", "error")
        return redirect(url_for('dashboard'))

@app.route('/history')
def history():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    files = sorted(os.listdir(REPORTS_DIR), reverse=True)
    pdf_files = [f for f in files if f.endswith('.pdf')]
    return render_template('history.html', files=pdf_files)

@app.route('/download/<filename>')
def download_report(filename):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return send_from_directory(REPORTS_DIR, filename, as_attachment=True)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash(" You have been logged out.", "success")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)