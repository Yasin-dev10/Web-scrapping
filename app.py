import streamlit as st
import pandas as pd
import sqlite3
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
    "3. Facebook Scraper", 
    "4. News Scraper", 
    "5. Telecom Scraper",
    "6. Data Separator & Validator",
    "7. CSV Merger"
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

elif choice == "3. Facebook Scraper":
    st.subheader("Facebook Scraper Tool")
    st.write("Soo saar xogta Facebook iyo Posts-ka maamula:")
    fb_url = st.text_input("Geli URL-ka Bogga Facebook:")
    limit = st.slider("Imisa Post ayaad rabtaa in lasoo saaro?", 1, 100, 10)
    
    if st.button("Run Facebook Scraper"):
        st.warning("Tool-kaan waa la diyaarinayaa si Database-ka toos ugu xirmo!")
        # Later we can import the Facebook scraper functions here

elif choice == "4. News Scraper":
    st.subheader("Web News Scraper Tool")
    st.write("Soo saar xogta Warbaahinta/News:")
    news_url = st.text_input("Geli URL-ka Warbaahinta (News Site):")
    if st.button("Run News Scraper"):
        st.warning("Tool-kaan waa la diyaarinayaa si toos Database-ka ugu xirmo!")

elif choice == "5. Telecom Scraper":
    st.subheader("Telecom Complaints Scraper Tool")
    st.write("Soo saar Cabashooyinka Telecom-ka (Complaints vs None)")
    if st.button("Run Telecom Scraper"):
         st.warning("Shaqadan waxaa lagu darayaa dhowaan si toos DB u gasho.")

elif choice == "6. Data Separator & Validator":
    st.subheader("Hubinta iyo Kala Saarista Xogta (Validator & Separator)")
    st.write("Maamul oo sax qaladka xogta ku jirta Database-ka inta aadan u qeybin Crime vs Not Crime.")
    
    conn = get_connection()
    df_validate = pd.read_sql_query("SELECT * FROM posts LIMIT 10", conn)
    conn.close()
    
    if not df_validate.empty:
        st.write("Tusaale kamid ah Xogta si aad Validate u sameyso:")
        st.dataframe(df_validate)
        if st.button("Validate & Separate All Data"):
            st.success("Xogta si otomaatig ah ayey isku Validate-gareysay (Mawduucan wali waa la hormarinayaa).")
    else:
        st.warning("Xog kuma jirto DB si loo kala saaro.")

elif choice == "7. CSV Merger":
    st.subheader("CSV Merger / Data Importer")
    st.write("Halkan waxaad ka isku dari kartaa files/Upload CSV.")
    uploaded_files = st.file_uploader("Dooro CSV files-ka si toos loogu guro Database", accept_multiple_files=True, type='csv')
    if st.button("Midee oo Geli Database-ka (Merge & Insert)"):
        if uploaded_files:
            import pandas as pd
            from database import insert_post
            for file in uploaded_files:
                df = pd.read_csv(file)
                # Simple logic to save
                count = 0
                for _, row in df.iterrows():
                    url = row.get('Url', row.get('URL', ''))
                    text = row.get('Text', row.get('text', str(row)))
                    category = row.get('Category', row.get('category', 'None'))
                    insert_post(url, text, category, file.name)
                    count += 1
                st.success(f"Waa la miday oo DB ayaa la geliyay {count} xogta {file.name}")
        else:
            st.error("Fadlan soo dooro files-ka ugu yaraan 1 CSV.")
