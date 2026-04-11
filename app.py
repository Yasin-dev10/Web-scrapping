import streamlit as st
import pandas as pd
import sqlite3
import random
import os
import subprocess
from database import init_db, get_connection

# App configuration
st.set_page_config(page_title="All-In-One Scraper Dashboard", layout="wide")

# Initialize DB on start
init_db()

st.title("All-In-One Web App (General GUI)")

# Qaybaha (Modules) ee la heli karo
menu = [
    "1. Dashboard (Xogta Guud)", 
    "2. Xogta (Data View)", 
    "7. CSV Merger (Soo Gelinta Xogta)",
    "8. Data Validator (Hubinta Xogta)",
    "6. Data Separator (Kala Saar & Balans)",
    "3. Facebook Scraper", 
    "4. News Scraper", 
    "5. Telecom Scraper"
]
choice = st.sidebar.selectbox("Dooro Qaybta Tool-ka aad rabto:", menu)

st.sidebar.markdown("---")
st.sidebar.write("### Waa nidaam dhameystiran oo bedelaya Script-yadii hore ee Python.")

if choice == "1. Dashboard (Xogta Guud)":
    st.subheader("Ku Soo Dhawow Web Dashboard-ka")
    st.write("Halkan waxaad uga jeedaa warbixinta guud ee xogta ku keydsan Database-ka.")
    
    conn = get_connection()
    df = pd.read_sql_query("SELECT category, COUNT(*) as tirada FROM posts GROUP BY category", conn)
    conn.close()
    
    if not df.empty:
        st.bar_chart(df.set_index('category'))
        st.write(df)
    else:
        st.info("Kuma jirto wax xog ah Database-ka hadda. Fadlan xog soo geli.")

elif choice == "2. Xogta (Data View)":
    st.subheader("Macluumaadka ku jira Database-ka")
    
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM posts", conn)
    conn.close()
    
    if not df.empty:
        category_filter = st.selectbox("Sifee Nooca Xogta:", ["Dhan (All)"] + list(df['category'].unique()))
        if category_filter != "Dhan (All)":
            df_filtered = df[df['category'] == category_filter]
        else:
            df_filtered = df
            
        st.dataframe(df_filtered, use_container_width=True)
    else:
        st.info("Kuma jirto wax xog ah Database-ka hadda.")

elif choice == "7. CSV Merger (Soo Gelinta Xogta)":
    st.subheader("1. Soo Gelinta Xogta (Data Importer)")
    st.write("Qaybtani waa halka aad kasoo bilaabayso. Halkan kasoo Upload garee files CSV ah, si toos ah ayaana loogu geynayaa Database-ka, kadibna qaybta 'Validator' iyo 'Separator' ayaad ula gudbi kartaa.")
    
    uploaded_files = st.file_uploader("Dooro CSV files-ka si toos loogu guro Database", accept_multiple_files=True, type='csv')
    
    if st.button("Midee oo Geli Database-ka (Merge & Insert)"):
        if uploaded_files:
            from database import insert_post
            total_added = 0
            for file in uploaded_files:
                try:
                    df = pd.read_csv(file)
                    count = 0
                    for _, row in df.iterrows():
                        url = row.get('Url', row.get('URL', 'Na'))
                        text = row.get('Text', row.get('text', str(row)))
                        category = row.get('Category', row.get('category', 'None'))
                        insert_post(url, text, category, file.name)
                        count += 1
                        total_added += 1
                    st.write(f"✅ {count} xog ayaa laga soo qaatay: {file.name}")
                except Exception as e:
                    st.error(f"Cilad baa ka dhacday akhriska faylka {file.name}: {e}")
            st.success(f"Wadar ahaan {total_added} ayaa lagu daray Database-ka! Hadda tag qaybta 'Data Validator' si aad u habayso.")
        else:
            st.error("Fadlan soo dooro files-ka ugu yaraan 1 CSV.")

