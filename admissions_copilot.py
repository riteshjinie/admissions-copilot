import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import json
import re
import streamlit.components.v1 as components



st.set_page_config(
    page_title="Engineering Admissions Copilot - JoSSA 2025",
    page_icon="🎓",
    layout="wide"
)

components.html(
    """
    <!-- Global site tag (gtag.js) - Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-39DYHCZPD3"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-39DYHCZPD3');
    </script>
    """,
    height=0,
)

# Setup Gemini

# Use secret from .streamlit/secrets.toml
import google.generativeai as genai
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

cutoffs = pd.read_csv("cutoffs2023-2024.csv")

institutes = sorted(cutoffs['Institute'].dropna().unique())
branches = sorted(cutoffs['Branch'].dropna().unique())
genders = sorted(cutoffs['Gender'].dropna().unique())
years = sorted(cutoffs['Year'].dropna().unique())
rounds = sorted(cutoffs['Round'].dropna().unique())

# Map common abbreviations to full branch keyword
branch_map = {
    "cs": "computer",
    "cse": "computer",
    "computer science": "computer",
    "computers": "computer",
    "ece": "electronics and communication",
    "ee": "electrical",
    "arch": "architecture",
    # Add more if needed
}

institute_map = {
    "iit": "indian institute of technology",
    "iits": "indian institute of technology",
    "all iits": "indian institute of technology",
    "nit": "national institute of technology",
    "nits": "national institute of technology",
    "all nits": "national institute of technology",
    "iiit": "indian institute of information technology",
    "iiits": "indian institute of information technology",
    "all iiits": "indian institute of information technology",
    # Add more if needed
}

# Streamlit UI
st.subheader("🎓 Engineering Admissions Copilot - JoSSA 2025")
#st.subheader("JoSSA 2025 predictions based on 2024 cutoff data")

st.markdown(
    """
    <p style="font-size:16px; color:gray; text-align:left;">
    This tool is an open-source initiative to help organize JoSAA 2023, 2024 cutoff data for easier exploration.  
    All data is used as-is and may contain errors. Use this tool at your own risk. The author is not liable for any inaccuracies or decisions based on this data.
    </p>
    """,
    unsafe_allow_html=True,
)

# Radio button outside the form
exam_type = st.radio("Which exam rank are you using?", ["JEE Mains", "JEE Advanced"])

# Outside the form: handle dynamic interactivity
crl = st.number_input("Enter your rank from " + exam_type, min_value=1, value=1000)
use_range = st.checkbox("Search within ± range?")
if use_range:
    rank_range = st.number_input("Enter range value", min_value=1, max_value=1000, value=200)

with st.form("form"):
    
    category = st.selectbox("Category", ["OPEN", "OPEN (Pwd)", "OBC-NCL", "OBC-NCL (PwD)", "SC", "SC (PwD)", "ST", "ST (PwD)", "EWS", "EWS (PwD)"])
    gender = st.selectbox("Gender", genders, index=1)
    #state = st.text_input("Domicile State")
    year = st.selectbox("Year", years, index=len(years)-1)
    round_selected = st.selectbox("Select JoSAA Round", ["ANY"] + rounds, index=1)

    # Modify the institute options based on exam_type
    if exam_type == "JEE Advanced":
        allowed_institutes = sorted([i for i in institutes if i.startswith("Indian Institute of Technology")])
        selected_institute = st.selectbox("Filter by Institute", ["All IITs"] + allowed_institutes)
        #selected_institute = st.selectbox("Institute (Only IITs allowed for JEE Advanced)", sorted([i for i in institutes if "Indian Institute of Technology" in i]), index=0, disabled=True)
    else:
        allowed_institutes = sorted([i for i in institutes if not i.startswith("Indian Institute of Technology")])
        selected_institute = st.selectbox("Filter by Institute", ["All except IITs", "All NITs"] + allowed_institutes)

    
    #selected_institute = st.selectbox("Filter by Institute", ["All", "IITs", "NITs"] + institutes)



    branch_query = st.text_input("Filter by Branch (comma-separated) (for example: cs, ece, electrical, civil)", "")
    submit = st.form_submit_button("Find Colleges")

