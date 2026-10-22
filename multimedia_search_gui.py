import tkinter as tk
from tkinter import ttk, messagebox
import oracledb # Using the modern connector
from datetime import datetime

# =========================================================================
# 1. ORACLE CONNECTION DETAILS 
# =========================================================================
ORACLE_USER = "apps"   
ORACLE_PASSWORD = "123"
ORACLE_DSN = "localhost:1521/orcl"
# =========================================================================

class MultimediaSearchApp:
    def __init__(self, master):
        self.master = master
        master.title("Multimedia Database Search Engine")

        # Set up styles for a cleaner look
        style = ttk.Style()
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10, 'bold'))

        main_frame = ttk.Frame(master, padding="15", style='TFrame')
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        master.grid_rowconfigure(0, weight=1)
        master.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        # --- Input Widgets Setup ---
        ttk.Label(main_frame, text="Search Criteria:", font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        row_counter = 1

        # File Type
        ttk.Label(main_frame, text="File Type:").grid(row=row_counter, column=0, sticky=tk.W, padx=5, pady=5)
        self.filetype_var = tk.StringVar(value="") # Default to empty for all types
        filetype_options = ["", "image", "video", "audio", "document"]
        self.filetype_entry = ttk.Combobox(main_frame, textvariable=self.filetype_var, values=filetype_options, state="readonly")
        self.filetype_entry.grid(row=row_counter, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        row_counter += 1

        # Location
        ttk.Label(main_frame, text="Location:").grid(row=row_counter, column=0, sticky=tk.W, padx=5, pady=5)
        self.location_var = tk.StringVar()
        self.location_entry = ttk.Entry(main_frame, textvariable=self.location_var)
        self.location_entry.grid(row=row_counter, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        row_counter += 1

        # Date Range (From and To)
        ttk.Label(main_frame, text="Date From (YYYY-MM-DD):").grid(row=row_counter, column=0, sticky=tk.W, padx=5, pady=5)
        self.date_from_var = tk.StringVar()
        self.date_from_entry = ttk.Entry(main_frame, textvariable=self.date_from_var)
        self.date_from_entry.grid(row=row_counter, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        row_counter += 1

        ttk.Label(main_frame, text="Date To (YYYY-MM-DD):").grid(row=row_counter, column=0, sticky=tk.W, padx=5, pady=5)
        self.date_to_var = tk.StringVar()
        self.date_to_entry = ttk.Entry(main_frame, textvariable=self.date_to_var)
        self.date_to_entry.grid(row=row_counter, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        row_counter += 1

        # Keyword (Annotation/Filename)
        ttk.Label(main_frame, text="Keyword:").grid(row=row_counter, column=0, sticky=tk.W, padx=5, pady=5)
        self.keyword_var = tk.StringVar()
        self.keyword_entry = ttk.Entry(main_frame, textvariable=self.keyword_var)
        self.keyword_entry.grid(row=row_counter, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        row_counter += 1

        # Search Button
        ttk.Button(main_frame, text="🔍 SEARCH DATABASE", command=self.run_search).grid(
            row=row_counter, column=0, columnspan=2, pady=15)
        row_counter += 1

        # --- Results Treeview Setup ---
        
        ttk.Label(main_frame, text="Results:", font=('Arial', 12, 'bold')).grid(row=row_counter, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        row_counter += 1

        columns = ("id", "filename", "filetype", "date_created", "location", "annotation", "file_path")
        self.tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=10)
        
        # Define Headings and Column Widths
        headings = {
            "id": ("ID", 30), "filename": ("Filename", 150), "filetype": ("Type", 70), 
            "date_created": ("Date Created", 100), "location": ("Location", 100), 
            "annotation": ("Annotation", 250), "file_path": ("File Path", 200)
        }
        
        for col, (text, width) in headings.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=tk.W, stretch=tk.YES if col in ["annotation", "file_path"] else tk.NO)

        self.tree.grid(row=row_counter, column=0, columnspan=2, sticky=(tk.N, tk.S, tk.E, tk.W))
        main_frame.grid_rowconfigure(row_counter, weight=1)
        
        # Add Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=row_counter, column=2, sticky='ns')
        self.tree.configure(yscrollcommand=scrollbar.set)
        
    # --- Date Parsing and Validation ---
    def parse_date(self, date_str):
        """Converts YYYY-MM-DD string to a datetime.date object or None."""
        if not date_str.strip():
            return None
        try:
            # We convert to a date object for proper passing to Oracle
            return datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
        except ValueError:
            messagebox.showerror("Input Error", f"Invalid date format: '{date_str.strip()}'. Please use YYYY-MM-DD.")
            return False # Signal parsing failure

    # --- Search Execution Logic ---
    def run_search(self):
        # 1. Clear previous results
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # 2. Collect and validate input
        filetype = self.filetype_var.get() or None
        location = self.location_var.get() or None
        keyword = self.keyword_var.get() or None
        
        date_from = self.parse_date(self.date_from_var.get())
        date_to = self.parse_date(self.date_to_var.get())

        if date_from is False or date_to is False:
            return # Stop if date parsing failed
        
        # 3. Establish Oracle Connection and execute PL/SQL Function
        conn = None
        try:
            # Connect using the DSN credentials
            conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=ORACLE_DSN)
            cursor = conn.cursor()
            
            # The SQL calls the PL/SQL function using the TABLE() operator
            sql = "SELECT * FROM TABLE(Search_Multimedia(:ft, :loc, :df, :dt, :kw))"
            
            # Execute the query. The function handles NULLs, so we pass everything.
            cursor.execute(sql, 
                           ft=filetype, 
                           loc=location, 
                           df=date_from, 
                           dt=date_to, 
                           kw=keyword)
            
            results = cursor.fetchall()
            
            if not results:
                messagebox.showinfo("Search Complete", "No multimedia data found matching the criteria.")
                return

            # 4. Populate Treeview
            for row in results:
                formatted_row = list(row)
                
                # Format the Date object (index 3) to a readable string
                if formatted_row[3] and isinstance(formatted_row[3], datetime):
                    formatted_row[3] = formatted_row[3].strftime('%Y-%m-%d')
                    
                self.tree.insert("", tk.END, values=formatted_row)
            
            messagebox.showinfo("Search Complete", f"Found {len(results)} records.")

        except oracledb.Error as e:
            error, = e.args
            messagebox.showerror("Database Error", f"Oracle Error Code: {error.code}\nMessage: {error.message}")
            
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            
        finally:
            if conn:
                conn.close()

if __name__ == '__main__':
    root = tk.Tk()
    app = MultimediaSearchApp(root)
    root.mainloop()
    
    
# run python multimedia_search_gui.py