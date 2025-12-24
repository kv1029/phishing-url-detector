from flask import Flask, render_template, request
import google.generativeai as genai
import os
import PyPDF2
import logging

# Initialize Flask app
app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- SECURE API KEY HANDLING ---
# Get key from Vercel Environment Variables
api_key = os.environ.get("GOOGLE_API_KEY") 

if not api_key:
    logger.error("No API Key found! Set GOOGLE_API_KEY in Vercel Settings.")
else:
    genai.configure(api_key=api_key)

# Initialize the Gemini model
model = genai.GenerativeModel("gemini-2.5-flash")
def predict_fake_or_real_email_content(text):
    prompt = f"""
    You are an expert in identifying scam messages in text, email etc. Analyze the given text and classify it as:

    - **Real/Legitimate** (Authentic, safe message)
    - **Scam/Fake** (Phishing, fraud, or suspicious message)

    **for the following Text:**
    {text}

    **Return a clear message indicating whether this content is real or a scam. 
    If it is a scam, mention why it seems fraudulent. If it is real, state that it is legitimate.**

    **Only return the classification message and nothing else.**
    Note: Don't return empty or null, you only need to return message for the input text
    """

    response = model.generate_content(prompt)
    return response.text.strip() if response else "Classification failed."

# Function to classify URL
def url_detection(url):
    prompt = f"""
    You are an advanced AI model specializing in URL security classification. Analyze the given URL and classify it as one of the following categories:

    1. Benign**: Safe, trusted, and non-malicious websites such as google.com, wikipedia.org, amazon.com.
    2. Phishing**: Fraudulent websites designed to steal personal information. Indicators include misspelled domains (e.g., paypa1.com instead of paypal.com), unusual subdomains, and misleading content.
    3. Malware**: URLs that distribute viruses, ransomware, or malicious software. Often includes automatic downloads or redirects to infected pages.
    4. Defacement**: Hacked or defaced websites that display unauthorized content, usually altered by attackers.

    **Example URLs and Classifications:**
    - **Benign_means_safe**: "https://www.microsoft.com/"
    - **Phishing**: "http://secure-login.paypa1.com/"
    - **Malware**: "http://free-download-software.xyz/"
    - **Defacement**: "http://hacked-website.com/"

    **Input URL:** {url}

    **Output Format:**  
    - Return only a string class name
    - Example output for a phishing site:  

    Analyze the URL and return the correct classification (Only name in lowercase such as benign etc.
    Note: Don't return empty or null, at any cost return the corrected class
    """

    response = model.generate_content(prompt)
    return response.text.strip() if response else "Detection failed."


# ... [Keep your predict_fake_or_real_email_content function here] ...
# ... [Keep your url_detection function here] ...

@app.route('/')
def home():
    client_ip = request.remote_addr
    return render_template("index.html", client_ip=client_ip)

# Scam File Upload Route
@app.route('/scam/', methods=['POST'])
def detect_scam():
    client_ip = request.remote_addr

    if 'file' not in request.files:
        return render_template("index.html", message="No file uploaded.", client_ip=client_ip)

    file = request.files['file']
    extracted_text = ""

    if file.filename.endswith('.pdf'):
        pdf_reader = PyPDF2.PdfReader(file)
        extracted_text = " ".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
    elif file.filename.endswith('.txt'):
        extracted_text = file.read().decode("utf-8")
    else:
        return render_template("index.html", message="Invalid file type. Upload PDF or TXT.", client_ip=client_ip)

    if not extracted_text.strip():
        return render_template("index.html", message="Empty file or unable to extract text.", client_ip=client_ip)

    message = predict_fake_or_real_email_content(extracted_text)
    return render_template("index.html", message=message, client_ip=client_ip)

# URL Prediction Route
@app.route('/predict', methods=['POST'])
def predict_url():
    client_ip = request.remote_addr
    url = request.form.get('url', '').strip()

    if not url.startswith(("http://", "https://")):
        return render_template("index.html", message="Invalid URL format.", input_url=url, client_ip=client_ip)

    classification = url_detection(url)
    return render_template("index.html", input_url=url, predicted_class=classification, client_ip=client_ip)

if __name__ == '__main__':
    app.run(debug=True)