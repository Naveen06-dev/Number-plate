
# This snippet can be used to scan images without the notebook
# Usage: python scan_plate.py

import cv2
import easyocr
import re
import os
import matplotlib.pyplot as plt

# 📍 Indian State Code Mapping
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

# 🧠 Recognize plate and predict state
def recognize_state_from_plate(image_path):
    print(f"Processing image: {image_path}")
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return

    print("📥 Initializing EasyOCR...")
    reader = easyocr.Reader(['en'], gpu=False)
    print("✅ OCR Model Ready!")

    print("📸 Reading image...")
    image = cv2.imread(image_path)
    if image is None:
        print("❌ Failed to read the image.")
        return

    print("🔍 Detecting text...")
    try:
        result = reader.readtext(image)
    except Exception as e:
        print(f"❌ OCR processing failed: {e}")
        return

    plate_text = ""
    print("Raw OCR Results:")
    for (bbox, text, prob) in result:
        print(f"  - Text: {text}, Prob: {prob:.4f}")
        
        clean_text = text.upper().replace(" ", "").replace("-", "")
        # The regex in the notebook was: ^[A-Z]{2}[0-9]{1,2}[A-Z]{0,3}[0-9]{4}$
        # This matches: KA05HA1997 or DL1CA1234
        if re.match(r'^[A-Z]{2}[0-9]{1,2}[A-Z]{0,3}[0-9]{4}$', clean_text):
            plate_text = clean_text
            break
        
        # Fallback check
        if len(clean_text) >= 6 and re.match(r'^[A-Z]{2}', clean_text) and re.search(r'[0-9]{4}$', clean_text):
             plate_text = clean_text
             # continue searching for better match or break? Let's keep searching if better match exists
             # But for now let's just break if we found a good candidate
             break

    if plate_text:
        state_code = plate_text[:2]
        state = state_map.get(state_code, "Unknown")
        print(f"\n✅ Detected Plate: {plate_text}")
        print(f"🏷️ Predicted State: {state}")
    else:
        print("❌ No valid number plate found matching the pattern.")
        
        # Fallback: Just print the text with highest probability if it looks alphanumeric
        print("Fallback: Top detections:")
        sorted_result = sorted(result, key=lambda x: x[2], reverse=True)
        for _, text, prob in sorted_result[:3]:
             print(f"  - {text} ({prob:.2f})")

if __name__ == "__main__":
    # You can change this filename to test other images
    image_filename = "WhatsApp Image 2025-07-16 at 11.48.35_e4f9b5f3.jpg"
    
    # Or search for first jpg in images folder
    if not os.path.exists(image_filename):
        if os.path.exists('images'):
            files = [f for f in os.listdir('images') if f.endswith('.jpg')]
            if files:
                image_filename = os.path.join('images', files[0])
    
    current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
    image_path = os.path.join(current_dir, image_filename)
    
    recognize_state_from_plate(image_path)
