import streamlit as st
from datetime import datetime, timedelta, date 
from collections import defaultdict
import requests


st.markdown('''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=Poppins:wght@600&display=swap');
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css');
    html, body, [class*="css"]  {
        font-family: 'Inter', 'Poppins', sans-serif !important;
        background: linear-gradient(135deg, #232526 0%, #414345 100%) !important;
        color: #f3f3f3 !important;
    }
    .main {
        background: rgba(30, 32, 38, 0.7) !important;
        border-radius: 24px;
        padding: 2.5rem 2rem 2rem 2rem;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid rgba(255,255,255,0.18);
        margin-top: 2rem;
    }
    .metric-card {
        background: rgba(255,255,255,0.08);
        border-radius: 18px;
        box-shadow: 0 4px 24px 0 rgba(31, 38, 135, 0.17);
        padding: 1.5rem;
        text-align: center;
        margin-bottom: 1rem;
        transition: transform 0.2s, box-shadow 0.2s;
        border: 1px solid rgba(255,255,255,0.10);
    }
    .metric-card:hover {
        transform: translateY(-6px) scale(1.03);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.27);
        background: rgba(255,255,255,0.13);
    }
    .metric-card h4 {
        font-family: 'Poppins', sans-serif;
        font-size: 1.1rem;
        color: #fda085;
        margin-bottom: 0.5rem;
    }
    .metric-card h2 {
        font-size: 2.2rem;
        color: #fff;
        margin: 0;
    }
    .fa-icon {
        font-size: 2.1rem;
        margin-bottom: 0.3rem;
        color: #f6d365;
        filter: drop-shadow(0 2px 8px #fda08533);
    }
    .stTabs [data-baseweb="tab-list"] {justify-content: center;}
    .stTabs [data-baseweb="tab"] {font-size: 1.1rem; font-weight: 600; color: #fda085;}
    .stTabs [data-baseweb="tab"]:hover {color: #f6d365;}
    .stDataFrame {border-radius: 16px; overflow: hidden; background: rgba(255,255,255,0.04);}
    .stForm {background: rgba(255,255,255,0.06); border-radius: 16px; padding: 1.5rem;}
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stDateInput>div>div>input, .stSelectbox>div>div {
        background: rgba(255,255,255,0.10) !important;
        color: #fff !important;
        border-radius: 8px !important;
        border: 1px solid #fda08533 !important;
    }
    .stSelectbox>div>div>div { /* Targeting the inner div for selectbox text color */
        color: #fff !important;
    }
    .stButton>button {
        background: linear-gradient(90deg, #f6d365 0%, #fda085 100%) !important;
        color: #232526 !important;
        border-radius: 8px !important;
        font-weight: 600;
        border: none;
        box-shadow: 0 2px 8px #fda08533;
        transition: background 0.2s;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #fda085 0%, #f6d365 100%) !important;
        color: #232526 !important;
    }
    .stAlert, .stInfo, .stWarning, .stError { /* General alert styling */
        border-radius: 12px !important;
        background: rgba(253,160,133,0.08) !important; /* Default to a warning-like background */
        color: #fff !important; /* Default text color */
        padding: 1rem !important;
    }
    .stError { /* Specific error styling */
        background: rgba(255, 77, 77, 0.15) !important; /* More reddish background for errors */
        border: 1px solid rgba(255, 77, 77, 0.5) !important;
    }
    .stSuccess { /* Specific success styling */
         background: rgba(77, 255, 150, 0.15) !important;
         border: 1px solid rgba(77, 255, 150, 0.5) !important;
    }

    </style>
''', unsafe_allow_html=True)

# --- API Endpoints ---
API_URL = "http://localhost:8000"  

# --- Data Models ---
class PolicyholderRep: 
    def __init__(self, id, name, age, policy_type, sum_insured):
        self.id = id
        self.name = name
        self.age = age
        self.policy_type = policy_type
        self.sum_insured = sum_insured

class ClaimRep: 
    def __init__(self, id, policyholder_id, amount, reason, status, date_of_claim):
        self.id = id
        self.policyholder_id = policyholder_id
        self.amount = amount
        self.reason = reason
        self.status = status
        if isinstance(date_of_claim, str):
            self.date_of_claim = datetime.fromisoformat(date_of_claim).date() #
        elif isinstance(date_of_claim, datetime):
            self.date_of_claim = date_of_claim.date()
        else: # Assumed to be datetime.date
            self.date_of_claim = date_of_claim


