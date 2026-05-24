import streamlit as st
import pandas as pd

# Page setup
st.set_page_config(page_title="Scimago Percentile Calculator", layout="wide")
st.title("📊 Scimago Journal Category & Percentile Finder")
st.write("Upload your Scimago export CSV to find the best ranking category for any journal.")

# 1. File Uploader
uploaded_file = st.file_uploader("Step 1: Upload your Scimago CSV File", type=["csv"])

if uploaded_file is not None:
    # Read the dataset (handle semicolon separated files common in Scimago)
    try:
        df = pd.read_csv(uploaded_file, sep=';')
    except Exception:
        df = pd.read_csv(uploaded_file, sep=',')
        
    # Clean up column spaces and convert SJR commas to dots for mathematical computation
    df.columns = df.columns.str.strip()
    if 'SJR' in df.columns:
        df['SJR_clean'] = df['SJR'].astype(str).str.replace(',', '.').astype(float)
    else:
        st.error("Could not find the 'SJR' column in the uploaded CSV file. Please check the export format.")
        st.stop()

    # 2. Select Journal Title Dropdown
    journal_titles = sorted(df['Title'].dropna().unique())
    selected_journal = st.selectbox("Step 2: Choose or type a Journal Title", options=journal_titles)

    if selected_journal:
        # Get the row metadata for the selected journal
        journal_row = df[df['Title'] == selected_journal].iloc[0]
        categories_raw = journal_row['Categories']
        
        st.subheader(f"Results for: *{selected_journal}*")
        st.info(f"**Global SJR Score:** {journal_row['SJR']}")
        
        # 3. Extract and parse all categories listed for this journal
        # e.g., "Mechanical Engineering (Q3); Mechanics of Materials (Q3)" -> ['Mechanical Engineering', 'Mechanics of Materials']
        journal_categories = [cat.split('(')[0].strip() for cat in categories_raw.split(';')]
        
        results = []
        
        # Calculate rank and percentile inside each category
        for category in journal_categories:
            # Filter rows containing this category
            cat_df = df[df['Categories'].str.contains(category, case=False, na=False)].copy()
            # Sort by SJR descending to rank locally
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
                    "Category Sub-Area": category,
                    "Rank": rank_in_cat,
                    "Total Journals": total_journals_in_cat,
                    "Percentile Placement": round(percentile, 2),
                    "Display String": f"{rank_in_cat} / {total_journals_in_cat}"
                })
        
        # Convert results list to a clean dataframe
        results_df = pd.DataFrame(results)
        
        if not results_df.empty:
            # Find the best entry (the highest percentile)
            best_idx = results_df['Percentile Placement'].idxmax()
            best_category = results_df.loc[best_idx, 'Category Sub-Area']
            best_percentile = results_df.loc[best_idx, 'Percentile Placement']
            
            # Display summary metric callout box
            st.success(f"🏆 **Best Performing Category:** {best_category} ({best_percentile}% Percentile)")
            
            # Display interactive table of all options
            st.dataframe(
                results_df.style.highlight_max(axis=0, subset=['Percentile Placement'], color='#d4edda'), 
                use_container_width=True
            )
            
            st.caption("*Note: The row highlighted green represents the best percentile ranking for this journal.*")
        else:
            st.warning("No category rankings could be extracted for this entry.")