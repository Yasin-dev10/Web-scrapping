import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os

class DataValidatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Text & Category Validator")
        self.root.geometry("800x640")
        
        self.df = None
        self.current_index = 0
        self.file_path = ""
        self.output_path = ""
        
        # UI Elements
        tk.Label(root, text="Hubiyaha Xogta (Data Validator)", font=("Helvetica", 16, "bold")).pack(pady=10)
        
        # File frame
        file_frame = tk.Frame(root)
        file_frame.pack(pady=5, fill="x", padx=20)
        
        tk.Button(file_frame, text="Xulo File CSV ah", font=("Helvetica", 10, "bold"), command=self.load_file).pack(side="left")
        self.file_label = tk.Label(file_frame, text="File lama dooran", fg="gray")
        self.file_label.pack(side="left", padx=10)
        
        # Info frame
        self.info_label = tk.Label(root, text="Tirada: 0/0", font=("Helvetica", 12))
        self.info_label.pack(pady=5)
        
        # Text display
        tk.Label(root, text="Qoraalka (Text):", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=20)
        self.text_display = scrolledtext.ScrolledText(root, height=12, width=80, wrap=tk.WORD, font=("Helvetica", 12))
        self.text_display.pack(padx=20, pady=5)
        
        # Category display
        self.cat_var = tk.StringVar()
        self.cat_var.set("Category Hadda: N/A")
        tk.Label(root, textvariable=self.cat_var, font=("Helvetica", 14, "bold"), fg="purple").pack(pady=10)
        
        # Actions frame
        action_frame = tk.Frame(root)
        action_frame.pack(pady=10)
        
        tk.Button(action_frame, text="Sax (Ku dhaaf sidaas)", bg="blue", fg="white", font=("Helvetica", 11, "bold"), width=20, command=self.keep_current).pack(side="left", padx=5)
        tk.Button(action_frame, text="Ka dhig: Crime", bg="red", fg="white", font=("Helvetica", 11, "bold"), width=15, command=lambda: self.update_category('crime-related')).pack(side="left", padx=5)
        tk.Button(action_frame, text="Ka dhig: Not Crime", bg="green", fg="white", font=("Helvetica", 11, "bold"), width=18, command=lambda: self.update_category('not crime-related')).pack(side="left", padx=5)
        
        nav_frame = tk.Frame(root)
        nav_frame.pack(pady=5)
        tk.Button(nav_frame, text="< Gadaal u noqo", font=("Helvetica", 11), command=self.go_back).pack(side="left", padx=10)
        tk.Button(nav_frame, text="Skip (Ka Gudub) >", font=("Helvetica", 11), command=self.skip).pack(side="left", padx=10)
        
        # Save button
        tk.Button(root, text="Save (Keydi Xogta)", bg="black", fg="white", font=("Helvetica", 12, "bold"), width=20, command=self.save_data).pack(pady=20)

    def load_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if filepath:
            try:
                self.df = pd.read_csv(filepath)
                
                # Check for columns and rename to standard lowercase names
                cols = [c.lower() for c in self.df.columns]
                
                text_col = None
                for c in ['text', 'qoraal', 'content', 'post']:
                    if c in cols:
                        text_col = self.df.columns[cols.index(c)]
                        break
                        
                cat_col = None
                for c in ['category', 'nooc', 'class']:
                    if c in cols:
                        cat_col = self.df.columns[cols.index(c)]
                        break
                
                if not text_col or not cat_col:
                    messagebox.showerror("Cilad", "File-ka waa inuu lahaadaa columns-ka 'text' iyo 'category' (ama magacyo la mid ah)")
                    return
                
                # Standardize column names if they are different cases
                rename_dict = {}
                if text_col != 'text': rename_dict[text_col] = 'text'
                if cat_col != 'category': rename_dict[cat_col] = 'category'
                if rename_dict:
                    self.df.rename(columns=rename_dict, inplace=True)
                
                self.file_path = filepath
                self.output_path = filepath.replace(".csv", "_validated.csv")
                self.file_label.config(text=os.path.basename(filepath), fg="black")
                
                self.current_index = 0
                self.show_current()
                
            except Exception as e:
                messagebox.showerror("Cilad Akhris", f"Waa la akhriyi waayay file-ka: {e}")

    def show_current(self):
        if self.df is not None and 0 <= self.current_index < len(self.df):
            row = self.df.iloc[self.current_index]
            
            # Update info
            self.info_label.config(text=f"Tirada: {self.current_index + 1} / {len(self.df)}")
            
            # Update text display
            self.text_display.delete('1.0', tk.END)
            self.text_display.insert(tk.END, str(row['text']))
            
            # Update category
            current_cat = str(row['category'])
            self.cat_var.set(f"Category Hadda: {current_cat}")
            
        elif self.df is not None and self.current_index >= len(self.df):
            messagebox.showinfo("Dhamaad", "Waxaad dhex martay dhammaan xogta! Fadlan 'Save' garee.")
            self.text_display.delete('1.0', tk.END)
            self.cat_var.set("Category Hadda: N/A")
            self.info_label.config(text=f"Tirada: Dhamaad / {len(self.df)}")
            self.current_index = len(self.df)

    def keep_current(self):
        if self.df is not None and self.current_index < len(self.df):
            self.current_index += 1
            self.show_current()

    def update_category(self, new_category):
        if self.df is not None and self.current_index < len(self.df):
            self.df.at[self.current_index, 'category'] = new_category
            self.current_index += 1
            self.show_current()

    def go_back(self):
        if self.df is not None and self.current_index > 0:
            self.current_index -= 1
            self.show_current()

    def skip(self):
        if self.df is not None and self.current_index < len(self.df):
            self.current_index += 1
            self.show_current()

    def save_data(self):
        if self.df is not None:
            try:
                self.df.to_csv(self.output_path, index=False)
                messagebox.showinfo("Guul", f"Xogta si sax ah ayaa loo keydiyay!\nMagaca File-ka: {os.path.basename(self.output_path)}")
            except Exception as e:
                messagebox.showerror("Cilad Keydis", f"Waa la keydin waayay file-ka: {e}")
        else:
            messagebox.showwarning("Digniin", "Ma jirto xog la keydiyo!")

if __name__ == "__main__":
    root = tk.Tk()
    app = DataValidatorGUI(root)
    root.mainloop()
