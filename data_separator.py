import pandas as pd
import os
import tkinter as tk
from tkinter import filedialog, messagebox

class DataSeparatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV Data Separator & Balancer")
        self.root.geometry("500x380")
        self.root.resizable(False, False)

        # Header Label
        tk.Label(root, text="App-ka Kala Saarista Xogta", font=("Helvetica", 14, "bold")).pack(pady=(15, 5))

        # File Selection
        tk.Label(root, text="Xulo file-ka CSV (Input File):", font=("Helvetica", 10, "bold")).pack(pady=(10, 0))
        
        file_frame = tk.Frame(root)
        file_frame.pack(pady=5, padx=20, fill="x")
        
        self.file_path_var = tk.StringVar()
        self.file_entry = tk.Entry(file_frame, textvariable=self.file_path_var, state='readonly', width=45)
        self.file_entry.pack(side="left", padx=(0, 10))
        
        self.browse_btn = tk.Button(file_frame, text="Browse...", command=self.browse_file)
        self.browse_btn.pack(side="left")

        # Target Count
        tk.Label(root, text="Tirada aad rabto Category Kasta (Tus: 5000):", font=("Helvetica", 10, "bold")).pack(pady=(20, 0))
        
        self.target_var = tk.StringVar(value="5000")
        self.target_entry = tk.Entry(root, textvariable=self.target_var, width=15, font=("Helvetica", 12), justify="center")
        self.target_entry.pack(pady=5)

        # Run Button
        self.run_btn = tk.Button(root, text="Kala Saar & Isku Keen", bg="green", fg="white", font=("Helvetica", 11, "bold"), command=self.process_data, width=20)
        self.run_btn.pack(pady=25)

        # Status output
        self.status_var = tk.StringVar()
        self.status_var.set("Waa diyaar, fadlan xulo file-ka.")
        self.status_label = tk.Label(root, textvariable=self.status_var, fg="blue", justify="center", font=("Helvetica", 9))
        self.status_label.pack(pady=5)

    def browse_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        if filepath:
            self.file_path_var.set(filepath)
            self.status_var.set("File waa la doortay.")

    def process_data(self):
        input_file = self.file_path_var.get()
        target_str = self.target_var.get()
        
        if not input_file or not os.path.exists(input_file):
            messagebox.showerror("Cilad", "Fadlan marka hore isticmaal 'Browse...' si aad u xulato file CSV ah!")
            return
            
        try:
            target_count = int(target_str)
            if target_count <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Cilad", "Fadlan geli tiro sax ah meesha tirada. Tusaale ahaan: 5000")
            return

        self.status_var.set("Processing... fadlan waxyar sug...")
        self.root.update()

        try:
            df = pd.read_csv(input_file)
        except Exception as e:
            messagebox.showerror("Cilad Akhris", f"Waa la akhriyi waayay file-ka. Ciladda: {e}")
            self.status_var.set("Cilad ayaa dhacday")
            return

        if 'category' not in df.columns:
            messagebox.showerror("Cilad", "Column-ka 'category' laguma arkin dhexda file-ka CSV-ga.")
            self.status_var.set("Cilad: category column ma jiro")
            return

        # Clean text
        df['category'] = df['category'].astype(str).str.strip().str.lower()

        # Filter
        crime_df = df[df['category'] == 'crime-related']
        non_crime_df = df[df['category'] == 'not crime-related']

        # Fallback if exact matching doesn't work
        if len(crime_df) == 0 and len(non_crime_df) == 0:
             crime_df = df[df['category'].str.contains('crime', na=False) & ~df['category'].str.contains('not crime', na=False)]
             non_crime_df = df[df['category'].str.contains('not crime', na=False) | df['category'].str.contains('none', na=False)]

        if len(crime_df) == 0 and len(non_crime_df) == 0:
            messagebox.showwarning("Xog la'aan", "Wax xog ah oo ah 'crime-related' ama 'not crime-related' lagama helin file-kaan.")
            self.status_var.set("Xog lagama helin.")
            return

        selected_crime_count = min(target_count, len(crime_df))
        selected_non_crime_count = min(target_count, len(non_crime_df))
        
        crime_sampled = crime_df.sample(n=selected_crime_count, random_state=42)
        non_crime_sampled = non_crime_df.sample(n=selected_non_crime_count, random_state=42)

        output_dir = os.path.dirname(os.path.abspath(input_file))

        crime_out = os.path.join(output_dir, f"crime_related_{len(crime_sampled)}.csv")
        non_crime_out = os.path.join(output_dir, f"not_crime_related_{len(non_crime_sampled)}.csv")
        
        crime_sampled.to_csv(crime_out, index=False)
        non_crime_sampled.to_csv(non_crime_out, index=False)
        
        combined_df = pd.concat([crime_sampled, non_crime_sampled])
        combined_df = combined_df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        combined_out = os.path.join(output_dir, f"combined_balanced_data_{len(combined_df)}.csv")
        combined_df.to_csv(combined_out, index=False)

        success_msg = (
            f"Waa lagu guuleystay shaqadii!\n\n"
            f"Crime-related (Isugayn la helay): {len(crime_df)}\n"
            f"Crime-related (Laga soo qaatay): {len(crime_sampled)}\n\n"
            f"Not crime-related (Isugayn la helay): {len(non_crime_df)}\n"
            f"Not crime-related (Laga soo qaatay): {len(non_crime_sampled)}\n\n"
            f"Faylasha cusub waxaa la soo dhigay isla galkii (folder-kii) ee uu CSV-ga ku jiray."
        )
        
        self.status_var.set("Shaqada si guul ah ayey ku idlaatay!")
        messagebox.showinfo("Guul", success_msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = DataSeparatorGUI(root)
    root.mainloop()