elif choice == "8. Data Validator (Hubinta Xogta)":
    st.subheader("2. Hubiyaha Xogta (Manual Data Validator)")
    st.write("Mid-mid u akhri qoraalada lagu soo shubay Database-ka oo sax noocooda (Crime vs Not Crime) adigoo bedelaya Database-ka isla markiiba.")
    
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
        
    conn = get_connection()
    df = pd.read_sql_query("SELECT id, text, category FROM posts", conn)
    conn.close()
    
    if not df.empty:
        total_rows = len(df)
        
        if st.session_state.current_index < total_rows:
            current_row = df.iloc[st.session_state.current_index]
            
            st.write(f"**Tirada:** {st.session_state.current_index + 1} / {total_rows}")
            
            st.markdown("### Qoraalka (Text):")
            st.info(current_row['text'])
            
            st.markdown(f"**Category Hadda:** `{current_row['category']}`")
            
            st.write("---")
            col1, col2, col3, col4 = st.columns(4)
            
            def update_db(post_id, new_cat):
                c = get_connection()
                cur = c.cursor()
                cur.execute("UPDATE posts SET category=? WHERE id=?", (new_cat, post_id))
                c.commit()
                c.close()
                st.session_state.current_index += 1
            
            with col1:
                if st.button("🩸 Ka dhig: Crime"):
                    update_db(current_row['id'], 'crime-related')
                    st.rerun()
            with col2:
                if st.button("🟢 Ka dhig: Not Crime"):
                    update_db(current_row['id'], 'not crime-related')
                    st.rerun()
            with col3:
                if st.button("✅ Sax (Ku Dhaaf / Skip)"):
                    st.session_state.current_index += 1
                    st.rerun()
            with col4:
                if st.button("⬅️ Gadaal u noqo") and st.session_state.current_index > 0:
                    st.session_state.current_index -= 1
                    st.rerun()
        else:
            st.success("Waxaad dhamaysay dhammaan xogta ku jirta Database-ka! Hadda waxaad tagi kartaa Data Separator si aad u kala qaadato.")
            if st.button("Dib ugu noqo bilowga"):
                st.session_state.current_index = 0
                st.rerun()
    else:
        st.warning("Database-ka wax xog ah kuma jiraan. Fadlan tag 'CSV Merger' oo soo geli.")

elif choice == "6. Data Separator (Kala Saar & Balans)":
    st.subheader("3. Data Separator & Balancer (Kala Saar & Isku Dheeli-tir)")
    st.write("Halkan xogtii aad soo Validate-gareysay ayaad ku kala dhigaysaa Crime iyo Not-Crime, adigoo dooranaya inta tirada aad u rabto fayl walba.")
    
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM posts", conn)
    conn.close()
    
    if not df.empty:
        df['clean_category'] = df['category'].astype(str).str.strip().str.lower()
        crime_df = df[df['clean_category'].str.contains('crime', na=False) & ~df['clean_category'].str.contains('not crime', na=False)]
        non_crime_df = df[df['clean_category'].str.contains('not crime', na=False) | df['clean_category'].str.contains('none', na=False)]
        
        st.write(f"**Dalabka Database-ka (Xogta Hadda Diyaarka Ah):** Crime: `{len(crime_df)}` | Not Crime: `{len(non_crime_df)}`")
        
        target_count = st.number_input("Tirada File kasta aad rabto inuu noqdo (Tus. 500):", min_value=1, value=50)
        
        if st.button("Kala Saar & Balans garee (Run Separator)"):
            selected_crime_count = min(target_count, len(crime_df))
            selected_non_crime_count = min(target_count, len(non_crime_df))
            
            if selected_crime_count > 0 and selected_non_crime_count > 0:
                crime_sampled = crime_df.sample(n=selected_crime_count, random_state=42).drop(columns=['clean_category'])
                non_crime_sampled = non_crime_df.sample(n=selected_non_crime_count, random_state=42).drop(columns=['clean_category'])
                
                st.success(f"Waa la kala saaray! Crime: {len(crime_sampled)} | Not Crime: {len(non_crime_sampled)}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button("Download Crime CSV", data=crime_sampled.to_csv(index=False).encode('utf-8'), file_name="crime_related_balanced.csv", mime="text/csv")
                with col2:
                    st.download_button("Download Not-Crime CSV", data=non_crime_sampled.to_csv(index=False).encode('utf-8'), file_name="not_crime_related_balanced.csv", mime="text/csv")
                with col3:
                    combined = pd.concat([crime_sampled, non_crime_sampled]).sample(frac=1, random_state=42)
                    st.download_button("Download Combined CSV", data=combined.to_csv(index=False).encode('utf-8'), file_name="combined_balanced_data.csv", mime="text/csv")
            else:
                st.error("Xog uma filna inaad kala saarto, fadlan horta Validate soo garee ama so scrape-garee.")
    else:
        st.warning("Database-ka waa madhan yahay.")

elif choice == "3. Facebook Scraper":
    st.subheader("Facebook Scraper Tool")
    if st.button("Run Facebook Scraper"):
        subprocess.Popen(["python", "facebook_scraper_gui.py"])
        st.success("App-ka Facebook Scraper waa furmay!")

elif choice == "4. News Scraper":
    st.subheader("Web News Scraper Tool")
    if st.button("Run News Scraper"):
        subprocess.Popen(["python", "news_scraper_gui.py"])
        st.success("App-ka News Scraper waa furmay!")

elif choice == "5. Telecom Scraper":
    st.subheader("Telecom Complaints Scraper Tool")
    if st.button("Run Telecom Scraper"):
        subprocess.Popen(["python", "telecom_complaints_scraper_gui.py"])
        st.success("App-ka Telecom Scraper waa furmay!")
