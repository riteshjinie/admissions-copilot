import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import json
import re
import streamlit.components.v1 as components
#import streamlit_analytics

# --- Configuration ---
st.set_page_config(
    page_title="Engineering Admissions Copilot - JoSAA 2025",
    page_icon="🎓",
    layout="centered"
)

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1rem !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #ADD8E6 !important;
        color: #262730 !important;
        border: 1px solid #your_desired_border_color !important; /* Optional: Add a border */
    }
    </style>
    """,
    unsafe_allow_html=True,
)



#streamlit_analytics.start_tracking()



st.markdown(
    """
        <!-- Global site tag (gtag.js) - Google Analytics -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-8SFFPX2S46"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-8SFFPX2S46');
        </script>
    """, unsafe_allow_html=True)

##components.html(
##    f"""
##    <script async src="https://www.googletagmanager.com/gtag/js?id=G-8SFFPX2S46"></script>
##    <script>
##      window.dataLayer = window.dataLayer || [];
##      function gtag(){{dataLayer.push(arguments);}}
##      gtag('js', new Date());
##
##      gtag('config', 'G-8SFFPX2S46');
##      gtag('event', 'page_view', {{
##        'page_title': document.title,
##        'page_location': window.location.href
##      }});
##    </script>
##    """,
##    height=0,
##)
   
# --- Data Loading and Initialization ---
@st.cache_data
def load_data():
    cutoffs = pd.read_csv("cutoffs2023-2025.csv")
    return cutoffs

cutoffs = load_data()

institutes = sorted(cutoffs['Institute'].dropna().unique())
branches = sorted(cutoffs['Branch'].dropna().unique())
genders = sorted(cutoffs['Gender'].dropna().unique())
years = sorted(cutoffs['Year'].dropna().unique())
rounds = sorted(cutoffs['Round'].dropna().unique())

# --- Mapping Dictionaries ---
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

state_nit_map = {
    "Karnataka": ["National Institute of Technology Karnataka, Surathkal"],
    "Telangana": ["National Institute of Technology, Warangal"],
    "Kerala": ["National Institute of Technology Calicut"],
    "Jharkhand": ["National Institute of Technology, Jamshedpur", "Birla Institute of Technology, Mesra, Ranchi", "Birla Institute of Technology, Deoghar Off-Campus"],
    "Tamil Nadu": ["National Institute of Technology, Tiruchirappalli"],
    "Uttar Pradesh": ["Motilal Nehru National Institute of Technology Allahabad"],
    "West Bengal": ["Indian Institute of Engineering Science and Technology, Shibpur", "National Institute of Technology Durgapur", "Ghani Khan Choudhury Institute of Engineering and Technology, Malda, West Bengal"],
    "Odisha": ["National Institute of Technology, Rourkela", "Institute of Chemical Technology, Mumbai: Indian Oil Odisha Campus, Bhubaneswar"],
    "Rajasthan": ["Malaviya National Institute of Technology Jaipur"],
    "Meghalaya": ["National Institute of Technology Meghalaya"],
    "Maharashtra": ["Visvesvaraya National Institute of Technology, Nagpur"],
    "Chhattisgarh": ["National Institute of Technology Raipur"],
    "Andhra Pradesh": ["National Institute of Technology, Andhra Pradesh"],
    "Haryana": ["National Institute of Technology, Kurukshetra"],
    "Bihar": ["National Institute of Technology Patna", "Birla Institute of Technology, Patna Off-Campus"],
    "Madhya Pradesh": ["Maulana Azad National Institute of Technology Bhopal"],
    "Jammu and Kashmir": ["National Institute of Technology, Srinagar"],
    "Himachal Pradesh": ["National Institute of Technology Hamirpur"],
    "Chandigarh": ["Punjab Engineering College, Chandigarh"],
    "Delhi": ["National Institute of Technology Delhi"],
    "Gujarat": ["Sardar Vallabhbhai National Institute of Technology, Surat"],
    "Punjab": ["Dr. B R Ambedkar National Institute of Technology, Jalandhar"],
    "Assam": ["National Institute of Technology, Silchar", "Assam University, Silchar"],
    "Uttarakhand": ["National Institute of Technology, Uttarakhand"],
    "Tripura": ["National Institute of Technology Agartala"],
    "Puducherry": ["National Institute of Technology Puducherry", "Puducherry Technological University, Puducherry"],
    "Goa": ["National Institute of Technology Goa"],
    "Manipur": ["National Institute of Technology, Manipur"],
    "Arunachal Pradesh": ["National Institute of Technology Arunachal Pradesh"],
    "Nagaland": ["National Institute of Technology Nagaland"],
    "Sikkim": ["National Institute of Technology Sikkim"],
    "Mizoram": ["National Institute of Technology, Mizoram"],
}

