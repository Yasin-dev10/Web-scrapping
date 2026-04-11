import streamlit as st
import pandas as pd
import sqlite3
from database import init_db, get_connection

# App configuration
st.set_page_config(page_title="Scraper Dashboard", layout="wide")

# Initialize DB on start
init_db()

st.title("Data Scraper Dashboard (Crime vs Non-Crime)")

menu = ["Dashboard (Xogta Guud)", "Xogta (Data View)", "Tijaabi Scraper"]
choice = st.sidebar.selectbox("Dooro Qaybta:", menu)

if choice == "Dashboard (Xogta Guud)":
    st.subheader("Ku Soo Dhawow Web Dashboard-ka")
    st.write("Waa nidaam loogu tala galay in xogta lagu uruuriyo, database lagu keydiyo, loona kala saaro Crime iyo Not Crime.")
    
    conn = get_connection()
    df = pd.read_sql_query("SELECT category, COUNT(*) as tirada FROM posts GROUP BY category", conn)
    conn.close()
    
    if not df.empty:
        st.bar_chart(df.set_index('category'))
        st.write(df)
    else:
        st.info("Kuma jirto wax xog ah Database-ka hadda. Fadlan xog soo geli ama 'scrape' garee (Adigoo tagaya Xogta (Data View) ama isticmaalaya script-ka).")

elif choice == "Xogta (Data View)":
    st.subheader("Macluumaadka ku jira Database-ka")
    
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM posts", conn)
    conn.close()
    
    if not df.empty:
        # Filtering functionality
        category_filter = st.selectbox("Sifee Nooca Xogta (Filari Nooca):", ["Dhan (All)"] + list(df['category'].unique()))
        if category_filter != "Dhan (All)":
            df_filtered = df[df['category'] == category_filter]
        else:
            df_filtered = df
            
        st.dataframe(df_filtered, use_container_width=True)
        
        # Download Data
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Data as CSV",
            data=csv,
            file_name='database_export.csv',
            mime='text/csv',
        )
    else:
        st.info("Kuma jirto wax xog ah Database-ka hadda.")

elif choice == "Tijaabi Scraper":
    st.subheader("Ku shubida xogta Database-ka")
    st.write("Qaybtan waa tusaale ku tusaya in xogta ay si toos ah u geleyso Database-ka (CSV la'aan).")
    
    with st.form("add_sample_data"):
        sample_url = st.text_input("URL:")
        sample_text = st.text_area("Qoraalka (Text):")
        sample_category = st.selectbox("Nooca (Category):", ["Crime", "Not Crime", "None"])
        sample_source = st.selectbox("Isha (Source):", ["Facebook", "News", "Other"])
        
        submit = st.form_submit_button("Ku Dar Xogta (Save to DB)")
        
        if submit:
            if sample_url and sample_text:
                from database import insert_post
                insert_post(sample_url, sample_text, sample_category, sample_source)
                st.success("Xogta si guul leh ayaa loogu daray Database-ka! Tag 'Xogta (Data View)' si aad u aragto.")
            else:
                st.error("Fadlan buuxi meelaha banaan.")
