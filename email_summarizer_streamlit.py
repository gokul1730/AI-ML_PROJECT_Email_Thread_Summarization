"""
Email Thread Summarization Tool - Streamlit Web Application
Run with: streamlit run email_summarizer_streamlit.py
"""

import streamlit as st
from transformers import pipeline
import re
import time

# Page configuration
st.set_page_config(
    page_title="Email Summarizer",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #64748B;
        text-align: center;
        margin-bottom: 2rem;
    }
    .result-box {
        background-color: #F0F9FF;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #BFDBFE;
        margin: 1rem 0;
    }
    .subject-text {
        font-size: 1.1rem;
        font-weight: bold;
        color: #1E40AF;
    }
    .summary-text {
        font-size: 1rem;
        line-height: 1.6;
        color: #334155;
    }
    .stButton>button {
        background-color: #3B82F6;
        color: white;
        font-weight: bold;
        padding: 0.5rem 2rem;
        border-radius: 5px;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #2563EB;
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def load_summarization_model():
    """Load and cache the summarization model"""
    with st.spinner("Loading AI model... This may take a minute on first run."):
        try:
            summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
            return summarizer, True
        except Exception as e:
            st.error(f"Failed to load model: {str(e)}")
            return None, False

def extract_subject(email_text):
    """Extract subject from email (first line or first 60 chars)"""
    lines = email_text.strip().split('\n')
    first_line = lines[0] if lines else email_text[:60]
    
    # Clean up the subject
    subject = first_line.strip()
    
    # Remove "Subject:" prefix if present
    subject = re.sub(r'^Subject:\s*', '', subject, flags=re.IGNORECASE)
    
    if len(subject) > 60:
        subject = subject[:57] + "..."
        
    return subject

def preprocess_email(email_text):
    """Preprocess email text for better summarization"""
    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n', '\n\n', email_text)
    
    # Remove email headers if present
    text = re.sub(r'^(From|To|Date|Subject|Cc|Bcc):.*$', '', text, flags=re.MULTILINE)
    
    # Remove quoted text (lines starting with >)
    text = re.sub(r'^>.*$', '', text, flags=re.MULTILINE)
    
    # Remove email signatures (common patterns)
    text = re.sub(r'(Best regards|Sincerely|Thanks|Regards|Best|Cheers),?\s*\n.*', '', 
                 text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove multiple consecutive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def summarize_email(email_text, summarizer):
    """Generate summary for the email"""
    # Extract subject
    subject = extract_subject(email_text)
    
    # Preprocess email
    processed_text = preprocess_email(email_text)
    
    # Truncate if too long (BART has max input length)
    max_length = 1024
    if len(processed_text) > max_length:
        processed_text = processed_text[:max_length]
        st.warning("⚠️ Email was truncated due to length limitations.")
    
    # Generate summary
    with st.spinner("Generating summary..."):
        try:
            summary_result = summarizer(
                processed_text,
                max_length=150,
                min_length=30,
                do_sample=False
            )
            summary = summary_result[0]['summary_text']
            return subject, summary, True
        except Exception as e:
            return subject, f"Error generating summary: {str(e)}", False

def load_sample_email():
    """Return a sample email for demonstration"""
    return """Subject: Project Update - Q4 Deliverables

Hi Team,

I wanted to provide a quick update on our Q4 project deliverables and timeline adjustments.

First, I'm pleased to report that the alpha version of our new customer portal has been successfully deployed to the staging environment. The development team has done an excellent job implementing the core features, including user authentication, dashboard analytics, and the reporting module. Initial testing shows that page load times have improved by 40% compared to our current system.

However, we've encountered some challenges with the payment integration module. The third-party API we're using has deprecated several endpoints, which means we need to refactor approximately 30% of our payment processing code. This will likely push our beta release back by two weeks.

On a positive note, the mobile app development is ahead of schedule. Both iOS and Android versions are now feature-complete, and we're currently in the QA phase. User acceptance testing will begin next Monday with a group of 50 beta testers from our customer advisory board.

Regarding budget, we're currently tracking at 92% of allocated resources. The additional two weeks for payment integration refactoring will require an additional $15,000 in development costs, which I've already discussed with finance.

Action items for next week:
- Complete payment API refactoring
- Begin mobile app UAT
- Finalize documentation for customer portal
- Schedule stakeholder demo for November 15th

Please let me know if you have any questions or concerns about these updates.

Best regards,
Sarah Johnson
Project Manager"""

def main():
    # Header
    st.markdown('<h1 class="main-header">📧 Email Thread Summarization Tool</h1>', 
                unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Transform lengthy emails into concise, actionable summaries</p>', 
                unsafe_allow_html=True)
    
    # Load model
    summarizer, model_loaded = load_summarization_model()
    
    if model_loaded:
        st.success("✅ AI Model loaded successfully!")
    else:
        st.error("❌ Failed to load AI model. Please refresh the page to try again.")
        return
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown("### 📝 Input Email")
        
        # Sample email button
        if st.button("📋 Load Sample Email", type="secondary"):
            st.session_state.email_input = load_sample_email()
        
        # Email input area
        email_text = st.text_area(
            "Paste or type your email message below:",
            height=400,
            placeholder="Enter your email content here...",
            key="email_input",
            help="You can paste complete email threads, forwarded messages, or any email content"
        )
        
        # Buttons
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        with col_btn1:
            summarize_clicked = st.button("🚀 Summarize", type="primary", 
                                         disabled=not email_text)
        with col_btn2:
            if st.button("🗑️ Clear"):
                st.session_state.email_input = ""
                st.rerun()
    
    with col2:
        st.markdown("### 📊 Summary Results")
        
        if summarize_clicked and email_text:
            subject, summary, success = summarize_email(email_text, summarizer)
            
            if success:
                # Display results in styled containers
                st.markdown('<div class="result-box">', unsafe_allow_html=True)
                st.markdown('<p class="subject-text">📌 Subject:</p>', unsafe_allow_html=True)
                st.write(subject)
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="result-box">', unsafe_allow_html=True)
                st.markdown('<p class="subject-text">📝 Summary:</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="summary-text">{summary}</p>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Word count statistics
                original_words = len(email_text.split())
                summary_words = len(summary.split())
                reduction = ((original_words - summary_words) / original_words) * 100
                
                st.markdown("### 📈 Statistics")
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                with col_stat1:
                    st.metric("Original Words", original_words)
                with col_stat2:
                    st.metric("Summary Words", summary_words)
                with col_stat3:
                    st.metric("Reduction", f"{reduction:.1f}%")
                
                # Success message
                st.balloons()
                st.success("✨ Email summarized successfully!")
            else:
                st.error(summary)  # Display error message
        elif not email_text:
            st.info("👈 Enter an email message and click 'Summarize' to generate a summary")
    
    # Footer with instructions
    st.markdown("---")
    with st.expander("ℹ️ How to use this tool"):
        st.markdown("""
        1. **Paste your email**: Copy and paste the complete email message into the input area
        2. **Click Summarize**: The AI will process your email and generate a concise summary
        3. **Review results**: Check the extracted subject line and the generated summary
        
        **Features:**
        - Automatically extracts the subject line from the email
        - Removes email headers, signatures, and quoted text
        - Generates concise summaries while preserving key information
        - Shows reduction statistics
        
        **Tips:**
        - Works best with emails between 100-1000 words
        - The tool will automatically truncate very long emails
        - Try the sample email to see how it works
        """)
    
    # Sidebar with additional information
    with st.sidebar:
        st.markdown("### 🤖 About the Model")
        st.info("""
        This tool uses Facebook's BART model 
        (bart-large-cnn) for text summarization.
        
        BART is specifically fine-tuned on 
        news articles and performs well on 
        various text summarization tasks.
        """)
        
        st.markdown("### 🎯 Best Use Cases")
        st.markdown("""
        - Project updates
        - Meeting summaries
        - Customer feedback
        - Technical discussions
        - Newsletter digests
        - Long email threads
        """)
        
        st.markdown("### ⚡ Performance")
        st.markdown("""
        - Processing time: 2-5 seconds
        - Max input: ~1000 words
        - Summary length: 30-150 words
        """)

if __name__ == "__main__":
    main()