# Create a sorted list of states for the dropdown
states = sorted(state_nit_map.keys())

# --- Filtering Function ---
def filter_cutoff_data(df, rank, use_range=False, rank_range=0, category=None, gender=None, year=None, round_selected="ANY", selected_institute="All", branch_query="", state="Select State"):
    matches = df.copy()

##    st.write("--- Debugging Filter Parameters in filter function ---")
##    st.write(f"Rank: {rank}")
##    st.write(f"Round: {round_selected}")
##    st.write(f"Category: {category}")
##    st.write(f"Branch: {branch_query}")
##    st.write(f"Institute: {selected_institute}")
##    st.write(f"Year: {year}")
##    st.write(f"State: {state}")
##    st.write("--- End Debugging ---")

    if use_range:
        lower_bound = rank - rank_range
        upper_bound = rank + rank_range
        matches = matches[(matches['Closing Rank'] >= lower_bound) & (matches['Closing Rank'] <= upper_bound)]
    else:
        matches = matches[matches['Closing Rank'] >= rank]

    if category and category != "All":
        matches = matches[matches['Category'].str.lower() == category.lower()]
    if gender and gender != "All":
        matches = matches[matches['Gender'].str.lower() == gender.lower()]
    if year:
        matches = matches[matches['Year'] == year]
    if round_selected != "ANY":
        matches = matches[matches['Round'] == round_selected]


    selected_institutes = [inst.strip().lower() for inst in selected_institute]

    if "all" in selected_institutes:
        pass  # If "All" is selected, no institute filtering is needed
    else:
        institute_filter = pd.Series([False] * len(matches), index=matches.index)
        for index, row in matches.iterrows():
            institute_name_lower = row['Institute'].strip().lower()
            match = False
            for selected_inst in selected_institutes:
                if selected_inst == "all iits" and "indian institute of technology" in institute_name_lower:
                    match = True
                    break
                elif selected_inst == "all nits" and "national institute of technology" in institute_name_lower:
                    match = True
                    break
                elif selected_inst == "all except iits" and "indian institute of technology" not in institute_name_lower:
                    match = True
                    break
                elif selected_inst in institute_map and institute_map[selected_inst].lower() in institute_name_lower:
                    match = True
                    break
                elif selected_inst == institute_name_lower:
                    match = True
                    break
            if match:
                institute_filter.at[index] = True
        matches = matches[institute_filter]