if submit:
    # Filter based on CRL, category etc
    if use_range:
        lower_bound = crl - rank_range
        upper_bound = crl + rank_range
        matches = cutoffs[
            (cutoffs['Closing Rank'] >= lower_bound) &
            (cutoffs['Closing Rank'] <= upper_bound) &
            (cutoffs['Category'].str.lower() == category.lower()) &
            (cutoffs['Gender'].str.lower() == gender.lower()) &
            (cutoffs['Year'] == year)
        ]
    else:
        matches = cutoffs[
            (cutoffs['Closing Rank'] >= crl) &
            (cutoffs['Category'].str.lower() == category.lower()) &
            (cutoffs['Gender'].str.lower() == gender.lower()) &
            (cutoffs['Year'] == year)
        ]
    if round_selected != "ANY":
        matches = matches[matches['Round'] == round_selected]

    # Apply optional institute filter
    selected_institute_normalized = selected_institute.strip().lower()

    if selected_institute_normalized == "all except iits":
        # Exclude institutes that contain "indian institute of technology" (IITs)
        matches = matches[~matches['Institute'].str.lower().str.contains("indian institute of technology", regex=False)]
    else:
        # Replace if found in map
        if selected_institute_normalized in institute_map:
            selected_institute = institute_map[selected_institute_normalized]
        else:
            selected_institute = selected_institute_normalized

        matches = matches[matches['Institute'].str.lower().str.contains(selected_institute.lower(), regex=False)]

    # Apply optional branch filter
    if branch_query.strip() != "":
        # Normalize and split input
        branch_keywords = [kw.strip().lower() for kw in branch_query.split(",") if kw.strip()]

        # Apply branch_map replacements if any
        branch_keywords = [branch_map.get(kw, kw) for kw in branch_keywords]

        # Check if user explicitly asked for architecture or planning
        include_architecture = any("arch" in kw for kw in branch_keywords)
        include_planning = any("plan" in kw for kw in branch_keywords)

        # Exclude architecture/planning-related branches unless explicitly included
        if not include_architecture:
            matches = matches[~matches['Branch'].str.lower().str.contains("architecture|arch", regex=True)]
        if not include_planning:
            matches = matches[~matches['Branch'].str.lower().str.contains("planning|plan", regex=True)]

        # Apply filter: match if any keyword appears in the branch name
        pattern = '|'.join(branch_keywords)
        matches = matches[matches['Branch'].str.lower().str.contains(pattern)]
    else:
        # No branch filter, exclude both architecture and planning
        matches = matches[~matches['Branch'].str.lower().str.contains("architecture|arch|planning|plan", regex=True)]


    # Drop duplicates based on key columns
    matches_unique = matches.drop_duplicates(subset=['Institute', 'Branch', 'Category'])

    if matches_unique.empty:
        st.warning("⚠️ Sorry, no colleges found for your profile.")
    else:
        st.success(f"🎯 Found {len(matches_unique)} possible options based on cutoffs in " + str(year))

        # Select only relevant columns
        display_data = matches_unique[['Closing Rank', 'Institute', 'Branch', 'Round']].sort_values(by='Closing Rank')

        # Reset index and convert to records for clean display
        display_data = display_data.reset_index(drop=True)

        # Convert to a format that Streamlit doesn't try to add index to
        st.dataframe(display_data.style.hide(axis='index'), use_container_width=True)



st.markdown("---")  # Horizontal line separator


# Gemini assistant

# Suggested example questions
sample_questions = [
    "What NITs can I get with 15000 rank for ECE?",
    "Show me IITs accepting 8000 rank for Computer Science.",
    "What are my options in Round 3 with rank 23000 for SC category?",
    "Can I get Mechanical in NIT with 12000 rank?",
    "What branches were available in IITs above 6000 CRL in year 2023?"
]

# UI section for hybrid input
st.subheader("🤖 Ask Admissions Copilot")

st.markdown(
    """
    <p style="font-size:16px; color:gray; text-align:left;">
    This section is an attempt to provide the same information using GenAI by understanding an English query.
    The system is able to understand simple queries with one branch, one college type and a rank but may fail at complex ones. Give it a try!
    </p>
    """,
    unsafe_allow_html=True,
)

selected_example = st.selectbox("💡 Choose a sample question:", [""] + sample_questions)
custom_question = st.text_area("Or type your own question below:")

# Final question used for processing
final_question = custom_question.strip() if custom_question.strip() else selected_example


def trigger_gemini():
    st.session_state["last_question"] = final_question
    st.session_state["run_query"] = True

st.button("Ask", on_click=trigger_gemini)

