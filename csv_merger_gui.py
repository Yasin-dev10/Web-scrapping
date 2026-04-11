import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import os
from datetime import datetime

class CSVMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV File Merger Tool")
        self.root.geometry("600x400")
        self.root.configure(padx=20, pady=20)
        
        self.selected_files = []
        
        # Title
        title_label = tk.Label(root, text="Isku Dar CSV Files Cadaan/Fudud (Merge CSVs)", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Step 1: Select files button
        self.select_btn = tk.Button(root, text="1. Dooro CSV Files-ka (Select Files)", command=self.select_files, width=40, height=2, bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold"))
        self.select_btn.pack(pady=10)
        
        # Listbox to show selected files
        self.files_listbox = tk.Listbox(root, selectmode=tk.MULTIPLE, width=70, height=8)
        self.files_listbox.pack(pady=5)
        
        # Clear button
        self.clear_btn = tk.Button(root, text="Nadiifi (Clear List)", command=self.clear_files, width=20)
        self.clear_btn.pack(pady=5)
        
        # Step 2: Merge button
        self.merge_btn = tk.Button(root, text="2. Isku Dar (Merge Now)", command=self.merge_csvs, width=40, height=2, bg="#2196F3", fg="white", font=("Helvetica", 10, "bold"))
        self.merge_btn.pack(pady=15)
        
        # Status Label
        self.status_label = tk.Label(root, text="Fadlan dooro files...", fg="gray")
        self.status_label.pack(side=tk.BOTTOM, pady=5)

    def select_files(self):
        file_paths = filedialog.askopenfilenames(
            title="Soco CSV files-ka aad rabto",
            filetypes=[("CSV files", "*.csv")]
        )
        if file_paths:
            for path in file_paths:
                if path not in self.selected_files:
                    self.selected_files.append(path)
                    self.files_listbox.insert(tk.END, os.path.basename(path))
            
            self.status_label.config(text=f"{len(self.selected_files)} files selected.", fg="black")

    def clear_files(self):
        self.selected_files.clear()
        self.files_listbox.delete(0, tk.END)
        self.status_label.config(text="Liiska waa la nadiifiyay.", fg="gray")

    def merge_csvs(self):
        if not self.selected_files:
            messagebox.showwarning("Digniin", "Fadlan marka hore dooro CSV files-ka!")
            return
            
        if len(self.selected_files) < 2:
            messagebox.showinfo("Macluumaad", "Hal file ayaad dooratay, ugu yaraan 2 file ayaa loo baahanyahay si isku darid loo sameeyo.")
            return

        save_path = filedialog.asksaveasfilename(
            title="Xagee rabtaa in la dhigo file-ka cusub?",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"merged_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if not save_path:
            return
            
        self.status_label.config(text="Waa la isku darayaa, fadlan sug...", fg="blue")
        self.root.update()
        
        try:
            dataframes = []
            for file in self.selected_files:
                try:
                    df = pd.read_csv(file)
                    dataframes.append(df)
                except Exception as e:
                    messagebox.showerror("Cilad (Error)", f"Cilad ayaa ka dhacday akhrinta file-ka:\n{os.path.basename(file)}\nError: {e}")
                    self.status_label.config(text="Cilad ayaa dhacday.", fg="red")
                    return
            
            # Merge all dataframes
            merged_df = pd.concat(dataframes, ignore_index=True)
            
            # Save to new csv
            merged_df.to_csv(save_path, index=False)
            
            self.status_label.config(text="Si guul leh ayaa loo isku daray! (Success)", fg="green")
            messagebox.showinfo("Guul", f"{len(self.selected_files)} files ayaa si guul leh la isugu daray.\n\nFile-ka cusub: {os.path.basename(save_path)}\nTirada guud ee xogta (Rows): {len(merged_df)}")
            
        except Exception as e:
            messagebox.showerror("Cilad", f"Waxa dhacday cilad aan la fileyn:\n{e}")
            self.status_label.config(text="Cilad ayaa dhacday.", fg="red")


if __name__ == "__main__":
    root = tk.Tk()
    app = CSVMergerApp(root)
    root.mainloop()