# --- Validation Functions ---
def validate_policyholder(name, age, policy_type, sum_insured):
    errors = []
    if not name.strip():
        errors.append("Name cannot be empty.")
    if not isinstance(age, int) or age < 0 or age > 120 : 
        errors.append("Age must be a valid number (0-120).")
    if policy_type not in ["Health", "Vehicle", "Life"]: 
        errors.append("Invalid policy type selected.")
    if not isinstance(sum_insured, (int, float)) or sum_insured <= 0:
        errors.append("Sum insured must be a positive number.")
    
    if errors:
        for error in errors:
            st.error(error) 
        return False
    return True

def validate_claim(policyholder_id_to_check, amount, reason, status, date_of_claim_obj, current_policyholders_list):
    errors = []
    valid_ph_ids = [ph['id'] for ph in current_policyholders_list]
    if policyholder_id_to_check not in valid_ph_ids:
        errors.append(f"Invalid Policyholder ID: {policyholder_id_to_check}. Valid IDs are: {valid_ph_ids}")
    
    if not (isinstance(amount, (int,float)) and amount > 0):
        errors.append("Claim amount must be a positive number.")
    
    if not reason or not reason.strip():
        errors.append("Reason cannot be empty.")
        
    if status not in ["Pending", "Approved", "Rejected"]: 
        errors.append("Invalid claim status.")
        
    if not isinstance(date_of_claim_obj, date): 
         errors.append("Invalid date format for date of claim.")
    else:
        try:
            datetime.combine(date_of_claim_obj, datetime.min.time())
        except Exception:
            errors.append("Invalid date of claim.")

    if errors:
        for error in errors:
            st.error(error) 
        return False
    return True

# --- Fetch initial data ---
def fetch_data(endpoint):
    try:
        response = requests.get(f"{API_URL}/{endpoint}/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error fetching {endpoint}: {e}")
        return []
    except Exception as e: # Catch other potential errors like JSON decoding
        st.error(f"Error processing data for {endpoint}: {e}")
        return []

policyholders_global = fetch_data("policyholders")
claims_global = fetch_data("claims")

st.markdown("<div class='main'>", unsafe_allow_html=True)
st.title("💰 ABC Insurance: Claims & Risk Portal")
tabs = st.tabs(["Dashboard", "Policyholders", "Claims", "Risk Analysis", "Reports"])

# --- Dashboard ---
with tabs[0]:
    st.markdown("<h2 style='text-align:center; font-family:Poppins,sans-serif;'>Dashboard Overview</h2>", unsafe_allow_html=True)
    pending_count = sum(1 for c in claims_global if c.get('status') == 'Pending')
    approved_count = sum(1 for c in claims_global if c.get('status') == 'Approved')
    rejected_count = sum(1 for c in claims_global if c.get('status') == 'Rejected')

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='fa-icon'><i class='fa-solid fa-users'></i></div>
            <h4>Policyholders</h4><h2>{len(policyholders_global)}</h2>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='fa-icon'><i class='fa-solid fa-file-invoice-dollar'></i></div>
            <h4>Claims</h4><h2>{len(claims_global)}</h2>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='fa-icon'><i class='fa-solid fa-hourglass-half'></i></div>
            <h4>Pending</h4><h2>{pending_count}</h2>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='fa-icon'><i class='fa-solid fa-circle-check'></i></div>
            <h4>Approved</h4><h2>{approved_count}</h2>
        </div>""", unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='fa-icon'><i class='fa-solid fa-circle-xmark'></i></div>
            <h4>Rejected</h4><h2>{rejected_count}</h2>
        </div>""", unsafe_allow_html=True)
    st.info("Navigate using the tabs above to manage policyholders, claims, and view analytics.")