if st.session_state.get("run_query", False) and st.session_state.get("last_question", "").strip():
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = f"""
        You're an Indian college admission counselor.
        You are helping students get admission into engineering colleges via JoSAA.

        Understand:
        - "IIT" = Indian Institute of Technology (e.g. IIT Bombay)
        - "NIT" = National Institute of Technology (e.g. NIT Trichy)
        - "IIIT" = Indian Institute of Information Technology (not same as IIT)

        Based on this student question, extract the following fields:
        - Closing Rank (numeric)
        - Round (1-5)
        - Category (OPEN, OBC, SC, etc.)
        - Branch (text)
        - Institute (text)
        - Year (numeric)

        Respond ONLY with raw JSON (no markdown/code blocks).

        Question: {st.session_state['last_question']}
        """

        response = model.generate_content(prompt)
        output = response.text
        clean_output = re.sub(r"```json|```", "", output).strip()

        extracted = json.loads(clean_output)
        #st.success("✅ Parsed Filters:")
        #st.json(extracted)

        # Filter data
        extracted = {k.lower(): v for k, v in extracted.items()}
        matches = cutoffs.copy()

        year = 2024;

        if "closing rank" in extracted and isinstance(extracted["closing rank"], int):
            matches = matches[matches["Closing Rank"] >= extracted["closing rank"]]

        if "round" in extracted and isinstance(extracted["round"], int):
            matches = matches[matches["Round"] == extracted["round"]]

        if "year" in extracted and isinstance(extracted["year"], int):
            year = extracted["year"]
        matches = matches[matches["Year"] == year]

        if "category" in extracted and isinstance(extracted["category"], str):
            cat_filter = extracted["category"]
            cat_filter = cat_filter.replace("General", "OPEN")
            cat_filter = cat_filter.replace("GEN", "OPEN")
            #st.text("Category Name:")
            #st.text(cat_filter)
            matches = matches[matches["Category"].str.upper() == extracted["category"].upper()]
        else:
            matches = matches[matches["Category"].str.upper() == "OPEN"]


        if "branch" in extracted and isinstance(extracted["branch"], str):
            branch_filter = extracted["branch"]
            branch_filter_normalized = branch_filter.strip().lower()
            # Replace if found in map
            if branch_filter_normalized in branch_map:
                branch_filter = branch_map[branch_filter_normalized]
            else:
                branch_filter = branch_filter_normalized
            #st.text("Expanded Branch Name:")
            #st.text(branch_filter)
            matches = matches[matches["Branch"].str.contains(branch_filter, case=False, na=False)]

        if "institute" in extracted and isinstance(extracted["institute"], str):
            inst_filter = extracted["institute"]
            inst_filter_normalized = inst_filter.strip().lower()
            # Replace if found in map
            if inst_filter_normalized in institute_map:
                inst_filter = institute_map[inst_filter_normalized]
            else:
                inst_filter = inst_filter_normalized
            #st.text("Expanded Institute Name:")
            #st.text(inst_filter)
            matches = matches[matches["Institute"].str.contains(inst_filter, case=False, na=False)]

        matches_unique = matches.drop_duplicates(subset=['Institute', 'Branch', 'Category'])

        if not matches_unique.empty:
            st.success(f"🎓 Found {len(matches_unique)} matching options based on cutoffs in " + str(year))
            display_data = matches_unique[['Closing Rank', 'Institute', 'Branch', 'Category', 'Round']].sort_values(by='Closing Rank')
            display_data = display_data.reset_index(drop=True)
            st.dataframe(display_data.style.hide(axis='index'), use_container_width=True)
        else:
            st.warning("No matches found. Try refining your question.")

    except json.JSONDecodeError as e:
        st.error(f"❌ JSON Parse Error: {e}")
        st.text("Raw model output:")
        st.text(output)

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

    # Reset trigger
    st.session_state["run_query"] = False


st.markdown("---")  # Horizontal line separator

st.markdown(
    """
    <p style="font-size:12px; color:gray; text-align:left;">
    &copy; 2025 Ritesh Jain. This tool is an open-source initiative to help organize JoSAA 2023, 2024 cutoff data for easier exploration.  
    All data is used as-is and may contain errors. Use this tool at your own risk. The author is not liable for any inaccuracies or decisions based on this data.
    </p>
    """,
    unsafe_allow_html=True,
)

