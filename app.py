
from flask import Flask, render_template, request, jsonify
import os
import cv2
import easyocr
import re
import uuid
import json
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
HISTORY_FILE = 'history.json'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize history file if not exists
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, 'w') as f:
        json.dump([], f)

# Initialize OCR reader once
print("Loading OCR model...")
reader = easyocr.Reader(['en'], gpu=False)
print("OCR model loaded.")

# State Mapping (Fallback)
state_map = {
    'AP': 'Andhra Pradesh', 'AR': 'Arunachal Pradesh', 'AS': 'Assam', 'BR': 'Bihar',
    'CG': 'Chhattisgarh', 'CH': 'Chandigarh', 'DL': 'Delhi', 'GA': 'Goa', 'GJ': 'Gujarat',
    'HR': 'Haryana', 'HP': 'Himachal Pradesh', 'JH': 'Jharkhand', 'JK': 'Jammu and Kashmir',
    'KA': 'Karnataka', 'KL': 'Kerala', 'LA': 'Ladakh', 'LD': 'Lakshadweep', 'MH': 'Maharashtra',
    'ML': 'Meghalaya', 'MN': 'Manipur', 'MP': 'Madhya Pradesh', 'MZ': 'Mizoram', 'NL': 'Nagaland',
    'OD': 'Odisha', 'PB': 'Punjab', 'PY': 'Puducherry', 'RJ': 'Rajasthan', 'SK': 'Sikkim',
    'TN': 'Tamil Nadu', 'TR': 'Tripura', 'TS': 'Telangana', 'UK': 'Uttarakhand', 'UP': 'Uttar Pradesh',
    'WB': 'West Bengal'
}

# RTO Code Mapping
rto_codes = {
  "AP": {
    "01": "Anantapur", "02": "Chittoor", "03": "Kadapa", "04": "Kurnool", "05": "Prakasam",
    "06": "Nellore", "07": "Guntur", "08": "Krishna", "09": "West Godavari", "10": "East Godavari",
    "11": "Visakhapatnam", "12": "Vizianagaram", "13": "Srikakulam"
  },
  "AR": { "01": "Itanagar", "02": "Naharlagun", "03": "Tawang", "04": "Bomdila" },
  "AS": {
    "01": "Guwahati", "02": "Nagaon", "03": "Jorhat", "04": "Sibsagar", "05": "Golaghat",
    "06": "Silchar", "07": "Dibrugarh", "08": "Lakhimpur"
  },
  "BR": {
    "01": "Patna", "02": "Gaya", "03": "Bhojpur", "04": "Chapra", "05": "Motihari",
    "06": "Darbhanga", "07": "Muzaffarpur", "10": "Bhagalpur"
  },
  "CG": { "01": "Raipur", "02": "Bhilai", "03": "Durg", "04": "Bilaspur", "05": "Korba" },
  "DL": {
    "01": "Delhi North", "02": "New Delhi", "03": "South Delhi", "04": "West Delhi",
    "05": "North East Delhi", "06": "Central Delhi", "07": "East Delhi", "08": "North West Delhi",
    "09": "South West Delhi"
  },
  "GJ": {
    "01": "Ahmedabad", "02": "Mehsana", "03": "Rajkot", "04": "Bhavnagar", "05": "Surat",
    "06": "Vadodara", "27": "Gandhinagar"
  },
  "HR": {
    "01": "Ambala", "02": "Yamunanagar", "03": "Panchkula", "26": "Gurgaon", "51": "Hisar"
  },
  "KA": {
    "01": "Bengaluru Central", "02": "Bengaluru West", "03": "Bengaluru East", "04": "Bengaluru North",
    "05": "Bengaluru South", "19": "Mangaluru", "25": "Tumakuru"
  },
  "KL": {
    "01": "Thiruvananthapuram", "02": "Kollam", "03": "Pathanamthitta", "04": "Alappuzha",
    "07": "Ernakulam", "10": "Thrissur"
  },
  "MH": {
    "01": "Mumbai Central", "02": "Mumbai West", "03": "Mumbai East", "04": "Thane",
    "12": "Pune", "14": "Pimpri-Chinchwad", "31": "Nagpur"
  },
  "MP": { "01": "Bhopal", "02": "Hoshangabad", "03": "Gwalior", "04": "Indore", "09": "Ujjain" },
  "PB": { "01": "Amritsar", "02": "Bathinda", "03": "Faridkot", "10": "Jalandhar" },
  "RJ": { "01": "Ajmer", "02": "Alwar", "14": "Jaipur", "19": "Jodhpur", "45": "Sikar" },
  "TN": {
    "01": "Chennai Central", "07": "Chennai South", "09": "Chennai West", "22": "Meenambakkam",
    "33": "Tiruchirappalli", "37": "Coimbatore South", "38": "Coimbatore North", "59": "Madurai North",
    "72": "Tirunelveli"
  },
  "TS": {
    "01": "Hyderabad Central", "02": "Hyderabad North", "03": "Hyderabad South", "05": "Secunderabad",
    "08": "Medchal"
  },
  "UP": {
    "01": "Allahabad", "02": "Kanpur", "14": "Agra", "16": "Aligarh", "32": "Lucknow", "53": "Gorakhpur"
  },
  "WB": { "01": "Kolkata", "02": "Kolkata North", "04": "Howrah", "06": "Alipore", "20": "Siliguri" }
}