##    selected_institute_normalized = selected_institute.strip().lower()
##    if selected_institute_normalized == "all except iits":
##        matches = matches[~matches['Institute'].str.lower().str.contains("indian institute of technology", regex=False)]
##    elif selected_institute_normalized == "all nits":
##        matches = matches[matches['Institute'].str.lower().str.contains("national institute of technology", regex=False)]
##    elif selected_institute_normalized != "all":
##        if selected_institute_normalized in institute_map:
##            selected_institute = institute_map[selected_institute_normalized]
##        else:
##            selected_institute = selected_institute_normalized
##        matches = matches[matches['Institute'].str.lower().str.contains(selected_institute.lower(), regex=False)]

    if state != "Select State":
        home_colleges = state_nit_map.get(state, [])
        #print(f"Debug: Home Colleges for {state}: {home_colleges}") # Print the list of home colleges

        def filter_by_state(row):
            institute_lower = row['Institute'].lower()
            if institute_lower in [hc.lower() for hc in home_colleges]:
                #print(f"Debug: Institute '{row['Institute']}' is a home college, checking for HS = {(row['Quota'] == 'HS')}")
                return row['Quota'] == 'HS'
            else:
                #print(f"Debug: Institute '{row['Institute']}' is not a home state college for '{state}', not filtering by quota.")
                return True # Do not filter if not a home state college

        matches = matches[matches.apply(filter_by_state, axis=1)]
    #else:
    #    st.warning(f"⚠️ College mapping not found for the state: {state}")

    if branch_query.strip() != "":
        branch_keywords = [kw.strip().lower() for kw in branch_query.split(",") if kw.strip()]
        branch_keywords = [branch_map.get(kw, kw) for kw in branch_keywords]
        include_architecture = any("arch" in kw for kw in branch_keywords)
        include_planning = any("plan" in kw for kw in branch_keywords)
        if not include_architecture:
            matches = matches[~matches['Branch'].str.lower().str.contains("architecture|arch", regex=True)]
        if not include_planning:
            matches = matches[~matches['Branch'].str.lower().str.contains("planning|plan", regex=True)]
        pattern = '|'.join(branch_keywords)
        matches = matches[matches['Branch'].str.lower().str.contains(pattern)]
    else:
        matches = matches[~matches['Branch'].str.lower().str.contains("architecture|arch|planning|plan", regex=True)]

    # Sort the DataFrame by 'Closing Rank' in descending order
    matches_sorted = matches.sort_values(by='Closing Rank', ascending=False)

    # Drop duplicates based on 'Institute', 'Branch', and 'Category', keeping the first occurrence
    # (which now has the highest Closing Rank due to the sorting)
    matches_unique_highest_rank = matches_sorted.drop_duplicates(subset=['Institute', 'Branch', 'Category'], keep='first')

    return matches_unique_highest_rank[['Closing Rank', 'Round', 'NIRF', 'Institute', 'Branch']].sort_values(by='Closing Rank').reset_index(drop=True)

# --- Main Streamlit UI ---
st.subheader("🎓 Engineering Admissions Copilot for JEE 2025")

st.markdown(
    """
    <p style="font-size:16px; color:gray; text-align:left;">
    This tool is an open-source initiative to help you prepare for JoSAA 2025 counselling using JEE 2023, 2024 cutoff data (*added 2025 rounds 1 and 2 data also).
    All data is fetched from the official JoSAA website and used as-is. Use this tool at your own risk. The author is not liable for any inaccuracies or decisions based on this data.
    </p>
    """,
    unsafe_allow_html=True,
)

# --- Structured Input Form ---
exam_type = st.radio("Which exam rank are you using?", ["JEE Mains", "JEE Advanced"])
crl = st.number_input("Enter your rank from " + exam_type, min_value=1, value=1000)
use_range = st.checkbox("Search within ± range of the above rank?")
rank_range_input = st.number_input("Enter range value", min_value=1, max_value=1000, value=200) if use_range else 0

with st.form("form"):
    category_form = st.selectbox("Select your Category for JEE", sorted(cutoffs['Category'].dropna().unique()), index=4)
    gender_form = st.selectbox("Select your Gender", genders, index=1)
    state_form = st.selectbox("Select the State where you gave your XII boards (for NITs and other colleges with Home State quota)", ["Select State"] + states)
    year_form = st.selectbox("Select the Year from where to use the cutoff data", years, index=len(years)-1)
    round_selected_form = st.selectbox("Select a particular JoSAA counselling Round", ["ANY"] + rounds, index=0)

    if exam_type == "JEE Advanced":
        allowed_institutes_form = sorted([i for i in institutes if i.startswith("Indian Institute of Technology")])
        selected_institute_form = st.multiselect("For JEE Advanced, filter by IITs (select multiple if needed):", ["All IITs", "All"] + allowed_institutes_form, default=["All IITs"])
    else:
        allowed_institutes_form = sorted([i for i in institutes if not i.startswith("Indian Institute of Technology")])
        selected_institute_form = st.multiselect("For JEE Mains, filter by NITs and other colleges (select multiple if needed):", ["All except IITs", "All NITs", "All"] + allowed_institutes_form, default=["All except IITs"])

