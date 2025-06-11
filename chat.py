import streamlit as st
import os
import time
import io
import re
import base64
import tempfile
import pandas as pd
import fitz  # PyMuPDF
import docx
from pptx import Presentation
from PIL import Image
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from html import unescape
import json
import pickle

# Set page config - MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    "iBUS Chatbot", 
    "🤖", 
    "wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.ibusnetworks.com/help',
        'Report a bug': 'https://www.ibusnetworks.com/bug',
        'About': 'iBUS Networks Interactive Chatbot'
    }
)

HISTORY_DIR = "chat_histories"
os.makedirs(HISTORY_DIR, exist_ok=True)

# Add CSS to ensure logo stays at top - after the existing set_page_config
st.markdown("""
<style>
    /* Override Streamlit's default header behavior */
    header {
        visibility: hidden;
    }
    
    /* Create a fixed header */
    .fixed-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background-color: white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        padding: 5px 10px; /* Reduced padding */
        z-index: 9999;
        display: flex;
        align-items: center;
        gap: 10px; /* Reduced gap */
    }
    
    /* Add padding to the main content to prevent it from being hidden behind the fixed header */
    .main-content-wrapper {
        margin-top: 70px; /* Reduced margin-top */
        padding: 10px;
    }
    
    /* Logo styling */
    .fixed-header img {
        height: 50px; /* Reduced height */
        width: 70px; /* Reduced width */
    }
    
    /* Text styling with responsive sizes */
    .header-text h1 {
        margin: 0;
        color: #003A6C;
        font-size: clamp(18px, 3vw, 28px); /* Reduced font size */
    }
    
    .header-text p {
        margin: 0;
        color: #6C757D;
        font-size: clamp(12px, 1.5vw, 16px); /* Reduced font size */
    }

    /* Media queries for different screen sizes */
    @media (max-width: 768px) {
        .fixed-header {
            padding: 4px 8px;
        }
        
        .fixed-header img {
            height: 40px;
            width: 55px;
        }
        
        .main-content-wrapper {
            margin-top: 50px;
        }
    }
    
    @media (max-width: 480px) {
        .fixed-header {
            padding: 3px 6px;
        }
        
        .fixed-header img {
            height: 35px;
            width: 45px;
        }
        
        .main-content-wrapper {
            margin-top: 40px;
        }
    }
</style>
""", unsafe_allow_html=True)

# Replace your existing logo and title section with this
st.markdown("""
<div class="fixed-header">
    <img src="https://media.licdn.com/dms/image/v2/C560BAQF4xkHYB4X3Fw/company-logo_200_200/company-logo_200_200/0/1672579746218/ibus_networks_logo?e=1750896000&v=beta&t=CUlZ2YnRxrYwUkEiQSbPHPQdXtEGxZ_5JOs9Oxm5IQM" alt="iBUS Logo">
    <div class="header-text">
        <h1>iBUS Interactive Chatbot</h1>
        <p>Your intelligent telecommunications assistant</p>
    </div>
</div>
<div class="main-content-wrapper">
""", unsafe_allow_html=True)