# --- Policyholders ---
with tabs[1]:
    st.markdown("<h2>Policyholder Management</h2>", unsafe_allow_html=True)
    with st.form("add_policyholder"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name")
            age_input = st.number_input("Age", min_value=0, max_value=120, step=1, value=30) 
        with col2:
            policy_type = st.selectbox("Policy Type", ["Health", "Vehicle", "Life"])
            sum_insured_input = st.number_input("Sum Insured", min_value=0.0, step=1000.0, value=10000.0) 
        
        submitted_ph = st.form_submit_button("Register Policyholder")
        
        if submitted_ph:
            
            try:
                age = int(age_input)
                sum_insured = float(sum_insured_input)
                if validate_policyholder(name, age, policy_type, sum_insured):
                    ph_data = {
                        "name": name, "age": age, "policy_type": policy_type, "sum_insured": sum_insured
                    }
                    response = requests.post(f"{API_URL}/policyholders/", json=ph_data)
                    if response.status_code == 201:
                        st.success(f"✅ Policyholder '{name}' registered successfully!")
                        policyholders_global = fetch_data("policyholders") # Refresh global list
                        st.rerun() # Rerun to update the UI, especially the table
                    else:
                        st.error(f"❌ Error registering policyholder: {response.text} (Status: {response.status_code})")
                # else: validate_policyholder already showed st.error messages
            except ValueError:
                st.error("Invalid input for Age or Sum Insured. Please enter valid numbers.")
            except requests.exceptions.RequestException as e:
                st.error(f"API connection error: {e}")

    st.markdown("<h4>Registered Policyholders</h4>", unsafe_allow_html=True)
    if policyholders_global:
        st.dataframe([
            {"ID": ph.get('id'), "Name": ph.get('name'), "Age": ph.get('age'),
             "Policy Type": ph.get('policy_type'), "Sum Insured": ph.get('sum_insured')}
            for ph in policyholders_global
        ], use_container_width=True)
    else:
        st.info("No policyholders registered yet or failed to fetch data.")

# --- Claims ---
with tabs[2]:
    st.markdown("<h2>Claim Management</h2>", unsafe_allow_html=True)
    
    policyholders_for_claim_form = fetch_data("policyholders")

    if not policyholders_for_claim_form:
        st.warning("No policyholders available to file a claim. Please register a policyholder first.")
    else:
        with st.form("add_claim"):
            col1, col2 = st.columns(2)
            with col1:
                ph_options_dict = {ph['id']: f"{ph['name']} (ID: {ph['id']})" for ph in policyholders_for_claim_form}
                selected_policyholder_id = st.selectbox(
                    "Policyholder",
                    options=list(ph_options_dict.keys()), 
                    format_func=lambda ph_id: ph_options_dict[ph_id] 
                )
                amount_input = st.number_input("Claim Amount", min_value=0.01, step=100.0, value=1000.0) 
            with col2:
                reason_input = st.text_input("Reason for Claim")
                status_input = st.selectbox("Claim Status", ["Pending", "Approved", "Rejected"])
                date_of_claim_input = st.date_input("Date of Claim", value=date.today()) 

            submitted_claim = st.form_submit_button("Add Claim")

            if submitted_claim:
                try:
                    amount = float(amount_input) 
                    reason = reason_input
                    status = status_input
                    
                    if validate_claim(selected_policyholder_id, amount, reason, status, date_of_claim_input, policyholders_for_claim_form):
                        claim_data = {
                            "policyholder_id": selected_policyholder_id,
                            "amount": amount,
                            "reason": reason,
                            "status": status,
                            "date_of_claim": date_of_claim_input.isoformat() 
                        }
                        response = requests.post(f"{API_URL}/claims/", json=claim_data)
                        if response.status_code == 201:
                            st.success(f"✅ Claim added successfully for policyholder ID {selected_policyholder_id}!")
                            claims_global = fetch_data("claims") # Refresh global claims
                            st.rerun() # Rerun to update UI
                        else:
                            st.error(f"❌ Error adding claim: {response.text} (Status: {response.status_code})")
                except ValueError:
                    st.error("Invalid input for Amount. Please enter a valid number.")
                except requests.exceptions.RequestException as e:
                    st.error(f"API connection error: {e}")
    
    st.markdown("<h4>All Claims</h4>", unsafe_allow_html=True)
    claims_to_display = fetch_data("claims") 
    if claims_to_display:
        ph_names_map = {ph['id']: ph['name'] for ph in policyholders_global}
        
        claims_df_data = []
        for cl in claims_to_display:
            claims_df_data.append({
                "ID": cl.get('id'),
                "Policyholder": ph_names_map.get(cl.get('policyholder_id'), f"Unknown (ID: {cl.get('policyholder_id')})"),
                "Amount": cl.get('amount'),
                "Reason": cl.get('reason'),
                "Status": cl.get('status'),
                "Date": cl.get('date_of_claim')
            })
        st.dataframe(claims_df_data, use_container_width=True)
    else:
        st.info("No claims added yet or failed to fetch data.")


# --- Risk Analysis ---
with tabs[3]:
    st.markdown("<h2>Risk Analysis</h2>", unsafe_allow_html=True)
    try:
        response = requests.get(f"{API_URL}/risk_analysis/")
        response.raise_for_status()
        analysis_data = response.json()

        risk_report_df_data = []
        if "risk_analysis_report" in analysis_data:
            for report_item in analysis_data["risk_analysis_report"]:
                risk_report_df_data.append({
                    "Policyholder ID": report_item.get("policyholder_id", "N/A"),
                    "Name": report_item.get("name", "N/A"),
                    "Risk Status": report_item.get("risk_status_message", "Error processing"),
                    "Is High Risk": "Yes" if report_item.get("high_risk") else "No",
                    "Reason/Details": report_item.get("reason", "N/A")
                })
        
        if risk_report_df_data:
            st.markdown("<h4>Policyholder Risk Assessment</h4>", unsafe_allow_html=True)
            st.dataframe(risk_report_df_data, use_container_width=True)
        else:
            st.info("No risk analysis data available or could not be processed.")

        # Corrected section for Approved Claims by Policy Type
        st.markdown("<h4>Approved Claims by Policy Type (Overall)</h4>", unsafe_allow_html=True)
        if "claims_by_policy_type_approved" in analysis_data and analysis_data["claims_by_policy_type_approved"]: 
            approved_claims_by_type = analysis_data["claims_by_policy_type_approved"] 
            if approved_claims_by_type:
                 st.bar_chart(approved_claims_by_type)
            else:
                 st.info("No approved claims data to display by policy type.")
        else:
            # MODIFIED TEXT
            st.info("Data for 'Approved Claims by Policy Type' not found in API response or no approved claims.")

        # NEW: Section for Total Claims by Policy Type
        st.markdown("<h4>Total Claims by Policy Type (Overall)</h4>", unsafe_allow_html=True)
        if "total_claims_by_policy_type" in analysis_data and analysis_data["total_claims_by_policy_type"]:
            all_claims_by_type_data = analysis_data["total_claims_by_policy_type"]
            if all_claims_by_type_data: # Check if dictionary is not empty
                 st.bar_chart(all_claims_by_type_data)
            else:
                 st.info("No claims data to display by policy type (overall).")
        else:
            st.info("Data for 'Total Claims by Policy Type' not found in API response or no claims exist.")
            
        if "high_risk_summary" in analysis_data and analysis_data["high_risk_summary"]:
            st.markdown("<h4>Summary of High-Risk Policyholders</h4>", unsafe_allow_html=True)
            high_risk_summary_df_data = [
                {
                    "Policyholder ID": hr_item.get("policyholder_id"),
                    "Name": hr_item.get("name"),
                    "Reason for High Risk": hr_item.get("reason_for_high_risk"),
                    "Recent Accepted Claims": hr_item.get("recent_accepted_claims_count", "N/A") 
                } for hr_item in analysis_data["high_risk_summary"]
            ]
            if high_risk_summary_df_data:
                st.table(high_risk_summary_df_data)
            else:
                st.info("No policyholders currently flagged as high risk based on the criteria.")

    except requests.exceptions.RequestException as e:
        st.error(f"API Error: Could not fetch risk analysis data. {e}")
    except Exception as e: # Catch other potential errors like JSON decoding
        st.error(f"An error occurred while processing risk analysis: {e}")


# --- Reports ---
with tabs[4]:
    st.markdown("<h2>Reports</h2>", unsafe_allow_html=True)
    try:
        response = requests.get(f"{API_URL}/reports/")
        response.raise_for_status()
        reports_data = response.json()

        policyholders_rep_list = fetch_data("policyholders") 
        ph_names_map_reports = {ph['id']: ph['name'] for ph in policyholders_rep_list}

        st.markdown("<h4>Total Claims Per Month</h4>", unsafe_allow_html=True)
        if reports_data.get("claims_per_month") and reports_data["claims_per_month"]:
            st.bar_chart(reports_data["claims_per_month"])
        else:
            st.info("No monthly claim data to report.")

        st.markdown("<h4>Average Accepted Claim Amount by Policy Type</h4>", unsafe_allow_html=True)
        if reports_data.get("avg_claim_by_type") and reports_data["avg_claim_by_type"]:
            st.bar_chart(reports_data["avg_claim_by_type"]) # This correctly shows average for 'Approved' claims as per API
        else:
            st.info("No average claim amount data to report by policy type.")

        st.markdown("<h4>Highest Claim Filed</h4>", unsafe_allow_html=True)
        highest_claim_info = reports_data.get("highest_claim")
        if highest_claim_info:
            st.write(f"**ID:** {highest_claim_info.get('id')}")
            st.write(f"**Amount:** ₹ {highest_claim_info.get('amount'):,.2f}")
            st.write(f"**Policyholder:** {ph_names_map_reports.get(highest_claim_info.get('policyholder_id'), 'Unknown')}")
        else:
            st.info("No claims filed yet to determine the highest.")

        st.markdown("<h4>Policyholders with Pending Claims</h4>", unsafe_allow_html=True)
        pending_names = reports_data.get("policyholders_with_pending_claims")
        if pending_names:
            st.write(", ".join(pending_names))
        else:
            st.info("No policyholders currently have pending claims.")

    except requests.exceptions.RequestException as e:
        st.error(f"API Error: Could not fetch report data. {e}")
    except Exception as e:
        st.error(f"An error occurred while processing reports: {e}")


st.markdown("</div>", unsafe_allow_html=True)