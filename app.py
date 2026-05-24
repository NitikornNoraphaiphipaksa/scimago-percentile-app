import streamlit as st
import pandas as pd
import re

# Page setup
st.set_page_config(page_title="Scimago Percentile Calculator", layout="wide")
st.title("📊 Scimago Journal Category & Percentile Finder")
st.write("Upload your Scimago export CSV to calculate optimized metrics and see specific category quartiles.")

# 1. File Uploader
uploaded_file = st.file_uploader("Step 1: Upload your Scimago CSV File", type=["csv"])

if uploaded_file is not None:
    # Read the dataset (handle semicolon separated files common in Scimago)
    try:
        df = pd.read_csv(uploaded_file, sep=';')
    except Exception:
        df = pd.read_csv(uploaded_file, sep=',')
        
    # Clean up column spaces
    df.columns = df.columns.str.strip()
    
    if 'SJR' in df.columns:
        # Convert regional comma format (0,304) to clean float notation (0.304)
        df['SJR_clean'] = df['SJR'].astype(str).str.replace(',', '.').astype(float)
    else:
        st.error("Could not find the 'SJR' column in the uploaded CSV file.")
        st.stop()

    # 2. Select Journal Title Dropdown
    journal_titles = sorted(df['Title'].dropna().unique())
    selected_journal = st.selectbox("Step 2: Choose or type a Journal Title", options=journal_titles)

    if selected_journal:
        # Get the row metadata for the selected journal
        journal_row = df[df['Title'] == selected_journal].iloc[0]
        categories_raw = journal_row['Categories']
        
        # Clean and display the SJR score
        sjr_display = str(journal_row['SJR']).replace(',', '.')
        
        st.subheader(f"Results for: *{selected_journal}*")
        st.info(f"**Global SJR Score:** {sjr_display}")
        
        # 3. Extract and parse categories and their specific quartiles
        # Split "Mechanical Engineering (Q3); Mechanics of Materials (Q3)"
        raw_category_list = [cat.strip() for cat in categories_raw.split(';')]
        
        results = []
        
        # Calculate rank and percentile inside each category
        for raw_cat in raw_category_list:
            if not raw_cat:
                continue
                
            # Extract category name and quartile using regex
            # e.g., "Mechanical Engineering (Q3)" -> Name: "Mechanical Engineering", Quartile: "Q3"
            match = re.match(r"^(.*?)\s*\((Q[1-4])\)$", raw_cat)
            if match:
                category_name = match.group(1).strip()
                quartile_value = match.group(2).strip()
            else:
                category_name = raw_cat
                quartile_value = "N/A"
            
            # Filter rows containing this specific category name
            cat_df = df[df['Categories'].str.contains(category_name, case=False, na=False)].copy()
            
            # Sort by SJR descending to establish accurate ranking within this category
            cat_df = cat_df.sort_values(by='SJR_clean', ascending=False).reset_index(drop=True)
            cat_df['Category_Rank'] = cat_df.index + 1
            
            total_journals_in_cat = len(cat_df)
            
            # Identify where our target journal sits in this sub-category
            match_row = cat_df[cat_df['Title'] == selected_journal]
            if not match_row.empty:
                rank_in_cat = match_row['Category_Rank'].values[0]
                
                # Formula: 1 - (Rank / Total) * 100
                percentile = (1 - (rank_in_cat / total_journals_in_cat)) * 100
                
                results.append({
                    "Category Sub-Area": category_name,
                    "Quartile": quartile_value,
                    "SJR Score": sjr_display,
                    "Rank": rank_in_cat,
                    "Total Journals": total_journals_in_cat,
                    "Percentile Placement (%)": round(percentile, 2),
                    "Rank / Total": f"{rank_in_cat} / {total_journals_in_cat}"
                })
        
        # Convert results list to a clean dataframe
        results_df = pd.DataFrame(results)
        
        if not results_df.empty:
            # Find the best entry (the highest percentile)
            best_idx = results_df['Percentile Placement (%)'].idxmax()
            best_category = results_df.loc[best_idx, 'Category Sub-Area']
            best_percentile = results_df.loc[best_idx, 'Percentile Placement (%)']
            best_quartile = results_df.loc[best_idx, 'Quartile']
            
            # Display summary metric callout box
            st.success(f"🏆 **Best Performing Category:** {best_category} ({best_quartile} | {best_percentile}% Percentile)")
            
            # Highlight max row and use a color background style for the Percentile column
            styled_df = results_df.style.background_gradient(
                subset=['Percentile Placement (%)'], 
                cmap='YlGnBu'  # Beautiful yellow-green-blue gradient shading
            ).highlight_max(
                axis=0, 
                subset=['Percentile Placement (%)'], 
                color='#bfa'  # Highlight the absolute highest rank row with a bright light green row accent
            )
            
            # Display interactive formatted table
            st.dataframe(styled_df, use_container_width=True)
            st.caption("*Tip: The row containing the maximum percentile is highlighted in light green, while the percentile column uses shading scales to represent performance density.*")
        else:
            st.warning("No category rankings could be extracted for this entry.")