# Add custom CSS for chat bubbles with username labels
st.markdown("""
<style>
    /* Enhanced chat container with iBUS branding */
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin-bottom: 18px;
        width: 100%;
    }
    
    /* User message - right aligned with iBUS primary color */
    .user-message-container {
        display: flex;
        justify-content: flex-end;
        width: 100%;
    }
    
    .user-message {
        background-color: var(--ibus-primary);
        color: white;
        border-radius: 18px 18px 0 18px;
        padding: 12px 18px;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        position: relative;
    }
    
    /* Bot message - left aligned with light background */
    .bot-message-container {
        display: flex;
        justify-content: flex-start;
        width: 100%;
    }
    
    .bot-message {
        background-color: white;
        color: var(--ibus-primary);
        border-radius: 18px 18px 18px 0;
        padding: 12px 18px;
        max-width: 80%;
        margin-right: auto;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        position: relative;
        border-left: 3px solid var(--ibus-secondary);
    }
    
    /* Username labels with iBUS colors */
    .username-label {
        font-size: 0.85em;
        margin-bottom: 6px;
        font-weight: 600;
    }
    
    .user-label {
        text-align: right;
        color: var(--ibus-primary);
    }
    
    .bot-label {
        text-align: left;
        color: var(--ibus-secondary);
    }
    
    /* Improved timestamp styling */
    .timestamp {
        font-size: 0.7em;
        color: rgba(255, 255, 255, 0.9);
        margin-top: 5px;
        text-align: right;
        display: inline-block;
        float: right;
        clear: both;
        width: 100%;
    }
    
    .bot-message .timestamp {
        color: rgba(0, 58, 108, 0.7);
    }
    
    /* Message content with better spacing */
    .message-content {
        display: inline-block;
        width: 100%;
        margin-bottom: 8px;
        line-height: 1.4;
    }
    
    /* Enhanced animation for new messages */
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    .user-message {
        animation: slideInRight 0.3s ease-out;
    }
    
    .bot-message {
        animation: slideInLeft 0.3s ease-out;
    }
    
    /* Add subtle hover effect */
    .user-message:hover, .bot-message:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Enhanced CSS styling based on iBUS logo colors (blue and gray tones)
st.markdown("""
<style>
    /* Color palette based on iBUS logo */
    :root {
        --ibus-primary: #003A6C;     /* Dark blue from logo */
        --ibus-secondary: #0077B6;   /* Medium blue */
        --ibus-accent: #48CAE4;      /* Light blue accent */
        --ibus-light: #ADE8F4;       /* Very light blue */
        --ibus-gray: #6C757D;        /* Complementary gray */
        --ibus-light-gray: #F8F9FA;  /* Background gray */
    }
    
    /* Global styling */
    .stApp {
        background-color: #F8F9FA;
    }
    
    /* Header styling */
    h1, h2, h3 {
        color: var(--ibus-primary);
        font-family: 'Helvetica Neue', Arial, sans-serif;
    }
    
    h1 {
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    
    /* Sidebar styling */
    .css-1d391kg, .css-12oz5g7 {
        background-color: white;
        border-right: 1px solid #E9ECEF;
    }
    
    /* Button styling */
    .stButton button {
        background-color: var(--ibus-primary);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 15px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        background-color: var(--ibus-secondary);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Primary button */
    .stButton button[data-baseweb="button"][kind="primary"] {
        background-color: var(--ibus-primary);
    }
    
    /* Secondary button */
    .stButton button[data-baseweb="button"][kind="secondary"] {
        background-color: var(--ibus-gray);
    }
    
    /* Chat message styling */
    .stChatMessage {
        border-radius: 12px;
        padding: 10px;
        margin: 10px 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    /* User message */
    .stChatMessage[data-testid="stChatMessage-USER"] {
        background-color: var(--ibus-light);
        border-bottom-right-radius: 4px;
    }
    
    /* Assistant message */
    .stChatMessage[data-testid="stChatMessage-ASSISTANT"] {
        background-color: white;
        border-bottom-left-radius: 4px;
    }
    
    /* Input box styling */
    .stTextInput input {
        border-radius: 8px;
        border: 1px solid #CED4DA;
        padding: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    .stTextInput input:focus {
        border-color: var(--ibus-secondary);
        box-shadow: 0 0 0 3px rgba(0,119,182,0.2);
    }
    
    /* File uploader styling */
    .stFileUploader {
        background-color: white;
        border-radius: 8px;
        padding: 10px;
        border: 1px dashed #CED4DA;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: white;
        border-radius: 8px;
        border: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        padding: 10px 15px;
        font-weight: 500;
        color: var(--ibus-primary);
    }
    
    .streamlit-expanderContent {
        background-color: white;
        border-radius: 0 0 8px 8px;
        padding: 15px;
        border: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    /* Logo container */
    .logo-container {
        display: flex;
        align-items: center;
        padding: 15px;
        background-color: white;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    
    .logo-container img {
        height: 60px;
        margin-right: 15px;
    }
    
    .logo-container h1 {
        margin: 0;
        color: var(--ibus-primary);
    }
    
    /* Fade-in animation for elements */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Apply animations to different components */
    .stButton button {
        transition: all 0.3s ease;
    }
    
    /* Chat message animations */
    .element-container:has(.stChatMessage) {
        animation: fadeIn 0.5s ease-out forwards;
    }
    
    /* Header animations */
    h1, h2, h3 {
        animation: fadeIn 0.7s ease-out forwards;
    }
    
    /* Staggered animation delays */
    .staggered-1 { animation-delay: 0.2s; }
    .staggered-2 { animation-delay: 0.4s; }
    .staggered-3 { animation-delay: 0.6s; }
    .staggered-4 { animation-delay: 0.8s; }
    
    /* Welcome message special animation */
    .welcome-message {
        animation: fadeIn 0.8s ease-out forwards;
    }
    
    /* Options container animation */
    .options-container {
        animation: fadeIn 1s ease-out forwards;
        animation-delay: 0.5s;
    }
    
    /* Typing effect */
    .typing-effect {
        border-left: 2px solid var(--ibus-secondary);
        padding-left: 8px;
        color: var(--ibus-primary);
        font-weight: 500;
    }
    
    /* Card styling for options */
    .option-card {
        background-color: white;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
        border-left: 4px solid var(--ibus-primary);
        margin: 10px 0;
        cursor: pointer;
    }
    
    .option-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        border-left: 4px solid var(--ibus-secondary);
    }
    
    /* Follow-up suggestions styling */
    .followup-container {
        margin-top: 20px;
        padding: 15px;
        background-color: var(--ibus-light-gray);
        border-radius: 8px;
        border-left: 4px solid var(--ibus-accent);
    }
    
    /* Success message styling */
    .success-message {
        padding: 15px;
        background-color: #d4edda;
        color: #155724;
        border-radius: 8px;
        margin: 15px 0;
        border-left: 4px solid #28a745;
        animation: fadeIn 0.5s ease-out forwards;
    }
    
    /* Style buttons to look like cards */
    .stButton button {
        background-color: white !important;
        color: var(--ibus-primary) !important;
        border-radius: 8px !important;
        padding: 15px !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05) !important;
        transition: all 0.3s ease !important;
        border-left: 4px solid var(--ibus-primary) !important;
        margin: 10px 0 !important;
        text-align: left !important;
        width: 100% !important;
        height: auto !important;
        white-space: normal !important;
    }
    
    .stButton button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 6px 12px rgba(0,0,0,0.1) !important;
        border-left: 4px solid var(--ibus-secondary) !important;
    }
    
    /* Make follow-up buttons more compact */
    .followup-container + div .stButton button {
        padding: 10px 15px !important;
        font-size: 0.9rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Add more CSS for typing indicator
st.markdown("""
<style>
    /* Improved typing indicator with iBUS colors */
    .typing-indicator {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        height: 24px;
        padding-left: 10px;
    }
    
    .typing-indicator span {
        height: 8px;
        width: 8px;
        background-color: var(--ibus-secondary);
        border-radius: 50%;
        display: inline-block;
        margin: 0 3px;
        opacity: 0.4;
    }
    
    .typing-indicator span:nth-child(1) {
        animation: pulse 1s infinite;
    }
    
    .typing-indicator span:nth-child(2) {
        animation: pulse 1s infinite 0.2s;
    }
    
    .typing-indicator span:nth-child(3) {
        animation: pulse 1s infinite 0.4s;
    }
    
    @keyframes pulse {
        0% { opacity: 0.4; transform: scale(1); }
        50% { opacity: 1; transform: scale(1.2); }
        100% { opacity: 0.4; transform: scale(1); }
    }
</style>
""", unsafe_allow_html=True)

# Add custom CSS specifically for timestamp
st.markdown("""
<style>
    /* Timestamp styling - make it more robust */
    .timestamp {
        font-size: 0.7em;
        color: black;
        margin-top: 5px;
        text-align: right;
        display: inline-block;
        float: right;
        clear: both;
        width: 100%;
    }
    
    /* Ensure message content and timestamp don't overlap */
    .message-content {
        display: inline-block;
        width: 100%;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Add custom CSS for file attachment button
st.markdown("""
<style>
    /* File attachment button styling */
    .attachment-button {
        position: absolute;
        right: 60px;
        bottom: 10px;
        background color: none;
        border: none;
        color: #0084ff;
        font-size: 20px;
        cursor: pointer;
        z-index: 100;
        padding: 5px;
        border-radius: 50%;
        transition: background-color 0.2s;
    }
    
    /* iBUS Mascot styling - fixed positioning */
    .ibus-mascot {
        position: absolute;
        left: 10px;
        bottom: 10px;
        z-index: 100;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 30px;
        height: 30px;
        overflow: visible;
    }
    
    .ibus-mascot img {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        object-fit: cover;
    }
    
    .attachment-button:hover {
        background-color: rgba(0, 132, 255, 0.1);
    }
    
    /* Chat input container to make room for attachment button */
    .stChatInputContainer {
        position: relative;
    }
    
    /* File upload area styling */
    .file-upload-area {
        margin-bottom: 10px;
        padding: 10px;
        border-radius: 8px;
        background-color: #f7f7f7;
    }
</style>
""", unsafe_allow_html=True)

# Add CSS for user avatar
st.markdown("""
<style>
    /* User avatar styling */
    .user-avatar {
        position: absolute;
        right: 10px;
        bottom: 10px;
        z-index: 100;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 30px;
        height: 30px;
        overflow: visible;
    }
    
    .user-avatar img {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        object-fit: cover;
    }
    
    /* Update user message to make room for avatar */
    .user-message {
        position: relative;
        padding-right: 40px; /* Add space for avatar */
    }
</style>
""", unsafe_allow_html=True)

# Define file extension lists
EXTS = ['pdf', 'docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls', 'csv']
IMAGE_EXTS = ['jpg', 'jpeg', 'png', 'gif', 'bmp']

# Configure Gemini
genai.configure(api_key="AIzaSyAc2xYCF0uCE6Ti3sTjc9-wxyvI5hHtBSM")

# Text Extraction
def extract_text(p,ext):
    try:
        if ext=='pdf': return "".join(pg.get_text() for pg in fitz.open(p))
        if ext in ('docx','doc'): return "\n".join(par.text for par in docx.Document(p).paragraphs)
        if ext in ('pptx','ppt'): return "\n".join(s.text for sl in Presentation(p).slides for s in sl.shapes if hasattr(s,'text'))
        if ext in ('xlsx','xls'):
            df = pd.read_excel(p)
            st.session_state.tables[os.path.basename(p)] = df
            return df.to_string()
        if ext=='csv':
            df = pd.read_csv(p)
            st.session_state.tables[os.path.basename(p)] = df
            return df.to_string()
    except Exception as e: st.error(f"{os.path.basename(p)}: {e}")

def generate_user_avatar(username):
    """Generate a user avatar with the first letter of their name"""
    if not username:
        return ""
    
    # Get first letter and capitalize it
    first_letter = username[0].upper()
    
    # Generate a consistent color based on the username
    hash_value = sum(ord(c) for c in username)
    hue = hash_value % 360  # 0-359 degrees on color wheel
    
    # Create a vibrant but not too light color (HSL format)
    bg_color = f"hsl({hue}, 70%, 60%)"
    
    # Create the SVG avatar
    svg = f'''
    <svg width="30" height="30" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
        <circle cx="15" cy="15" r="15" fill="{bg_color}"/>
        <text x="15" y="20" font-family="Arial, sans-serif" font-size="16" 
              font-weight="bold" fill="white" text-anchor="middle">{first_letter}</text>
    </svg>
    '''
    
    # Return the SVG as a data URI
    return f'<img src="data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}" alt="User Avatar">'

def get_history_path(username):
    safe_username = re.sub(r'\W+', '_', username.lower())
    return os.path.join(HISTORY_DIR, f"{safe_username}.pkl")

def save_chat_history(username, chat_history):
    path = get_history_path(username)
    with open(path, 'wb') as f:
        pickle.dump(chat_history, f)

def load_chat_history(username):
    path = get_history_path(username)
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return pickle.load(f)
    return []





# Ask Gemini with real-time data capability
def ask_gemini(q, ctx, images=None):
    try:
        mdl = genai.GenerativeModel('gemini-1.5-flash')
        
        # Check if the question is asking for real-time or current information
        real_time_indicators = [
            "current", "latest", "today", "now", "recent", "update", 
            "real-time", "real time", "live", "news", "weather", "stock", 
            "price", "market", "trending", "happening", "this week",
            "this month", "this year", "forecast", "prediction"
        ]
        
        # Detect if this is a general knowledge question or iBUS specific
        ibus_indicators = ["ibus", "network", "telecom", "company", "service", "infrastructure"]
        is_ibus_related = any(indicator in q.lower() for indicator in ibus_indicators)
        
        # Check if it needs real-time data
        needs_real_time = any(indicator in q.lower() for indicator in real_time_indicators)
        
        # For general knowledge questions that aren't about iBUS, we can ignore the context
        if not is_ibus_related and "what is" in q.lower() or "how to" in q.lower() or "who is" in q.lower():
            # This is likely a general knowledge question
            ctx = "You are a helpful assistant that can answer general knowledge questions."
        
        # Ensure we have context for iBUS-related questions
        if is_ibus_related and (not ctx or ctx == "iBUS Networks is a telecommunications company."):
            # Check if we have document content in session state
            if st.session_state.documents_content:
                ctx = "\n".join(f"{n}:\n{c}" for n,c in st.session_state.documents_content.items())
        
        # Prepare prompt with context and explicit instruction not to repeat the question
        base_prompt = f"""Context:
{ctx}

Question: {q}

Important: Provide a direct answer without repeating the question. Do not use formats like "Question: ... Answer: ...". Just give the answer. 
If the answer is not directly available in the context, use your knowledge to provide the most accurate and helpful response. 
Never say that you don't have information or that the answer isn't in the provided documents - always try to give a helpful response."""
        
        # If real-time data is needed, add a web search component
        if needs_real_time:
            try:
                import requests
                from bs4 import BeautifulSoup
                from datetime import datetime
                
                # Add current date and time information
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                real_time_info = f"Current date and time: {current_time}\n\n"
                
                # Attempt to get some basic real-time information
                search_terms = q.replace("?", "").replace("!", "").replace(".", "")
                search_url = f"https://news.google.com/rss/search?q={search_terms}&hl=en-US&gl=US&ceid=US:en"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                response = requests.get(search_url, headers=headers, timeout=5)
                
                # Add the real-time information to the prompt with the same instruction
                prompt = f"""{base_prompt}

Real-time information:
{real_time_info}

Please provide an up-to-date answer based on both the context and the real-time information. If the question is about general knowledge and not related to iBUS Networks, focus on the real-time information. Remember, do not repeat the question in your answer and never say you don't have information."""
            except Exception as e:
                # If web search fails, fall back to the base prompt with a note
                prompt = f"{base_prompt}\n\nNote: I attempted to search for real-time information but encountered an error: {str(e)}. I'll answer based on my available knowledge."
        else:
            prompt = base_prompt
        
        if images:
            parts = [{"text": prompt}] + [
                {"inline_data": {"mime_type": "image/jpeg", "data": img}} for img in images
            ]
            response = mdl.generate_content(contents=[{"parts": parts}]).text
        else:
            response = mdl.generate_content(contents=[{"parts":[{"text": prompt}]}]).text
        
        # Clean up the response to remove any question repetition and leading/trailing asterisks
        if "Question:" in response and "Answer:" in response:
            response = response.split("Answer:", 1)[1].strip()
        
        # Remove any leading/trailing asterisks that might cause formatting issues
        response = response.strip('*')
        
        return response
    except Exception as e: 
        # Check if it's a rate limit error
        error_str = str(e)
        if "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower():
            return """I'm currently experiencing high demand and have reached my API rate limit. 

Please try again in a few minutes, or consider:
1. Asking simpler questions
2. Breaking your request into smaller parts
3. Using fewer images in your queries

This is a temporary limitation of the free tier API usage."""
        else:
            return f"Error: {e}"

# Generate follow-up questions based on the conversation
def generate_followups(q, a, ctx):
    try:
        # Create a more detailed prompt for generating specific follow-up questions
        prompt = f"""Based on this conversation:
User: {q}
Assistant: {a}

Generate 3 specific, detailed follow-up questions the user might want to ask next.
Each question should:
1. Be directly related to the topic discussed
2. Ask for more specific details or examples
3. Explore a natural next step in the conversation
4. Be phrased as a complete question (with a question mark)
5. Be concise (under 10 words if possible)
6. Avoid using the word "you" - phrase questions objectively

Format as a simple numbered list (1. 2. 3.) with no additional text."""
        
        try:
            response = ask_gemini(prompt, ctx)
            # Check if we got a rate limit error response
            if "rate limit" in response.lower() or "quota" in response.lower():
                raise Exception("Rate limit exceeded")
                
            questions = [qq.strip().strip('*') for qq in re.findall(r'\d+\.\s*(.*?)\s*(?=\n\d+\.|\n\n|$)', response, re.DOTALL) if qq.strip()]
            
            # Ensure questions are specific and end with question marks
            specific_questions = []
            for question in questions[:3]:
                # Add a question mark if missing
                if not question.endswith('?'):
                    question += '?'
                
                # Ensure the question is not too generic
                generic_patterns = [
                    r'^tell me more',
                    r'^can you explain',
                    r'^what else',
                    r'^how does',
                    r'^why is'
                ]
                
                is_generic = any(re.search(pattern, question.lower()) for pattern in generic_patterns)
                
                if is_generic and len(ctx) > 100:
                    # Try to make it more specific by adding a keyword from the context
                    keywords = re.findall(r'\b[A-Z][a-zA-Z]{4,}\b', ctx)
                    if keywords:
                        # Use the first keyword that's not already in the question
                        for keyword in keywords:
                            if keyword.lower() not in question.lower():
                                question = question.replace('?', f' about {keyword}?')
                                break
                
                specific_questions.append(question)
            
            # If we don't have enough questions, generate some based on the context
            if len(specific_questions) < 2:
                raise Exception("Not enough specific questions generated")
                
            return specific_questions[:3]  # Return exactly 3 questions
            
        except Exception as e:
            # If we hit an error, try to generate more specific fallback questions
            print(f"Error in follow-up generation: {e}")
            
            # Extract key terms from the question and answer
            combined_text = f"{q} {a}"
            words = combined_text.split()
            # Filter out common words and get potential key terms
            common_words = ['the', 'and', 'is', 'in', 'to', 'a', 'of', 'for', 'with', 'on', 'at']
            key_terms = [w for w in words if len(w) > 4 and w.lower() not in common_words][:3]
            
            if key_terms:
                return [
                    f"What are the benefits of {key_terms[0]}?",
                    f"How does {key_terms[0]} compare to alternatives?",
                    f"Can you provide examples of {key_terms[0]} in use?"
                ]
            else:
                return [
                    f"What specific features does this offer?",
                    f"How is this implemented in practice?",
                    f"What are the next steps I should take?"
                ]
            
    except Exception as e:
        print(f"Error generating follow-ups: {e}")
        # Return more specific generic questions if there's an error
        return [
            f"What are the key benefits of this approach?",
            f"How does this compare to alternatives?",
            f"Can you provide a specific example?"
        ]

# Remove graph-related functions
def generate_graph_from_request(user_prompt, df_dict):
    """Detect if user wants a chart and return available dataframes"""
    # Always return False to disable chart functionality
    return False, None

# Remove chart creation function
def create_interactive_chart(df, chart_type, x_col, y_col, title=None):
    """Placeholder function that does nothing"""
    return None

# Remove chart export function
def export_chart(fig, format_type):
    """Placeholder function that does nothing"""
    return None

# Function to check if a response indicates a rate limit error
def is_rate_limit_error(response):
    rate_limit_indicators = [
        "429", "rate limit", "quota", "exceeded", "try again", "temporary limitation"
    ]
    return any(indicator in response.lower() for indicator in rate_limit_indicators)

# Function to handle predefined options
def handle_predefined_option(option):
    """Handle clicks on predefined option buttons"""
    if option == "Upload Files":
        st.session_state['show_file_upload'] = True
        message = "Please use the sidebar to upload your files for analysis."
    elif option == "What is iBUS?":
        message = "iBUS Networks is a leading telecommunications company specializing in innovative connectivity solutions for businesses and organizations."
    elif option == "Services offered":
        message = "iBUS Networks offers a range of services including:\n\n- High-speed internet connectivity\n- Network infrastructure solutions\n- Cloud services\n- Managed IT services\n- Telecommunications consulting"
    elif option == "Contact information":
        message = "You can contact iBUS Networks through:\n\n- Email: info@ibusnetworks.com\n- Phone: +1-555-IBUS-NET\n- Website: www.ibusnetworks.com"
    elif option == "Help with this chatbot":
        message = "This chatbot can help you with:\n\n1. Information about iBUS Networks and services\n2. Analyzing documents you upload\n3. Creating visualizations from data files\n4. Answering questions about telecommunications\n\nJust type your question or upload files to get started!"
    else:
        message = f"You selected: {option}"
    
    # Add the user's selection to chat history
    st.session_state.chat_history.append({"role":"user","content":option})
    # Add the response to chat history
    st.session_state.chat_history.append({"role":"assistant","content":message})
    
    # Generate follow-up questions based on this interaction
    ctx = "iBUS Networks is a telecommunications company."
    st.session_state['current_followups'] = generate_followups(option, message, ctx)
    
    # Turn off the options display after selection
    st.session_state['show_options'] = False

# Add a loading animation function
def show_loading_animation(seconds=1.5):
    """Display a loading animation for the specified number of seconds"""
    progress_placeholder = st.empty()
    progress_bar = progress_placeholder.progress(0)
    
    for i in range(100):
        time.sleep(seconds/100)
        progress_bar.progress(i + 1)
    
    progress_placeholder.empty()

# Session State Init
for k,v in {'chat_history':[],'documents_content':{},'processed_files':[],'images':[],'tables':{},'user_name':None,'asked_name':False,'file_summaries':{},'show_file_upload':False,'message_timestamps':{},'files_displayed':False}.items():
    st.session_state.setdefault(k,v)

# Ask for name if not already asked
if not st.session_state.user_name:
    if not st.session_state.asked_name:
        # Get current timestamp
        current_time = datetime.now().strftime("%I:%M %p")
        
        # Add initial greeting to chat history if it's empty
        greeting_msg = "Hello! I'm the iBUS chatbot. Can I know your name, please?"
        
        # Create a placeholder for the greeting
        greeting_placeholder = st.empty()
        
        # Add a slight delay before showing the greeting
        time.sleep(0.8)
        
        # Display the greeting with a typing effect
        for i in range(1, len(greeting_msg) + 1):
            greeting_placeholder.markdown(f"<div class='typing-effect'>{greeting_msg[:i]}</div>", unsafe_allow_html=True)
            time.sleep(0.03)  # Adjust typing speed
        
        # Replace the placeholder with the chat message (don't create a new one)
        greeting_placeholder.markdown(f"""
        <div class="chat-container">
            <div class="username-label bot-label">iChat</div>
            <div class="bot-message-container">
                <div class="bot-message">
                    <div class="message-content">{greeting_msg}</div>
                    <div class="timestamp">{current_time}</div>
                    <div class="ibus-mascot">
                        <img src="https://media.licdn.com/dms/image/v2/C560BAQF4xkHYB4X3Fw/company-logo_200_200/company-logo_200_200/0/1672579746218/ibus_networks_logo?e=1750896000&v=beta&t=CUlZ2YnRxrYwUkEiQSbPHPQdXtEGxZ_5JOs9Oxm5IQM" alt="iBUS Mascot">
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add to session state only once with timestamp
        message_id = f"assistant_{len(st.session_state.chat_history)}"
        st.session_state.message_timestamps[message_id] = current_time
        st.session_state.chat_history.append({"role":"assistant","content":greeting_msg, "id": message_id})
        st.session_state.asked_name = True
    
    # Don't display chat history here - it will duplicate the greeting
    # Instead, only show the name input field
    user_name = st.text_input("", placeholder="Enter your name here...", key="name_input")
    if user_name:
        st.session_state.user_name = user_name
        # Load previous history
        st.session_state.chat_history = load_chat_history(user_name)

    if user_name:
        # Get current timestamp for user response
        user_time = datetime.now().strftime("%I:%M %p")
        
        st.session_state.user_name = user_name
        # Add user response to chat with timestamp
        message_id = f"user_{len(st.session_state.chat_history)}"
        st.session_state.message_timestamps[message_id] = user_time
        st.session_state.chat_history.append({"role":"user","content":user_name, "id": message_id})
        
        # Get timestamp for welcome message
        welcome_time = datetime.now().strftime("%I:%M %p")
        
        # Add welcome message with timestamp
        welcome_msg = f"👋 Welcome {user_name}! How can I assist you today?"
        message_id = f"assistant_{len(st.session_state.chat_history)}"
        st.session_state.message_timestamps[message_id] = welcome_time
        st.session_state.chat_history.append({"role":"assistant","content":welcome_msg, "id": message_id})
        # Set a flag to show predefined options after welcome
        st.session_state['show_options'] = True
        # Add a flag to trigger staggered animations
        st.session_state['show_staggered_animation'] = True
        st.rerun()
else:
    # Display full chat history if we already have the user's name
    for i, m in enumerate(st.session_state.chat_history):
        # Get timestamp for this message
        message_id = m.get('id', f"{m['role']}_{i}")
        timestamp = st.session_state.message_timestamps.get(message_id, "")
        
        if m['role'] == 'user':
            # Display user messages on the right
            st.markdown(f"""
            <div class="chat-container">
                <div class="username-label user-label">{st.session_state.user_name}</div>
                <div class="user-message-container">
                    <div class="user-message">
                        <div class="message-content">{m['content']}</div>
                        <div class="timestamp">{timestamp}</div>
                        <div class="user-avatar">
                            {generate_user_avatar(st.session_state.user_name)}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Display assistant messages on the left
            content = m['content']
            # Remove any "Question: ... Answer:" format if it exists
            if "Question:" in content and "Answer:" in content:
                content = content.split("Answer:", 1)[1].strip()
            
            # Remove any leading asterisks that might be causing the stars to appear
            content = content.lstrip('*')
            
            st.markdown(f"""
            <div class="chat-container">
                <div class="username-label bot-label">iChat</div>
                <div class="bot-message-container">
                    <div class="bot-message">
                        <div class="message-content">{content}</div>
                        <div class="timestamp">{timestamp}</div>
                        <div class="ibus-mascot">
                            <img src="https://media.licdn.com/dms/image/v2/C560BAQF4xkHYB4X3Fw/company-logo_200_200/company-logo_200_200/0/1672579746218/ibus_networks_logo?e=1750896000&v=beta&t=CUlZ2YnRxrYwUkEiQSbPHPQdXtEGxZ_5JOs9Oxm5IQM" alt="iBUS Mascot">
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# Show predefined options after welcome message if flag is set
if st.session_state.get('show_options', False) and not st.session_state.processed_files:
    # Add a slight delay before showing options
    time.sleep(0.5)
    
    st.markdown("""
    <div class="options-container">
        <h3 style="color: #003A6C; margin-bottom: 15px;">
            <span style="margin-right: 8px;">💬</span>How can I help you today?
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Define the predefined options
    options = [
        {"title": "What is iBUS?", "icon": "🏢", "desc": "Learn about our company"},
        {"title": "Services offered", "icon": "🛠️", "desc": "Explore our service offerings"},
        {"title": "Contact information", "icon": "📞", "desc": "Get in touch with iBUS Networks"},
        {"title": "Help with this chatbot", "icon": "❓", "desc": "Learn how to use this chatbot"}
    ]
    
    # Create a single row with 4 columns for all options
    cols = st.columns(4)

    # Display all options in a single row
    for i, option in enumerate(options):
        with cols[i]:
            option_id = f"option_{i}"
            if st.button(f"{option['icon']} {option['title']}", key=option_id, help=option['desc']):
                # Add the user's selection to chat history
                st.session_state.chat_history.append({"role":"user","content":option['title']})
                
                # Get response for this option
                if option['title'] == "What is iBUS?":
                    message = "iBUS Networks is a leading telecommunications company specializing in innovative connectivity solutions for businesses and organizations."
                elif option['title'] == "Services offered":
                    message = "iBUS Networks offers a range of services including:\n\n- High-speed internet connectivity\n- Network infrastructure solutions\n- Cloud services\n- Managed IT services\n- Telecommunications consulting"
                elif option['title'] == "Contact information":
                    message = "You can contact iBUS Networks through:\n\n- Email: info@ibusnetworks.com\n- Phone: +1-555-IBUS-NET\n- Website: www.ibusnetworks.com"
                elif option['title'] == "Help with this chatbot":
                    message = "This chatbot can help you with:\n\n1. Information about iBUS Networks and services\n2. Analyzing documents you upload\n3. Creating visualizations from data files\n4. Answering questions about telecommunications\n\nJust type your question or upload files to get started!"
                else:
                    message = f"You selected: {option['title']}"
                
                # Add the response to chat history
                st.session_state.chat_history.append({"role":"assistant","content":message})
                
                # Generate follow-up questions based on this interaction
                ctx = "iBUS Networks is a telecommunications company."
                st.session_state['current_followups'] = generate_followups(option['title'], message, ctx)
                
                # Turn off the options display after selection
                st.session_state['show_options'] = False
                
                st.rerun()  # Refresh the chat history display

# Only show sidebar upload if user has entered their name and clicked upload option
if False:  # Changed from conditional to always False to disable sidebar upload
    # This code will never execute now
    pass
else:
    # Define empty variables to avoid reference errors
    uploads = None
    folder = None
    process_button = False
    clear_button = False

if process_button and (uploads or folder):
    processed_files_count = 0
    file_summaries = []
    file_summaries_text = ""  # Initialize the variable
    
    # Process uploaded files
    for src in uploads or []:
        ext = os.path.splitext(src.name)[1][1:].lower()
        if ext in IMAGE_EXTS:
            try:
                img = Image.open(src)
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG')
                img_bytes = img_byte_arr.getvalue()
                st.session_state.images.append(img_bytes)
                st.session_state.processed_files.append(src.name)
                processed_files_count += 1
                file_summaries.append(f"- Processed image: {src.name}")
            except Exception as e:
                st.error(f"Error processing image {src.name}: {e}")
        elif ext in EXTS:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
            tmp.write(src.getvalue())
            tmp.close()
            txt = extract_text(tmp.name, ext)
            if txt:
                st.session_state.documents_content[src.name] = txt
                st.session_state.processed_files.append(src.name)
                processed_files_count += 1
                
                # Generate a brief summary for the text document
                try:
                    summary_prompt = f"Provide a very brief 3-line summary of this document content:\n\n{txt[:2000]}..."
                    summary = ask_gemini(summary_prompt, "", None).strip()
                    # Ensure it's not too long
                    if len(summary.split('\n')) > 3:
                        summary = '\n'.join(summary.split('\n')[:3])
                    st.session_state['file_summaries'][src.name] = summary
                    file_summaries.append(f"📄 **{src.name}**: {summary}")
                except Exception as e:
                    summary = f"Document processed. Contains {len(txt.split())} words."
                    st.session_state['file_summaries'][src.name] = summary
                    file_summaries.append(f"📄 **{src.name}**: {summary}")
    
    # Process files from folder path if provided
    if folder and os.path.isdir(folder):
        # Get all files in the folder with supported extensions
        folder_files = []
        for ext in EXTS + IMAGE_EXTS:
            folder_files.extend(glob.glob(os.path.join(folder, f"*.{ext}")))
        
        for file_path in folder_files:
            file_name = os.path.basename(file_path)
            ext = os.path.splitext(file_name)[1][1:].lower()
            
            if ext in IMAGE_EXTS:
                try:
                    img = Image.open(file_path)
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='JPEG')
                    img_bytes = img_byte_arr.getvalue()
                    st.session_state.images.append(img_bytes)
                    st.session_state.processed_files.append(file_name)
                    processed_files_count += 1
                    
                    # Add summary for the image
                    summary = f"Image processed. Visual content available for analysis."
                    st.session_state['file_summaries'][file_name] = summary
                    file_summaries_text += f"📷 **{file_name}**: {summary}\n\n"
                except Exception as e:
                    st.error(f"Error processing image {file_name}: {e}")
            else:
                try:
                    txt = extract_text(file_path, ext)
                    if txt:
                        st.session_state.documents_content[file_name] = txt
                        st.session_state.processed_files.append(file_name)
                        processed_files_count += 1
                        
                        # Generate a brief summary for the text document
                        try:
                            summary_prompt = f"Provide a very brief 3-line summary of this document content:\n\n{txt[:2000]}..."
                            summary = ask_gemini(summary_prompt, "", None).strip()
                            # Ensure it's not too long
                            if len(summary.split('\n')) > 3:
                                summary = '\n'.join(summary.split('\n')[:3])
                            st.session_state['file_summaries'][file_name] = summary
                            file_summaries_text += f"📄 **{file_name}**: {summary}\n\n"
                        except Exception as e:
                            summary = f"Document processed. Contains {len(txt.split())} words."
                            st.session_state['file_summaries'][file_name] = summary
                            file_summaries_text += f"📄 **{file_name}**: {summary}\n\n"
                except Exception as e:
                    st.error(f"Error processing file {file_name}: {e}")
    elif folder:
        st.sidebar.error(f"Folder path not found: {folder}")
    
    st.sidebar.success(f"✅ Processed {processed_files_count} files")
    
    # Create the file_summaries_text from the file_summaries list
    if file_summaries:
        file_summaries_text = "\n\n".join(file_summaries)
    else:
        file_summaries_text = "No files were successfully processed."
    
    # Display file summaries in the main area
    if processed_files_count > 0:
        st.markdown(f"""
        <div class="success-message">
        <div style="padding: 15px; background-color: #d4edda; border-radius: 5px; 
                    margin: 10px 0; animation: fadeIn 0.7s ease-out;">
            <h3 style="margin: 0; color: #155724;">📄 Processed {processed_files_count} Files</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Use an accordion for file summaries with animation
        for file_name, summary in st.session_state['file_summaries'].items():
            with st.expander(f"📎 {file_name}"):
                st.markdown(f"""
                <div style="animation: fadeIn 0.5s ease-out;">
                    <p><strong>Summary:</strong><br>{summary}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Add the summaries to the chat history
    if processed_files_count > 0:
        chat_message = f"**Files Processed:**\n\n{file_summaries_text}"
        st.markdown(f"**iChat**: {chat_message}")
        st.session_state.chat_history.append({"role":"assistant","content":chat_message})
    
    # After processing files and adding to chat history, generate follow-up questions
    # Get the combined context from all documents
    combined_ctx = "\n".join(f"{n}:\n{c}" for n,c in st.session_state.documents_content.items())
    
    # Generate a generic question about the files to use for follow-up generation
    generic_q = "What information is in these files?"
    generic_ans = "I've processed your files and extracted their content. You can now ask me questions about them."
    
    # Generate follow-up questions based on the file content
    st.session_state['current_followups'] = generate_followups(generic_q, generic_ans, combined_ctx)
    
    # Reset the files_displayed flag to show the newly uploaded files
    st.session_state.files_displayed = False
    
    # Rerun to update the UI with new follow-up questions
    st.rerun()  # Refresh the chat history display

if clear_button:
    st.session_state.processed_files = []
    st.session_state.documents_content = {}
    st.session_state.images = []
    st.session_state.tables = {}
    st.session_state.chat_history = []
    st.session_state.files_displayed = False
    st.rerun()  # Refresh the chat history display

# Main Area Chat Context
if st.session_state.processed_files:
    st.markdown('<h3>💬 Ask a question about your documents</h3>', unsafe_allow_html=True)
    ctx = "\n".join(f"{n}:\n{c}" for n,c in st.session_state.documents_content.items())
else:
    ctx = "iBUS Networks is a telecommunications company."  # Replace with actual IBUS_INFO

# Show Uploaded Images - only if they haven't been displayed before
if st.session_state.images and not st.session_state.files_displayed:
    st.subheader("🖼️ Uploaded Images")
    cols = st.columns(min(3, len(st.session_state.images)))
    for i, img_bytes in enumerate(st.session_state.images):
        with cols[i % 3]:
            st.image(Image.open(io.BytesIO(img_bytes)), width=200)
    
    # Mark files as displayed so they don't show again
    st.session_state.files_displayed = True

# Predefined Topics
if not st.session_state.chat_history and not st.session_state.processed_files:
    st.markdown('<h3>How can we help you today?</h3>', unsafe_allow_html=True)
    
    # Create a row of buttons for predefined topics
    USER_TOPICS = ["What is iBUS?", "Services offered", "Contact information"]  # Replace with actual topics
    cols = st.columns(len(USER_TOPICS))
    for i, topic in enumerate(USER_TOPICS):
        if cols[i].button(f"📝 {topic}", key=f"topic_{i}"):
            # Get current timestamp
            current_time = datetime.now().strftime("%I:%M %p")
            
            # Add user question to chat history with timestamp
            message_id = f"user_{len(st.session_state.chat_history)}"
            st.session_state.message_timestamps[message_id] = current_time
            st.session_state.chat_history.append({"role":"user","content":topic, "id": message_id})
            
            # Immediately display the user's selection with timestamp using the new style
            st.markdown(f"""
            <div class="chat-container">
                <div class="username-label user-label">{st.session_state.user_name}</div>
                <div class="user-message-container">
                    <div class="user-message">
                        <div class="message-content">{topic}</div>
                        <div class="timestamp">{current_time}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show a typing indicator while generating the response
            typing_placeholder = st.empty()
            typing_placeholder.markdown("""
            <div class="chat-container">
                <div class="username-label bot-label">iChat</div>
                <div class="bot-message-container">
                    <div class="bot-message" style="background-color: #f0f2f5;">
                        <div class="typing-indicator">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Make sure we're using the most up-to-date context
            if st.session_state.processed_files:
                current_ctx = "\n".join(f"{n}:\n{c}" for n,c in st.session_state.documents_content.items())
            else:
                current_ctx = "iBUS Networks is a telecommunications company."  # Replace with actual IBUS_INFO
            
            # Get answer from Gemini
            ans = ask_gemini(topic, current_ctx, st.session_state.images if st.session_state.images else None)
            
            # Make sure the answer doesn't have the question format
            if "Question:" in ans and "Answer:" in ans:
                ans = ans.split("Answer:", 1)[1].strip()
            
            # Get response timestamp
            response_time = datetime.now().strftime("%I:%M %p")
            
            # Remove the typing indicator and display the answer with timestamp using the new style
            typing_placeholder.markdown(f"""
            <div class="chat-container">
                <div class="username-label bot-label">iChat</div>
                <div class="bot-message-container">
                    <div class="bot-message">
                        <div class="message-content">{ans}</div>
                        <div class="timestamp">{response_time}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Add the clean answer to chat history with timestamp
            message_id = f"assistant_{len(st.session_state.chat_history)}"
            st.session_state.message_timestamps[message_id] = response_time
            st.session_state.chat_history.append({"role":"assistant","content":ans, "id": message_id})
            
            # Generate follow-up questions
            st.session_state['current_followups'] = generate_followups(topic, ans, current_ctx)
            
            st.rerun()  # Refresh the chat history display

# Chat Input - only show if we have the user's name
if st.session_state.user_name:
    if q := st.chat_input("Type your question here..."):
        # Get current timestamp
        current_time = datetime.now().strftime("%I:%M %p")  # 12-hour format with AM/PM
        
        # Add user question to chat history with timestamp
        message_id = f"user_{len(st.session_state.chat_history)}"
        st.session_state.message_timestamps[message_id] = current_time
        st.session_state.chat_history.append({"role":"user","content":q, "id": message_id})
        
        # Immediately display the user's question with timestamp using the new style
        st.markdown(f"""
        <div class="chat-container">
            <div class="username-label user-label">{st.session_state.user_name}</div>
            <div class="user-message-container">
                <div class="user-message">
                    <div class="message-content">{q}</div>
                    <div class="timestamp">{current_time}</div>
                    <div class="user-avatar">
                        {generate_user_avatar(st.session_state.user_name)}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Show a typing indicator while generating the response
        typing_placeholder = st.empty()
        typing_placeholder.markdown("""
        <div class="chat-container">
            <div class="username-label bot-label">iChat</div>
            <div class="bot-message-container">
                <div class="bot-message" style="background-color: #f0f2f5; position: relative;">
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                    <div class="ibus-mascot">
                        <img src="https://media.licdn.com/dms/image/v2/C560BAQF4xkHYB4X3Fw/company-logo_200_200/company-logo_200_200/0/1672579746218/ibus_networks_logo?e=1750896000&v=beta&t=CUlZ2YnRxrYwUkEiQSbPHPQdXtEGxZ_5JOs9Oxm5IQM" alt="iBUS Mascot">
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Make sure we're using the most up-to-date context
        if st.session_state.processed_files:
            ctx = "\n".join(f"{n}:\n{c}" for n,c in st.session_state.documents_content.items())
        else:
            ctx = "iBUS Networks is a telecommunications company."  # Default context

        # Check if it's a chart request - replaced with always False
        is_chart_request, available_dfs = False, None

        if is_chart_request and available_dfs:
            # This block will never execute now
            pass
        elif is_chart_request:
            # This block will never execute now
            pass
        else:
            # For non-chart questions, use Gemini with the full context
            ans = ask_gemini(q, ctx, st.session_state.images if st.session_state.images else None)
            
            # Make sure the answer doesn't have the question format
            if "Question:" in ans and "Answer:" in ans:
                ans = ans.split("Answer:", 1)[1].strip()
                
            # Make sure we don't show chart UI for non-chart questions
            st.session_state['show_chart_ui'] = False

        # Get response timestamp
        response_time = datetime.now().strftime("%I:%M %p")
        
        # Remove the typing indicator and display the answer with timestamp using the new style
        typing_placeholder.markdown(f"""
        <div class="chat-container">
            <div class="username-label bot-label">iChat</div>
            <div class="bot-message-container">
                <div class="bot-message">
                    <div class="message-content">{ans}</div>
                    <div class="timestamp">{response_time}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add the clean answer to chat history with timestamp
        message_id = f"assistant_{len(st.session_state.chat_history)}"
        st.session_state.message_timestamps[message_id] = response_time
        st.session_state.chat_history.append({"role":"assistant","content":ans, "id": message_id})
        
        # Generate follow-up questions
        st.session_state['current_followups'] = generate_followups(q, ans, ctx)
        
        st.rerun()  # Refresh the chat history display

# Function to display dual responses and let user choose
def display_dual_responses(question, ctx, images=None):
    # Generate two different responses
    response1 = ask_gemini(question, ctx, images)
    response2 = ask_gemini(question, ctx, images)
    
    # Get current timestamp
    response_time = datetime.now().strftime("%I:%M %p")
    
    # Display both responses side by side
    cols = st.columns(2)
    
    with cols[0]:
        st.markdown(f"""
        <div class="chat-container">
            <div class="username-label bot-label">Option A</div>
            <div class="bot-message-container">
                <div class="bot-message">
                    <div class="message-content">{response1}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Choose Option A"):
            return response1, response_time
            
    with cols[1]:
        st.markdown(f"""
        <div class="chat-container">
            <div class="username-label bot-label">Option B</div>
            <div class="bot-message-container">
                <div class="bot-message">
                    <div class="message-content">{response2}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Choose Option B"):
            return response2, response_time
    
    return None, None

# Initialize chart UI session state if not present
if 'show_chart_ui' not in st.session_state:
    st.session_state['show_chart_ui'] = False
if 'available_dfs' not in st.session_state:
    st.session_state['available_dfs'] = {}

# Display chart UI if needed - replaced with empty block to disable functionality
if st.session_state.get('show_chart_ui', False) and st.session_state.get('available_dfs'):
    # Chart UI disabled
    st.session_state['show_chart_ui'] = False

# Display follow-up suggestions if available
if 'current_followups' in st.session_state and st.session_state['current_followups']:
    st.markdown('<div class="followup-container"><h4>Follow-up Questions</h4></div>', unsafe_allow_html=True)
    
    # Use all available follow-up questions (up to 3) instead of adding "Upload Files"
    followup_questions = st.session_state['current_followups'].copy()
    # Make sure we don't have more than 3 options
    if len(followup_questions) > 3:
        followup_questions = followup_questions[:3]
    
    # Create a row of columns for the follow-up questions
    cols = st.columns(len(followup_questions))
    
    # Store the clicked follow-up question
    clicked_followup = None
    
    # Display each follow-up question in its own column
    for i, fq in enumerate(followup_questions):
        with cols[i]:
            # Use a unique key for each follow-up
            followup_id = f"followup_{i}_{hash(fq)}_{len(st.session_state.chat_history)}"
            if st.button(fq, key=followup_id):
                clicked_followup = fq
    
    # Process the clicked follow-up question outside the column context
    if clicked_followup:
        # Get current timestamp
        current_time = datetime.now().strftime("%I:%M %p")
        
        # Add to chat history with timestamp
        message_id = f"user_{len(st.session_state.chat_history)}"
        st.session_state.message_timestamps[message_id] = current_time
        st.session_state.chat_history.append({"role":"user","content":clicked_followup, "id": message_id})
        
        # Show a typing indicator while generating the response
        typing_placeholder = st.empty()
        typing_placeholder.markdown("""
        <div class="chat-container">
            <div class="username-label bot-label">iChat</div>
            <div class="bot-message-container">
                <div class="bot-message" style="background-color: #f0f2f5;">
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Make sure we're using the most up-to-date context
        if st.session_state.processed_files:
            ctx = "\n".join(f"{n}:\n{c}" for n,c in st.session_state.documents_content.items())
        else:
            ctx = "iBUS Networks is a telecommunications company."  # Default context
            
        # Get the answer using Gemini
        ans = ask_gemini(clicked_followup, ctx, st.session_state.images if st.session_state.images else None)
        
        # Make sure the answer doesn't have the question format
        if "Question:" in ans and "Answer:" in ans:
            ans = ans.split("Answer:", 1)[1].strip()
        
        # Get response timestamp
        response_time = datetime.now().strftime("%I:%M %p")
        
        # Remove the typing indicator and display the answer with timestamp using the new style
        typing_placeholder.markdown(f"""
        <div class="chat-container">
            <div class="username-label bot-label">iChat</div>
            <div class="bot-message-container">
                <div class="bot-message">
                    <div class="message-content">{ans}</div>
                    <div class="timestamp">{response_time}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add to chat history with timestamp
        message_id = f"assistant_{len(st.session_state.chat_history)}"
        st.session_state.message_timestamps[message_id] = response_time
        st.session_state.chat_history.append({"role":"assistant","content":ans, "id": message_id})
        
        # Generate new follow-up questions after answering
        st.session_state['current_followups'] = generate_followups(clicked_followup, ans, ctx)
        st.rerun()  # Refresh the chat history display

# Add implementation for Find functionality
if st.session_state.get('show_find_ui', False):
    with st.expander("🔍 Find in Documents", expanded=True):
        search_query = st.text_input("Enter search term:", key="search_query")
        search_button = st.button("Search", key="search_button")
        
        if search_button and search_query:
            # Debug information
            st.write(f"Searching for: '{search_query}'")
            st.write(f"Number of documents: {len(st.session_state.documents_content)}")
            
            search_results = []
            
            # Search through all document content
            for filename, content in st.session_state.documents_content.items():
                if search_query.lower() in content.lower():
                    # Find the context around the search term
                    index = content.lower().find(search_query.lower())
                    start = max(0, index - 100)
                    end = min(len(content), index + len(search_query) + 100)
                    
                    # Get the context snippet
                    context = content[start:end]
                    if start > 0:
                        context = "..." + context
                    if end < len(content):
                        context += "..."
                    
                    # Highlight the search term
                    highlighted = context.replace(
                        search_query, 
                        f"<span style='background-color: yellow; font-weight: bold;'>{search_query}</span>"
                    )
                    
                    search_results.append({
                        "filename": filename,
                        "context": highlighted
                    })
            
            # Display search results
            if search_results:
                st.markdown(f"Found **{len(search_results)}** results for '{search_query}':")
                
                for result in search_results:
                    with st.expander(f"📄 {result['filename']}"):
                        st.markdown(result["context"], unsafe_allow_html=True)
            else:
                st.info(f"No results found for '{search_query}'")
                
                # Check if documents are loaded
                if not st.session_state.documents_content:
                    st.warning("No documents have been uploaded yet. Please upload documents first.")

# Add implementation for Summary functionality
if st.session_state.get('show_summary_ui', False):
    with st.expander("📝 Generate Summary", expanded=True):
        if st.session_state.documents_content:
            summary_options = ["All Documents"] + list(st.session_state.documents_content.keys())
            selected_doc = st.selectbox("Select document to summarize:", summary_options)
            
            summary_type = st.radio(
                "Summary type:",
                ["Brief (1-2 paragraphs)", "Detailed (5-7 paragraphs)", "Key Points"]
            )
            
            if st.button("Generate Summary", key="generate_summary"):
                with st.spinner("Generating summary..."):
                    # Prepare content for summarization
                    if selected_doc == "All Documents":
                        content = "\n\n".join([f"Document: {name}\n{text}" for name, text in st.session_state.documents_content.items()])
                    else:
                        content = st.session_state.documents_content[selected_doc]
                    
                    # Determine prompt based on summary type
                    if summary_type == "Brief (1-2 paragraphs)":
                        prompt = f"Provide a brief 1-2 paragraph summary of this content:\n\n{content[:5000]}..."
                    elif summary_type == "Detailed (5-7 paragraphs)":
                        prompt = f"Provide a detailed 5-7 paragraph summary of this content:\n\n{content[:5000]}..."
                    else:  # Key Points
                        prompt = f"Extract 5-7 key points from this content:\n\n{content[:5000]}..."
                    
                    # Generate summary using ask_gemini function
                    summary = ask_gemini(prompt, "", None)
                    
                    # Display the summary
                    st.markdown("### Summary")
                    st.markdown(summary)
                    
                    # Option to add to chat
                    if st.button("Add to Chat", key="add_summary_to_chat"):
                        # Add user message
                        user_msg = f"Generate a {summary_type.lower()} for {selected_doc}"
                        st.session_state.chat_history.append({"role": "user", "content": user_msg})
                        
                        # Add assistant message with summary
                        st.session_state.chat_history.append({"role": "assistant", "content": summary})
                        
                        # Close the summary UI
                        st.session_state['show_summary_ui'] = False
                        st.rerun()
        else:
            st.warning("No documents available for summarization. Please upload documents first.")
        
        # Add close button
        if st.button("✖️ Close", key="close_summary"):
            st.session_state['show_summary_ui'] = False
            st.rerun()

# Remove sidebar file upload section and replace with inline upload
if st.session_state.user_name:
    # Create a container for the chat input and file upload
    input_container = st.container()
    
    # Add custom CSS for inline file upload
    st.markdown("""
    <style>
        /* Inline file upload styling */
        .inline-upload-container {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            gap: 10px;
        }
        
        .uploaded-files-list {
            margin-top: 10px;
            padding: 10px;
            background-color: #f7f7f7;
            border-radius: 8px;
            font-size: 14px;
        }
        
        .file-item {
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            border-bottom: 1px solid #eee;
        }
        
        /* Position the file upload near the chat input */
        .stChatInputContainer {
            position: relative;
            margin-top: 10px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Create columns for the chat input area
    col1, col2 = st.columns([6, 1])
    
    with col2:
        # Add plus icon dropdown menu with click instead of hover
        st.markdown("""
        <style>
            /* Plus icon dropdown styling */
            .plus-dropdown {
                position: relative;
                display: inline-block;
            }
            
            
            
            .plus-icon:hover {
                background-color: #e4e6e9;
            }
            
            .dropdown-content {
                display: none;  /* Hidden by default */
                position: absolute;
                bottom: 45px;
                right: 0;
                background-color: white;
                min-width: 160px;
                box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
                border-radius: 8px;
                z-index: 1000;
            }
        </style>
        
        <div class="plus-dropdown">
             <div class="plus-icon" id="plus-button"></div>
            <div class="dropdown-content" id="dropdown-menu" style="display: none;">
                <div class="dropdown-item" id="files-option">
                    <i>📎</i> Files
                </div>
                <div class="dropdown-item" id="find-option">
                    <i>🔍</i> Find
                </div>
                <div class="dropdown-item" id="chart-option">
                    <i>📊</i> Create Chart
                </div>
                <div class="dropdown-item" id="summary-option">
                    <i>📝</i> Summarize
                </div>
            </div>
        </div>

        <script>
            // Simple toggle function for the dropdown menu
            document.addEventListener('DOMContentLoaded', function() {
                const plusButton = document.getElementById('plus-button');
                const dropdownMenu = document.getElementById('dropdown-menu');
                
                // Toggle dropdown when plus button is clicked
                plusButton.addEventListener('click', function(e) {
                    e.stopPropagation();
                    if (dropdownMenu.style.display === 'none' || !dropdownMenu.style.display) {
                        dropdownMenu.style.display = 'block';
                    } else {
                        dropdownMenu.style.display = 'none';
                    }
                });
                
                // Close dropdown when clicking elsewhere
                document.addEventListener('click', function(e) {
                    if (e.target !== plusButton && !dropdownMenu.contains(e.target)) {
                        dropdownMenu.style.display = 'none';
                    }
                });
                
                // Setup dropdown item click handlers
                const filesOption = document.getElementById('files-option');
                if (filesOption) {
                    filesOption.addEventListener('click', function() {
                        const filesButton = document.querySelector('button[key="inline_upload_trigger"]');
                        if (filesButton) filesButton.click();
                        dropdownMenu.style.display = 'none';
                    });
                }
                
                const findOption = document.getElementById('find-option');
                if (findOption) {
                    findOption.addEventListener('click', function() {
                        const findButton = document.querySelector('button[key="find_trigger"]');
                        if (findButton) findButton.click();
                        dropdownMenu.style.display = 'none';
                    });
                }
                
                const chartOption = document.getElementById('chart-option');
                if (chartOption) {
                    chartOption.addEventListener('click', function() {
                        const chartButton = document.querySelector('button[key="chart_trigger"]');
                        if (chartButton) chartButton.click();
                        dropdownMenu.style.display = 'none';
                    });
                }
                
                const summaryOption = document.getElementById('summary-option');
                if (summaryOption) {
                    summaryOption.addEventListener('click', function() {
                        const summaryButton = document.querySelector('button[key="summary_trigger"]');
                        if (summaryButton) summaryButton.click();
                        dropdownMenu.style.display = 'none';
                    });
                }
            });
        </script>
        """, unsafe_allow_html=True)
        
        # Hidden buttons to trigger actions from JavaScript
        st.markdown("""
        <div id="hiddenButtonsContainer" style="display:none;">
            <div id="uploadTrigger"></div>
            <div id="findTrigger"></div>
            <div id="chartTrigger"></div>
            <div id="summaryTrigger"></div>
        </div>

        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Create a floating plus button
            var plusBtn = document.createElement('div');
            plusBtn.innerHTML = '+';
            plusBtn.style.position = 'fixed';
            plusBtn.style.bottom = '80px';
            plusBtn.style.right = '30px';
            plusBtn.style.width = '50px';
            plusBtn.style.height = '50px';
            plusBtn.style.backgroundColor = '#003A6C';
            plusBtn.style.color = 'white';
            plusBtn.style.borderRadius = '50%';
            plusBtn.style.display = 'flex';
            plusBtn.style.alignItems = 'center';
            plusBtn.style.justifyContent = 'center';
            plusBtn.style.fontSize = '24px';
            plusBtn.style.cursor = 'pointer';
            plusBtn.style.boxShadow = '0 2px 10px rgba(0,0,0,0.3)';
            plusBtn.style.zIndex = '9999';
            
            // Create dropdown menu
            var menu = document.createElement('div');
            menu.style.position = 'fixed';
            menu.style.bottom = '140px';
            menu.style.right = '30px';
            menu.style.backgroundColor = 'white';
            menu.style.borderRadius = '8px';
            menu.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
            menu.style.minWidth = '160px';
            menu.style.zIndex = '9998';
            menu.style.display = 'none';
            
            // Add menu items
            var items = [
                {id: 'uploadItem', icon: '📎', text: 'Upload Files', trigger: 'uploadTrigger'},
                {id: 'findItem', icon: '🔍', text: 'Find', trigger: 'findTrigger'},
                {id: 'chartItem', icon: '📊', text: 'Create Chart', trigger: 'chartTrigger'},
                {id: 'summaryItem', icon: '📝', text: 'Summarize', trigger: 'summaryTrigger'}
            ];
            
            items.forEach(function(item) {
                var menuItem = document.createElement('div');
                menuItem.id = item.id;
                menuItem.innerHTML = '<span style="margin-right:8px;">' + item.icon + '</span>' + item.text;
                menuItem.style.padding = '12px 16px';
                menuItem.style.cursor = 'pointer';
                menuItem.style.display = 'flex';
                menuItem.style.alignItems = 'center';
                
                menuItem.onmouseover = function() {
                    this.style.backgroundColor = '#f1f1f1';
                };
                
                menuItem.onmouseout = function() {
                    this.style.backgroundColor = 'white';
                };
                
                menuItem.onclick = function() {
                    // Trigger the corresponding button click
                    document.getElementById(item.trigger).click();
                    menu.style.display = 'none';
                };
                
                menu.appendChild(menuItem);
            });
            
            // Toggle menu when plus button is clicked
            plusBtn.onclick = function(e) {
                e.stopPropagation();
                menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
            };
            
            // Close menu when clicking elsewhere
            document.onclick = function(e) {
                if (e.target !== plusBtn) {
                    menu.style.display = 'none';
                }
            };
            
            // Add elements to the document
            document.body.appendChild(plusBtn);
            document.body.appendChild(menu);
            
            // Connect triggers to actual buttons
            document.getElementById('uploadTrigger').addEventListener('click', function() {
                document.querySelector('button[key="inline_upload_trigger"]').click();
            });
            
            document.getElementById('findTrigger').addEventListener('click', function() {
                document.querySelector('button[key="find_trigger"]').click();
            });
            
            document.getElementById('chartTrigger').addEventListener('click', function() {
                document.querySelector('button[key="chart_trigger"]').click();
            });
            
            document.getElementById('summaryTrigger').addEventListener('click', function() {
                document.querySelector('button[key="summary_trigger"]').click();
            });
        });
        </script>
        """, unsafe_allow_html=True)

        # Hide these buttons by default and make them visible only via JavaScript
        st.markdown("""
        <style>
        button[key="inline_upload_trigger"], 
        button[key="find_trigger"], 
        button[key="chart_trigger"], 
        button[key="summary_trigger"] {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)


        # Initialize toggle in session state
        if "show_plus_menu" not in st.session_state:
            st.session_state.show_plus_menu = False

        # Toggle button
        if st.button("➕", key="plus_icon"):
            st.session_state.show_plus_menu = not st.session_state.show_plus_menu

        # Show/hide hidden buttons when "+" is toggled
        if st.session_state.show_plus_menu:
            st.button("📤 Upload", key="inline_upload_trigger", help="Trigger for file upload", on_click=lambda: st.session_state.update(show_inline_upload=True))
            st.button("🔍 Find", key="find_trigger", help="Trigger for find functionality", on_click=lambda: st.session_state.update(show_find_ui=True))
            st.button("📊 Chart", key="chart_trigger", help="Trigger for chart functionality", on_click=lambda: st.session_state.update(show_chart_ui=True))
            st.button("📝 Summary", key="summary_trigger", help="Trigger for summary functionality", on_click=lambda: st.session_state.update(show_summary_ui=True))


        # Add a floating plus button that will show a menu with options to trigger these buttons
        st.markdown("""
        <script>
        // Wait for the page to fully load
        window.addEventListener('load', function() {
            // Create plus button
            const plusButton = document.createElement('button');
            plusButton.innerHTML = '+';
            plusButton.style.position = 'fixed';
            plusButton.style.bottom = '80px';
            plusButton.style.right = '30px';
            plusButton.style.width = '50px';
            plusButton.style.height = '50px';
            plusButton.style.backgroundColor = '#003A6C';
            plusButton.style.color = 'white';
            plusButton.style.border = 'none';
            plusButton.style.borderRadius = '50%';
            plusButton.style.fontSize = '24px';
            plusButton.style.cursor = 'pointer';
            plusButton.style.zIndex = '9999';
            
            // Create menu
            const menu = document.createElement('div');
            menu.style.position = 'fixed';
            menu.style.bottom = '140px';
            menu.style.right = '30px';
            menu.style.backgroundColor = 'white';
            menu.style.borderRadius = '8px';
            menu.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
            menu.style.padding = '10px 0';
            menu.style.display = 'none';
            menu.style.zIndex = '9999';
            
            // Create menu items
            const options = [
                {text: '📎 Upload Files', key: 'inline_upload_trigger'},
                {text: '🔍 Find', key: 'find_trigger'},
                {text: '📊 Create Chart', key: 'chart_trigger'},
                {text: '📝 Summarize', key: 'summary_trigger'}
            ];
            
            options.forEach(option => {
                const item = document.createElement('div');
                item.innerHTML = option.text;
                item.style.padding = '10px 20px';
                item.style.cursor = 'pointer';
                
                item.addEventListener('mouseover', function() {
                    this.style.backgroundColor = '#f0f0f0';
                });
                
                item.addEventListener('mouseout', function() {
                    this.style.backgroundColor = 'transparent';
                });
                
                item.addEventListener('click', function() {
                    // Find and click the corresponding button
                    const button = document.querySelector(`button[key="${option.key}"]`);
                    if (button) button.click();
                    menu.style.display = 'none';
                });
                
                menu.appendChild(item);
            });
            
            // Toggle menu when plus button is clicked
            plusButton.addEventListener('click', function(e) {
                e.stopPropagation();
                menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
            });
            
            // Close menu when clicking elsewhere
            document.addEventListener('click', function(e) {
                if (e.target !== plusButton) {
                    menu.style.display = 'none';
                }
            });
            
            // Add elements to the document
            document.body.appendChild(plusButton);
            document.body.appendChild(menu);
        });
        </script>
        """, unsafe_allow_html=True)


    # Display inline file upload area
    if st.session_state.get('show_inline_upload', False):
        with st.expander("Upload Files", expanded=True):
            uploads = st.file_uploader("Upload documents", type=EXTS + IMAGE_EXTS, accept_multiple_files=True, key="inline_uploader")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                process_button = st.button("📂 Process Files", key="inline_process_files", 
                                        help="Process uploaded files and extract content",
                                        type="primary")
            with col2:
                clear_button = st.button("🧹 Clear Files", key="inline_clear_files", 
                                        help="Clear all uploaded files",
                                        type="secondary")
            with col3:
                close_button = st.button("✖️ Close", key="close_upload", 
                                        help="Close file upload area",
                                        type="secondary")
                
            if close_button:
                st.session_state['show_inline_upload'] = False
                st.rerun()
                
            # Display currently uploaded files
            if st.session_state.processed_files:
                st.markdown("### Uploaded Files")
                for file in st.session_state.processed_files:
                    st.markdown(f"- {file}")

# Process files when the process button is clicked
if process_button and uploads:
    processed_files_count = 0
    file_summaries = []
    file_summaries_text = ""  # Initialize the variable
    
    # Process uploaded files
    for src in uploads or []:
        ext = os.path.splitext(src.name)[1][1:].lower()
        if ext in IMAGE_EXTS:
            try:
                img = Image.open(src)
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG')
                img_bytes = img_byte_arr.getvalue()
                st.session_state.images.append(img_bytes)
                st.session_state.processed_files.append(src.name)
                processed_files_count += 1
                file_summaries.append(f"- Processed image: {src.name}")
            except Exception as e:
                st.error(f"Error processing image {src.name}: {e}")
        elif ext in EXTS:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
            tmp.write(src.getvalue())
            tmp.close()
            txt = extract_text(tmp.name, ext)
            if txt:
                st.session_state.documents_content[src.name] = txt
                st.session_state.processed_files.append(src.name)
                processed_files_count += 1
                
                # Generate a brief summary for the text document
                try:
                    summary_prompt = f"Provide a very brief 3-line summary of this document content:\n\n{txt[:2000]}..."
                    summary = ask_gemini(summary_prompt, "", None).strip()
                    # Ensure it's not too long
                    if len(summary.split('\n')) > 3:
                        summary = '\n'.join(summary.split('\n')[:3])
                    st.session_state['file_summaries'][src.name] = summary
                    file_summaries.append(f"- {src.name}: {summary}")
                except Exception as e:
                    summary = f"Document processed. Contains {len(txt.split())} words."
                    st.session_state['file_summaries'][src.name] = summary
                    file_summaries.append(f"- {src.name}: {summary}")
            
            # Clean up the temporary file
            try:
                os.unlink(tmp.name)
            except:
                pass
    
    # Add a system message about processed files
    if processed_files_count > 0:
        # Get current timestamp
        current_time = datetime.now().strftime("%I:%M %p")
        
        # Create a system message about the processed files
        system_message = f"📁 Processed {processed_files_count} file(s):\n" + "\n".join(file_summaries)
        
        # Add to chat history with timestamp
        message_id = f"system_{len(st.session_state.chat_history)}"
        st.session_state.message_timestamps[message_id] = current_time
        st.session_state.chat_history.append({"role":"system","content":system_message, "id": message_id})
        
        # Generate follow-up questions based on the file content
        combined_ctx = "\n".join(f"{n}:\n{c}" for n,c in st.session_state.documents_content.items())
        st.session_state['current_followups'] = generate_followups("What information is in these files?", 
                                                                 "I've processed your files and extracted their content. You can now ask me questions about them.", 
                                                                 combined_ctx)
        
        # Hide the upload area after processing
        st.session_state['show_inline_upload'] = False
        st.rerun()

# Clear files when clear button is clicked
if clear_button:
    st.session_state.documents_content = {}
    st.session_state.processed_files = []
    st.session_state.images = []
    st.session_state.tables = {}
    st.session_state.file_summaries = {}
    
    # Add a system message about cleared files
    current_time = datetime.now().strftime("%I:%M %p")
    system_message = "🧹 All files have been cleared."
    
    # Add to chat history with timestamp
    message_id = f"system_{len(st.session_state.chat_history)}"
    st.session_state.message_timestamps[message_id] = current_time
    st.session_state.chat_history.append({"role":"system","content":system_message, "id": message_id})
    
    st.rerun()  # Refresh the chat history display

# Define a function to save chat history to disk
def save_chat_history(user_name):
    if not os.path.exists('chat_cache'):
        os.makedirs('chat_cache')
    
    # Create a dictionary with all the user's session data we want to save
    user_data = {
        'chat_history': st.session_state.chat_history,
        'message_timestamps': st.session_state.message_timestamps,
        'documents_content': st.session_state.documents_content,
        'processed_files': st.session_state.processed_files,
        'file_summaries': st.session_state.get('file_summaries', {}),
        'images': st.session_state.images,
        # Remove tables reference if it doesn't exist
    }
    
    # Save to disk using pickle
    try:
        with open(f'chat_cache/{user_name.lower().replace(" ", "_")}.pkl', 'wb') as f:
            pickle.dump(user_data, f)
    except Exception as e:
        st.error(f"Error saving chat history: {e}")

# Define a function to load chat history from disk
def load_chat_history(user_name):
    cache_file = f'chat_cache/{user_name.lower().replace(" ", "_")}.pkl'
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'rb') as f:
                user_data = pickle.load(f)
                
            # Restore all the saved session data
            st.session_state.chat_history = user_data.get('chat_history', [])
            st.session_state.message_timestamps = user_data.get('message_timestamps', {})
            st.session_state.documents_content = user_data.get('documents_content', {})
            st.session_state.processed_files = user_data.get('processed_files', [])
            
            # Check if file_summaries exists in session state before assigning
            if 'file_summaries' not in st.session_state:
                st.session_state['file_summaries'] = {}
            st.session_state['file_summaries'].update(user_data.get('file_summaries', {}))
            
            st.session_state.images = user_data.get('images', [])
            # Remove tables reference
            
            return True
        except Exception as e:
            st.error(f"Error loading chat history: {e}")
    return False

# Add this at the end of the chat input processing section
# This ensures chat history is saved after each interaction
if st.session_state.get('user_name'):
    save_chat_history(st.session_state.user_name)