##    if exam_type == "JEE Advanced":
##        allowed_institutes_form = sorted([i for i in institutes if i.startswith("Indian Institute of Technology")])
##        selected_institute_form = st.selectbox("Do you want to filter by Institute?", ["All IITs", "All"] + allowed_institutes_form)
##    else:
##        allowed_institutes_form = sorted([i for i in institutes if not i.startswith("Indian Institute of Technology")])
##        selected_institute_form = st.selectbox("Do you want to filter by Institute?", ["All except IITs", "All NITs", "All"] + allowed_institutes_form)

    branch_query_form = st.text_input("Do you want to filter by Branch? (for example: cs, ece, electrical, civil)", "")
    submit_button = st.form_submit_button("Find Colleges")

if submit_button:
    results_df = filter_cutoff_data(
        cutoffs,
        crl,
        use_range,
        rank_range_input,
        category_form,
        gender_form,
        year_form,
        round_selected_form,
        selected_institute_form,
        branch_query_form,
        state_form
    )
    if results_df.empty:
        st.warning("⚠️ Sorry, no colleges found for your profile.")
    else:
        st.success(f"🎯 Found {len(results_df)} possible options based on cutoffs in " + str(year_form))
        st.dataframe(results_df.style.hide(axis='index'), use_container_width=True)

st.divider()
st.markdown(
    """
    <div style="text-align: center;">
        ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨
    </div>
    """,
    unsafe_allow_html=True,
)
st.divider()

# --- Gemini Assistant ---
st.subheader("🤖 Ask Admissions Copilot")

st.markdown(
    """
    <p style="font-size:16px; color:gray; text-align:left;">
    This section is an attempt to understand your filtering options using GenAI and provide you with a list of matching colleges.
    At the moment, the tool can understand simple queries with one branch, one college type and a rank.
    A few sample queries are given below. Feel free to modify them as per your need.
    </p>
    """,
    unsafe_allow_html=True,
)

sample_questions = [
    "What NITs can I get with a rank of 10000 for Computer Science?",
    "Show me the IITs I might get with a rank around 8000.",
    "What are the options for rank 4000 for aerospace in the 2023 cutoffs?",
    "Can I get Mechanical in NIT with 12000 rank?",
    "What branches were available in NITs above 6000 CRL for Haryana domicile?",
    "Can I get anything at rank 80000?",
]

def update_custom_question():
    st.session_state["custom_question"] = st.session_state["selected_example"]

selected_example = st.selectbox("💡 You can choose a sample question from this list:", [""] + sample_questions, key="selected_example", on_change=update_custom_question)
custom_question = st.text_area("💡 Or type your own question below. You can also modify a sample question here", key="custom_question")

# The final question is always from the custom text area
final_question = st.session_state.get("custom_question", "")

def run_gemini_query():
    if final_question:
        st.session_state["last_question"] = final_question
        st.session_state["run_query"] = True

ask_button = st.button("Ask", on_click=run_gemini_query)

if st.session_state.get("run_query", False) and st.session_state.get("last_question", "").strip():
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = f"""
        You are an expert Indian college admission counselor, helping students with JoSAA admissions.

        When asked a question about college admissions, you need to identify and extract specific information. If a piece of information is NOT explicitly mentioned in the question, you should use a sensible default value.

        Here's the information you need to extract:
        - Closing Rank: Extract the numerical rank mentioned. If not mentioned, do not invent one.
        - Round: Extract the round number (1 to 6) if mentioned. If not mentioned, the value should be NULL.
        - Category: Extract the admission category (e.g., OPEN, OBC-NCL, SC, ST, EWS) if mentioned. If the category is NOT mentioned in the question, the DEFAULT value MUST be "OPEN".
        - Branch: Extract the engineering branch (e.g., computer science, electronics and communication) if mentioned. If not mentioned, the value should be NULL.
        - Institute Type: Identify the type of institute (e.g., IIT, NIT, IIIT) if mentioned. If a specific institute name is given, try to categorize it. If the type is not clear, the value should be NULL.
        - Year: Extract the admission year if mentioned. If not mentioned, the DEFAULT value MUST be 2024.
        - State: Extract the domicile state if mentioned. If not mentioned, the value should be NULL.

        Your response MUST be a raw JSON object containing these fields as keys. Do not include any explanations or markdown.

        Example Question: What NITs can I get with 15000 rank for ECE in round 1?
        Expected JSON Response:
        {{
          "Closing Rank": 15000,
          "Round": 1,
          "Category": "OPEN",
          "Branch": "electronics and communication",
          "Institute Type": "nit",
          "Year": 2024,
          "State": null
        }}

        Now, process the following question and respond ONLY with the raw JSON:

        Question: {st.session_state['last_question']}
        """
        response = model.generate_content(prompt)
        output = response.text
        clean_output = re.sub(r"```json|```", "", output).strip()
        extracted = json.loads(clean_output)
