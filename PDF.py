import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import PyPDF2
import threading
import requests
import json
from datetime import datetime
import os

class PDFQAApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Q&A Assistant")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.pdf_text = ""
        self.pdf_filename = ""
        self.ollama_models = []
        self.selected_model = tk.StringVar(value="llama2")
        
        self.setup_ui()
        self.check_ollama_connection()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="PDF Q&A Assistant", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # PDF Upload Section
        upload_frame = ttk.LabelFrame(main_frame, text="PDF Upload", padding="10")
        upload_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        upload_frame.columnconfigure(1, weight=1)
        
        ttk.Button(upload_frame, text="Select PDF", 
                  command=self.select_pdf).grid(row=0, column=0, padx=(0, 10))
        
        self.pdf_label = ttk.Label(upload_frame, text="No PDF selected", 
                                  foreground='gray')
        self.pdf_label.grid(row=0, column=1, sticky=tk.W)
        
        # Model Selection
        model_frame = ttk.LabelFrame(main_frame, text="LLM Model", padding="10")
        model_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(model_frame, text="Model:").grid(row=0, column=0, padx=(0, 10))
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.selected_model, 
                                       state="readonly", width=20)
        self.model_combo.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Button(model_frame, text="Refresh Models", 
                  command=self.refresh_models).grid(row=0, column=2)
        
        self.connection_label = ttk.Label(model_frame, text="Checking Ollama...", 
                                         foreground='orange')
        self.connection_label.grid(row=0, column=3, padx=(10, 0))
        
        # Chat Section
        chat_frame = ttk.LabelFrame(main_frame, text="Q&A Chat", padding="10")
        chat_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, 
                                                     height=15, state=tk.DISABLED,
                                                     font=('Arial', 10))
        self.chat_display.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), 
                              pady=(0, 10))
        
        # Question input
        input_frame = ttk.Frame(chat_frame)
        input_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
        input_frame.columnconfigure(0, weight=1)
        
        self.question_entry = ttk.Entry(input_frame, font=('Arial', 10))
        self.question_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        self.question_entry.bind('<Return>', lambda e: self.ask_question())
        
        self.ask_button = ttk.Button(input_frame, text="Ask Question", 
                                    command=self.ask_question)
        self.ask_button.grid(row=0, column=1)
        
        # Debug button to check PDF content
        self.debug_button = ttk.Button(input_frame, text="Debug PDF", 
                                      command=self.debug_pdf)
        self.debug_button.grid(row=0, column=2, padx=(10, 0))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status bar
        self.status_label = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN, 
                                     anchor=tk.W)
        self.status_label.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
    def select_pdf(self):
        file_path = filedialog.askopenfilename(
            title="Select PDF file",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if file_path:
            self.pdf_filename = os.path.basename(file_path)
            self.pdf_label.config(text=f"Loading: {self.pdf_filename}", foreground='orange')
            self.status_label.config(text="Extracting text from PDF...")
            self.progress.start()
            
            # Extract text in a separate thread
            thread = threading.Thread(target=self.extract_pdf_text, args=(file_path,))
            thread.daemon = True
            thread.start()
    
    def extract_pdf_text(self, file_path):
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                print(f"DEBUG: PDF has {len(pdf_reader.pages)} pages")  # Debug info
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    print(f"DEBUG: Page {page_num + 1} extracted {len(page_text)} characters")  # Debug info
                    
                    if page_text.strip():  # Only add if there's actual text
                        text += f"\n--- Page {page_num + 1} ---\n"
                        text += page_text
                    else:
                        text += f"\n--- Page {page_num + 1} (No text extracted) ---\n"
            
            print(f"DEBUG: Total extracted text length: {len(text)}")  # Debug info
            print(f"DEBUG: First 200 chars: {text[:200]}")  # Debug info
            
            self.pdf_text = text
            
            # Update UI in main thread
            self.root.after(0, self.pdf_loaded_callback)
            
        except Exception as e:
            print(f"DEBUG: PDF extraction error: {str(e)}")  # Debug info
            self.root.after(0, lambda: self.show_error(f"Error reading PDF: {str(e)}"))
    
    def pdf_loaded_callback(self):
        self.progress.stop()
        self.pdf_label.config(text=f"Loaded: {self.pdf_filename} ({len(self.pdf_text)} chars)", 
                             foreground='green')
        self.status_label.config(text="PDF loaded successfully. Ready for questions.")
        self.add_to_chat("System", f"PDF '{self.pdf_filename}' loaded successfully! You can now ask questions about its content.")
    
    def check_ollama_connection(self):
        def check():
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if response.status_code == 200:
                    models_data = response.json()
                    self.ollama_models = [model['name'] for model in models_data.get('models', [])]
                    self.root.after(0, self.update_connection_status, True)
                else:
                    self.root.after(0, self.update_connection_status, False)
            except:
                self.root.after(0, self.update_connection_status, False)
        
        thread = threading.Thread(target=check)
        thread.daemon = True
        thread.start()
    
    def update_connection_status(self, connected):
        if connected:
            self.connection_label.config(text="✓ Ollama Connected", foreground='green')
            self.model_combo['values'] = self.ollama_models
            if self.ollama_models:
                self.selected_model.set(self.ollama_models[0])
        else:
            self.connection_label.config(text="✗ Ollama Not Found", foreground='red')
            self.model_combo['values'] = []
            messagebox.showwarning("Ollama Not Found", 
                                 "Ollama is not running. Please install and start Ollama to use this app.\n\n"
                                 "Visit: https://ollama.ai")
    
    def refresh_models(self):
        self.check_ollama_connection()
    
    def ask_question(self):
        question = self.question_entry.get().strip()
        if not question:
            return
        
        if not self.pdf_text:
            messagebox.showwarning("No PDF", "Please upload a PDF file first.")
            return
        
        if not self.selected_model.get():
            messagebox.showwarning("No Model", "Please select an LLM model.")
            return
        
        self.question_entry.delete(0, tk.END)
        self.add_to_chat("You", question)
        self.ask_button.config(state=tk.DISABLED)
        self.status_label.config(text="Generating response...")
        self.progress.start()
        
        # Generate response in separate thread
        thread = threading.Thread(target=self.generate_response, args=(question,))
        thread.daemon = True
        thread.start()
    
    def generate_response(self, question):
        try:
            # Prepare the prompt with PDF context (use more content and better formatting)
            pdf_content = self.pdf_text[:8000] if len(self.pdf_text) > 8000 else self.pdf_text
            
            prompt = f"""You are an AI assistant that answers questions based on provided document content. Please read the document carefully and answer the question based only on the information in the document.

DOCUMENT CONTENT:
{pdf_content}

QUESTION: {question}

Please provide a detailed answer based on the document content above. If the information is not in the document, say so clearly."""

            # Call Ollama API
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.selected_model.get(),
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "num_predict": 500
                    }
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('response', 'No response received')
                self.root.after(0, self.display_response, answer)
            else:
                self.root.after(0, self.show_error, f"API Error: {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.root.after(0, self.show_error, "Request timed out. Try again.")
        except Exception as e:
            self.root.after(0, self.show_error, f"Error: {str(e)}")
    
    def display_response(self, response):
        self.progress.stop()
        self.ask_button.config(state=tk.NORMAL)
        self.status_label.config(text="Ready")
        self.add_to_chat("Assistant", response)
    
    def add_to_chat(self, sender, message):
        self.chat_display.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M")
        
        if sender == "System":
            self.chat_display.insert(tk.END, f"[{timestamp}] {message}\n\n", "system")
        else:
            self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: {message}\n\n")
        
        # Configure tags for styling
        self.chat_display.tag_configure("system", foreground="blue", font=('Arial', 9, 'italic'))
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def show_error(self, error_message):
        self.progress.stop()
        self.ask_button.config(state=tk.NORMAL)
        self.status_label.config(text="Error occurred")
        messagebox.showerror("Error", error_message)
    
    def debug_pdf(self):
        """Debug function to check PDF content"""
        if not self.pdf_text:
            messagebox.showinfo("Debug", "No PDF text loaded!")
            return
            
        debug_info = f"""PDF Debug Information:
        
Filename: {self.pdf_filename}
Total characters: {len(self.pdf_text)}
        
First 500 characters:
{self.pdf_text[:500]}

Last 500 characters:
{self.pdf_text[-500:]}"""
        
        # Create a new window to show debug info
        debug_window = tk.Toplevel(self.root)
        debug_window.title("PDF Debug Info")
        debug_window.geometry("600x400")
        
        debug_text = scrolledtext.ScrolledText(debug_window, wrap=tk.WORD)
        debug_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        debug_text.insert(tk.END, debug_info)
        debug_text.config(state=tk.DISABLED)

def main():
    # Check dependencies
    try:
        import PyPDF2
        import requests
    except ImportError as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Missing Dependencies", 
                           f"Required package not found: {e.name}\n\n"
                           "Please install with:\n"
                           "pip install PyPDF2 requests")
        return
    
    root = tk.Tk()
    app = PDFQAApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()