def process_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return None, "Failed to read image"

    # --- Preprocessing for better accuracy ---
    # 1. Resize (Upscale) if image is small
    height, width = image.shape[:2]
    if width < 1000:
        scale_ratio = 1000 / width
        image = cv2.resize(image, None, fx=scale_ratio, fy=scale_ratio, interpolation=cv2.INTER_CUBIC)

    # 2. Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 3. Gaussian Blur (Reduce noise)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 4. Adaptive Threshold (Binarize) - distinct text from background
    # This helps even with shadows or uneven lighting
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    # Run OCR on the processed image (thresh) and original gray for robustness
    try:
        # Pass the preprocessed image
        result = reader.readtext(thresh)
        # If no result, try grayscale
        if not result:
             result = reader.readtext(gray)
    except Exception as e:
        return None, str(e)

    plate_text = ""
    
    # Try to find a match with the strict regex first
    for (bbox, text, prob) in result:
        clean_text = text.upper().replace(" ", "").replace("-", "").replace(".", "")
        # Matches typical format like KA05HA1997
        if re.match(r'^[A-Z]{2}[0-9]{1,2}[A-Z]{0,3}[0-9]{4}$', clean_text):
            plate_text = clean_text
            break
            
    # Fallback: look for strong resemblance
    if not plate_text:
         for (bbox, text, prob) in result:
            clean_text = text.upper().replace(" ", "").replace("-", "").replace(".", "")
            if len(clean_text) >= 6 and re.match(r'^[A-Z]{2}', clean_text) and re.search(r'[0-9]{4}$', clean_text):
                 plate_text = clean_text
                 break

    if plate_text:
        state_code = plate_text[:2]
        
        # Extract RTO/District code (Next 2 digits)
        rto_number = ""
        if len(plate_text) >= 4 and plate_text[2:4].isdigit():
             rto_number = plate_text[2:4]
        
        state_name = state_map.get(state_code, "Unknown State")
        rto_place = "Unknown Location"
        
        # Lookup RTO Code
        if state_code in rto_codes and rto_number in rto_codes[state_code]:
            rto_place = rto_codes[state_code][rto_number]
            
        # Format the output string
        # e.g., "Maharashtra, Pune (12)" or just "State, RTO Code" details
        if rto_place != "Unknown Location":
            result_string = f"{state_name}, {rto_place} ({state_code}{rto_number})"
        else:
            result_string = state_name
            
        return {"plate_text": plate_text, "state": result_string}, None
    else:
        return None, "No valid number plate detected"

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/scan', methods=['POST'])
def scan():
    if 'image' not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"})
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"})
    
    if file:
        # Save file temporarily
        filename = f"{uuid.uuid4()}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process image
        result, error = process_image(filepath)
        
        # Clean up file
        try:
            os.remove(filepath)
        except:
            pass
            
        if result:
            return jsonify({"success": True, **result})
        else:
            return jsonify({"success": False, "error": error})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
