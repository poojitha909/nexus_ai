import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import base64

# --- CONFIGURATION ---
# PASTE YOUR KEY HERE
GEMINI_API_KEY = "AIzaSyD-Zt6Dd4tTV584W01nDEwaiWGIMF2gsJQ"

# Configure Model
# --- IMPROVED CONFIGURATION ---

# Configure Model with Auto-Detection
try:
    genai.configure(api_key=GEMINI_API_KEY)
    
    # 1. List available models that support generation
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)
    
    # 2. Pick the first valid model (Prioritize Gemini 1.5 if available)
    # This loop looks for the best model you actually have access to.
    chosen_model = ""
    if available_models:
        # Try to find a 'flash' or 'pro' model first
        for m in available_models:
            if 'flash' in m or 'pro' in m:
                chosen_model = m
                break
        # Fallback to the first one if no specific one found
        if not chosen_model:
            chosen_model = available_models[0]
            
        print(f"System: Using Model -> {chosen_model}")
        model = genai.GenerativeModel(chosen_model)
    else:
        st.error("CRITICAL: No compatible Gemini models found for this API Key.")
        
except Exception as e:
    st.warning(f"API Setup Error: {e}")

def generate_german_text(service, contract_id, reason):
    """
    Asks AI to write the formal German legal text.
    """
    prompt = f"""
    Write a formal contract termination letter (Kündigungsschreiben) in German.
    
    Details:
    - Service to cancel: {service}
    - Contract/Customer Number: {contract_id}
    - Reason: {reason} (If empty, use standard 'next possible date')
    
    Rules:
    - Subject Line: "Kündigung meines Vertrags"
    - Tone: Formal, Bureaucratic, Polite.
    - Include the phrase: "Bitte senden Sie mir eine schriftliche Bestätigung der Kündigung unter Angabe des Beendigungszeitpunktes." (Requesting confirmation).
    - Do NOT include placeholders like [Your Name]. Just write the body text.
    """
    response = model.generate_content(prompt)
    return response.text

def create_pdf(sender_name, sender_addr, company_name, company_addr, body_text):
    """
    Typesets the text into a formal German A4 Letter.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    
    # 1. Header (Sender Info - Top Left)
    pdf.cell(200, 5, txt=sender_name, ln=True)
    pdf.cell(200, 5, txt=sender_addr, ln=True)
    pdf.ln(10)
    
    # 2. Recipient (Company Info)
    pdf.set_font("Arial", style='B', size=11)
    pdf.cell(200, 5, txt=company_name, ln=True)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 5, txt=company_addr)
    pdf.ln(15)
    
    # 3. Date (Right Aligned)
    pdf.cell(0, 10, txt="Datum: [Current Date]", ln=True, align='R')
    pdf.ln(5)
    
    # 4. The AI Generated Body
    # We need to handle encoding for German characters (ä, ö, ü)
    # FPDF standard font doesn't support unicode well, so we encode to latin-1
    try:
        clean_body = body_text.encode('latin-1', 'replace').decode('latin-1')
    except:
        clean_body = body_text # Fallback
        
    pdf.multi_cell(0, 6, txt=clean_body)
    
    pdf.ln(20)
    pdf.cell(0, 10, txt="__________________________", ln=True)
    pdf.cell(0, 10, txt="(Unterschrift / Signature)", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- THE UI ---
st.set_page_config(page_title="Kündigung AI", page_icon="🇩🇪")
st.title("🇩🇪 German Bureaucracy Killer")
st.subheader("Cancel any contract in Germany instantly.")

col1, col2 = st.columns(2)
with col1:
    st.markdown("### Your Details")
    my_name = st.text_input("Your Full Name", "Poojitha Guntoju")
    my_address = st.text_area("Your Address (Street, Zip, City)")
    contract_id = st.text_input("Contract/Customer Number")

with col2:
    st.markdown("### Company Details")
    company_name = st.text_input("Company Name (e.g., Vodafone, McFit)")
    company_address = st.text_area("Company Address")
    reason = st.text_input("Reason (Optional)")

if st.button("Generate Cancellation Letter"):
    if not GEMINI_API_KEY or "PASTE" in GEMINI_API_KEY:
        st.error("Paste your API Key in the code first!")
    else:
        with st.spinner("Consulting German Laws..."):
            # 1. Get Text from AI
            german_body = generate_german_text(company_name, contract_id, reason)
            
            # 2. Show Preview
            st.text_area("Generated German Text", german_body, height=200)
            
            # 3. Create PDF
            try:
                pdf_bytes = create_pdf(my_name, my_address, company_name, company_address, german_body)
                
                # 4. Download Button
                st.download_button(
                    label="Download Official PDF",
                    data=pdf_bytes,
                    file_name="Kuendigung.pdf",
                    mime="application/pdf"
                )
                st.success("Letter generated! Print, Sign, and Send.")
            except Exception as e:
                st.error(f"PDF Error: {e}")