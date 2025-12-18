import streamlit as st
import requests
import google.generativeai as genai
import json

# --- 1. UI CONFIG ---
st.set_page_config(page_title="Nexus: Serper Edition", page_icon="🚀", layout="wide")

# --- 2. CONFIGURATION ---
# PASTE YOUR KEYS HERE
GEMINI_API_KEY = "AIzaSyD-Zt6Dd4tTV584W01nDEwaiWGIMF2gsJQ"
SERPER_API_KEY = "77c2ecedad65d70b16555180fa7fc76103941db9"

# Configure Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    chosen_model = next((m for m in available_models if 'flash' in m or 'pro' in m), available_models[0] if available_models else None)
    model = genai.GenerativeModel(chosen_model)
except Exception as e:
    st.error(f"Gemini Config Error: {e}")

def search_google_serper(query):
    """
    Uses Serper.dev to search Google for LinkedIn profiles.
    Returns a LIST of DICTIONARIES (Clean Data).
    """
    url = "https://google.serper.dev/search"
    
    # We force Google to look for LinkedIn Profiles only
    formatted_query = f"site:linkedin.com/in/ {query}"
    
    payload = json.dumps({
        "q": formatted_query,
        "num": 5  # Get exact top 5 results
    })
    
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        
        clean_results = []
        # Parse the "organic" results from Google
        for r in data.get("organic", []):
            clean_results.append({
                "name": r.get("title", "Unknown Name").replace(" | LinkedIn", ""),
                "link": r.get("link", "#"),
                "bio": r.get("snippet", "No bio available.")
            })
            
        return clean_results

    except Exception as e:
        st.error(f"Serper API Error: {e}")
        return []

def get_ai_strategy(profiles_data, mission, my_bg):
    if not profiles_data:
        return "No profiles found."
    
    # Convert list of dicts to string for AI
    data_block = ""
    for i, p in enumerate(profiles_data):
        data_block += f"{i+1}. {p['name']} - {p['bio']}\n"
    
    prompt = f"""
    Act as a Master Networker.
    
    MY BACKGROUND: {my_bg}
    MY MISSION: {mission}
    
    CANDIDATES FOUND:
    {data_block}
    
    INSTRUCTIONS:
    1. Analyze all 5 candidates.
    2. Rank them 1 to 5 based on who is most likely to reply and help.
    3. For the WINNER (#1), write a specific Cold DM (300 chars).
    4. For the Runner Up (#2), write a specific Cold DM.
    """
    
    response = model.generate_content(prompt)
    return response.text

# --- 4. THE APP UI ---
st.title("🚀 Nexus: Sniper Networker")
st.caption("Powered by Serper.dev & Gemini")

with st.sidebar:
    st.header("Setup")
    if "PASTE" in SERPER_API_KEY:
        st.warning("⚠️ Paste Serper Key!")
    else:
        st.success("✅ Serper Key Loaded")
    
    my_background = st.text_area("Your Profile", "CS Engineer (Jan 2026), Ex-Salesforce, building Agentic AI tools.", height=100)

col1, col2 = st.columns(2)
with col1:
    role = st.text_input("Who?", "Engineering Manager")
with col2:
    loc = st.text_input("Where?", "Berlin")

mission = st.text_input("Your Goal", "I want to pitch my Kündigung-AI tool.")

if st.button("Scout Network"):
    if "PASTE" in GEMINI_API_KEY or "PASTE" in SERPER_API_KEY:
        st.error("Keys Missing! Check code.")
    else:
        with st.spinner("Scouting Top 5 Leads..."):
            # 1. Search
            query_string = f"{role} {loc}"
            profiles = search_google_serper(query_string)
            
            if profiles:
                # 2. Display the 5 Profiles CLEARLY
                st.divider()
                st.subheader(f"🔍 Top {len(profiles)} Leads Found")
                
                # Display cards for each person
                for p in profiles:
                    with st.container():
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.markdown(f"**{p['name']}**")
                            st.caption(p['bio'])
                        with c2:
                            st.link_button("🔗 Profile", p['link'])
                        st.divider()

                # 3. AI Analysis
                st.subheader("🧠 Strategic Analysis")
                with st.spinner("Brain is thinking..."):
                    analysis = get_ai_strategy(profiles, mission, my_background)
                    st.write(analysis)
            else:
                st.error("0 Results. Serper key might be invalid or query too weird.")