##        st.json(extracted) # For debugging the extracted output

        # Convert keys to lowercase for case-insensitive access
        extracted_lower = {k.lower(): v for k, v in extracted.items()}

        # Prepare arguments for the filtering function
        rank_gemini = extracted_lower.get("closing rank")
        round_gemini = extracted_lower.get("round")
        category_gemini = extracted_lower.get("category")
        branch_gemini = extracted_lower.get("branch")
        institute_type_gemini = extracted_lower.get("institute type")
        year_gemini = extracted_lower.get("year") if extracted_lower.get("year") else 2024
        state_gemini = extracted_lower.get("state") if extracted_lower.get("state") else "Select State"

##        st.write("--- Debugging Filter Parameters ---")
##        st.write(f"Rank: {rank_gemini}")
##        st.write(f"Round: {round_gemini}")
##        st.write(f"Category: {category_gemini}")
##        st.write(f"Branch: {branch_gemini}")
##        st.write(f"Institute: {institute_type_gemini if institute_type_gemini else 'ALL'}")
##        st.write(f"Year: {year_gemini}")
##        st.write(f"State: {state_gemini}")
##        st.write("--- End Debugging ---")

        if rank_gemini is not None:
            institute_list_gemini = []
            if institute_type_gemini:
                if institute_type_gemini.lower() == "iit":
                    institute_list_gemini = ["All IITs"]
                elif institute_type_gemini.lower() == "nit":
                    institute_list_gemini = ["All NITs"]
                else:
                    # If a specific institute name was extracted, add it as a list
                    institute_list_gemini = [institute_type_gemini]
            else:
                institute_list_gemini = ["All"] # Default if no institute type is mentioned

            results_gemini_df = filter_cutoff_data(
                cutoffs,
                rank_gemini,
                False, # use_range is always False for direct query
                0,
                category_gemini if category_gemini else "OPEN", # Default category
                "Gender-Neutral", # Gender is not typically asked
                year_gemini,
                round_gemini if round_gemini is not None else "ANY", # Handle potential None for round
                institute_list_gemini, # Pass the list of institutes
                branch_gemini if branch_gemini else "", # Default for branch
                state_gemini # State has a default of "Select State" already
            )

            if not results_gemini_df.empty:
                st.success(f"🤖 found {len(results_gemini_df)} matching options based on cutoffs in {year_gemini}")
                st.dataframe(results_gemini_df.style.hide(axis='index'), use_container_width=True)
            else:
                st.warning("🤖 couldn't find any matching options based on the query.")
        else:
            st.warning("🤖 could not extract a valid rank from your query. Please ensure you have mentioned your rank.")

    except json.JSONDecodeError as e:
        st.error(f"❌ JSON Parse Error: {e}")
        st.text("Raw model output:")
        st.text(output)

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

    # Reset trigger AFTER processing the query
    st.session_state["run_query"] = False

# Initialize run_query and last_question in session state if they don't exist
if "run_query" not in st.session_state:
    st.session_state["run_query"] = False
if "last_question" not in st.session_state:
    st.session_state["last_question"] = ""
if "custom_question" not in st.session_state:
    st.session_state["custom_question"] = ""
if "selected_example" not in st.session_state:
    st.session_state["selected_example"] = ""


st.markdown("---")  # Horizontal line separator

st.markdown(
    """
    <p style="font-size:12px; color:gray; text-align:left;">
    &copy; 2025 Ritesh Jain. This tool is an open-source initiative to help you prepare for JoSAA 2025 counselling using JEE 2023, 2024 cutoff data (*added 2025 rounds 1 and 2 data also).
    All data is fetched from the official JoSAA website and used as-is. Use this tool at your own risk. The author is not liable for any inaccuracies or decisions based on this data.
    </p>
    """,
    unsafe_allow_html=True,
)

#streamlit_analytics.stop_tracking()
