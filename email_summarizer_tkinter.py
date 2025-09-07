"""
Email Thread Summarization Tool - Tkinter Desktop Application
This application takes email messages as input and provides concise summaries.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from transformers import pipeline
import textwrap
import re

class EmailSummarizer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Email Thread Summarization Tool")
        self.root.geometry("900x700")
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Model variable
        self.summarizer = None
        self.model_loaded = False
        
        # Setup UI
        self.setup_ui()
        
        # Load model in background
        self.load_model_thread()
        
    def setup_ui(self):
        """Create the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Email Thread Summarization Tool", 
                                font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 10))
        
        # Input section
        input_label = ttk.Label(main_frame, text="Paste or type your email message below:", 
                                font=('Arial', 11))
        input_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 5))
        
        # Email input text area
        self.email_input = scrolledtext.ScrolledText(main_frame, height=12, width=80, 
                                                     wrap=tk.WORD, font=('Arial', 10))
        self.email_input.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, pady=10)
        
        # Summarize button
        self.summarize_btn = ttk.Button(button_frame, text="Summarize Email", 
                                        command=self.summarize_email, state='disabled')
        self.summarize_btn.pack(side=tk.LEFT, padx=5)
        
        # Clear button
        clear_btn = ttk.Button(button_frame, text="Clear All", command=self.clear_all)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Model status label
        self.status_label = ttk.Label(button_frame, text="Loading model...", 
                                      foreground='orange')
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Output section
        output_frame = ttk.LabelFrame(main_frame, text="Summary Results", padding="10")
        output_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        output_frame.columnconfigure(1, weight=1)
        output_frame.rowconfigure(1, weight=1)
        
        # Subject line
        subject_label = ttk.Label(output_frame, text="Subject:", font=('Arial', 10, 'bold'))
        subject_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.subject_text = ttk.Label(output_frame, text="", font=('Arial', 10), 
                                      wraplength=700, justify=tk.LEFT)
        self.subject_text.grid(row=0, column=1, sticky=tk.W, pady=(0, 5), padx=(10, 0))
        
        # Summary
        summary_label = ttk.Label(output_frame, text="Summary:", font=('Arial', 10, 'bold'))
        summary_label.grid(row=1, column=0, sticky=tk.NW, pady=(5, 0))
        
        self.summary_output = scrolledtext.ScrolledText(output_frame, height=8, width=70, 
                                                        wrap=tk.WORD, font=('Arial', 10),
                                                        state='disabled')
        self.summary_output.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), 
                                 pady=(5, 0), padx=(10, 0))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Add sample email button
        sample_btn = ttk.Button(button_frame, text="Load Sample Email", 
                                command=self.load_sample_email)
        sample_btn.pack(side=tk.LEFT, padx=5)
        
    def load_model_thread(self):
        """Load the summarization model in a separate thread"""
        thread = threading.Thread(target=self.load_model, daemon=True)
        thread.start()
        
    def load_model(self):
        """Load the summarization model"""
        try:
            # Use a smaller model for faster loading
            self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
            self.model_loaded = True
            
            # Update UI in main thread
            self.root.after(0, self.model_loaded_callback)
        except Exception as e:
            self.root.after(0, lambda: self.model_error_callback(str(e)))
            
    def model_loaded_callback(self):
        """Called when model is successfully loaded"""
        self.status_label.config(text="Model loaded ✓", foreground='green')
        self.summarize_btn.config(state='normal')
        
    def model_error_callback(self, error_msg):
        """Called when model loading fails"""
        self.status_label.config(text="Model failed to load", foreground='red')
        messagebox.showerror("Model Loading Error", 
                           f"Failed to load the summarization model:\n{error_msg}\n\n"
                           "Please check your internet connection and try again.")
        
    def extract_subject(self, email_text):
        """Extract subject from email (first line or first 60 chars)"""
        lines = email_text.strip().split('\n')
        first_line = lines[0] if lines else email_text[:60]
        
        # Clean up the subject
        subject = first_line.strip()
        if len(subject) > 60:
            subject = subject[:57] + "..."
            
        return subject
    
    def preprocess_email(self, email_text):
        """Preprocess email text for better summarization"""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', email_text)
        
        # Remove email headers if present
        text = re.sub(r'^(From|To|Date|Subject|Cc|Bcc):.*$', '', text, flags=re.MULTILINE)
        
        # Remove quoted text (lines starting with >)
        text = re.sub(r'^>.*$', '', text, flags=re.MULTILINE)
        
        # Remove email signatures (common patterns)
        text = re.sub(r'(Best regards|Sincerely|Thanks|Regards|Best),?\s*\n.*', '', text, 
                     flags=re.IGNORECASE | re.DOTALL)
        
        return text.strip()
    
    def summarize_email(self):
        """Summarize the email content"""
        email_text = self.email_input.get("1.0", tk.END).strip()
        
        if not email_text:
            messagebox.showwarning("No Input", "Please enter an email message to summarize.")
            return
            
        if not self.model_loaded:
            messagebox.showwarning("Model Loading", "Please wait for the model to load.")
            return
            
        # Start progress bar
        self.progress.start(10)
        self.summarize_btn.config(state='disabled')
        
        # Run summarization in separate thread
        thread = threading.Thread(target=self.perform_summarization, 
                                 args=(email_text,), daemon=True)
        thread.start()
        
    def perform_summarization(self, email_text):
        """Perform the actual summarization (runs in separate thread)"""
        try:
            # Extract subject
            subject = self.extract_subject(email_text)
            
            # Preprocess email
            processed_text = self.preprocess_email(email_text)
            
            # Truncate if too long (BART has max input length)
            max_length = 1024
            if len(processed_text) > max_length:
                processed_text = processed_text[:max_length]
            
            # Generate summary
            summary_result = self.summarizer(processed_text, 
                                            max_length=150, 
                                            min_length=30, 
                                            do_sample=False)
            summary = summary_result[0]['summary_text']
            
            # Update UI in main thread
            self.root.after(0, lambda: self.display_results(subject, summary))
            
        except Exception as e:
            self.root.after(0, lambda: self.summarization_error(str(e)))
            
    def display_results(self, subject, summary):
        """Display the summarization results"""
        self.progress.stop()
        self.summarize_btn.config(state='normal')
        
        # Update subject
        self.subject_text.config(text=subject)
        
        # Update summary
        self.summary_output.config(state='normal')
        self.summary_output.delete("1.0", tk.END)
        self.summary_output.insert("1.0", summary)
        self.summary_output.config(state='disabled')
        
    def summarization_error(self, error_msg):
        """Handle summarization errors"""
        self.progress.stop()
        self.summarize_btn.config(state='normal')
        messagebox.showerror("Summarization Error", 
                           f"Failed to summarize the email:\n{error_msg}")
        
    def clear_all(self):
        """Clear all input and output fields"""
        self.email_input.delete("1.0", tk.END)
        self.subject_text.config(text="")
        self.summary_output.config(state='normal')
        self.summary_output.delete("1.0", tk.END)
        self.summary_output.config(state='disabled')
        
    def load_sample_email(self):
        """Load a sample email for testing"""
        sample_email = """Subject: Project Update - Q4 Deliverables

Hi Team,

I wanted to provide a quick update on our Q4 project deliverables and timeline adjustments.

First, I'm pleased to report that the alpha version of our new customer portal has been 
successfully deployed to the staging environment. The development team has done an excellent 
job implementing the core features, including user authentication, dashboard analytics, and 
the reporting module. Initial testing shows that page load times have improved by 40% compared 
to our current system.

However, we've encountered some challenges with the payment integration module. The third-party 
API we're using has deprecated several endpoints, which means we need to refactor approximately 
30% of our payment processing code. This will likely push our beta release back by two weeks.

On a positive note, the mobile app development is ahead of schedule. Both iOS and Android versions 
are now feature-complete, and we're currently in the QA phase. User acceptance testing will begin 
next Monday with a group of 50 beta testers from our customer advisory board.

Regarding budget, we're currently tracking at 92% of allocated resources. The additional two weeks 
for payment integration refactoring will require an additional $15,000 in development costs, which 
I've already discussed with finance.

Action items for next week:
- Complete payment API refactoring
- Begin mobile app UAT
- Finalize documentation for customer portal
- Schedule stakeholder demo for November 15th

Please let me know if you have any questions or concerns about these updates.

Best regards,
Sarah Johnson
Project Manager"""
        
        self.email_input.delete("1.0", tk.END)
        self.email_input.insert("1.0", sample_email)
        
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = EmailSummarizer()
    app.run()