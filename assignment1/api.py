# api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import oracledb
from datetime import datetime, timedelta, date
from collections import defaultdict

app = FastAPI(
    title="Insurance Claims API",
    description="API for managing insurance policyholders and claims, with risk analysis.",
    version="1.2.1"
)

# --- Oracle DB Configuration ---
DB_USER = "system"
DB_PASSWORD = "shardul"  
DB_DSN = "localhost:1521/FREE"  

# --- Oracle DB Connection ---
def get_connection():
    try:
        conn = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
        return conn
    except oracledb.Error as e:
        print(f"Oracle Connection Error: {e}")
        raise HTTPException(status_code=503, detail="Database connection unavailable.")

# --- Pydantic Models ---
class PolicyholderBase(BaseModel):
    name: str = Field(..., min_length=1, example="John Doe")
    age: int = Field(..., gt=0, le=120, example=35)
    policy_type: str = Field(..., example="Health")
    sum_insured: float = Field(..., gt=0, example=50000.00)

class PolicyholderIn(PolicyholderBase):
    pass

class PolicyholderOut(PolicyholderBase):
    id: int

class ClaimBase(BaseModel):
    policyholder_id: int = Field(..., example=1)
    amount: float = Field(..., gt=0, example=1250.75)
    reason: str = Field(..., min_length=5, example="Routine check-up")
    status: str # Expected: "Pending", "Approved", "Rejected"
    date_of_claim: date

class ClaimIn(ClaimBase):
    pass

class ClaimOut(ClaimBase):
    id: int
    date_of_claim: str 

# --- API Endpoints ---

@app.post("/policyholders/", response_model=PolicyholderOut, status_code=201, tags=["Policyholders"])
def create_policyholder(ph: PolicyholderIn):
    """Registers a new policyholder."""
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        ph_id_var = cur.var(oracledb.NUMBER)
        cur.execute("""
            INSERT INTO policyholders (name, age, policy_type, sum_insured)
            VALUES (:name, :age, :policy_type, :sum_insured)
            RETURNING id INTO :out_id
        """, {
            'name': ph.name, 'age': ph.age, 'policy_type': ph.policy_type,
            'sum_insured': ph.sum_insured, 'out_id': ph_id_var
        })
        ph_id_result = ph_id_var.getvalue()
        if ph_id_result is None or not ph_id_result:
            raise HTTPException(status_code=500, detail="Failed to retrieve policyholder ID after insert.")
        ph_id = ph_id_result[0]
        conn.commit()
        return {**ph.dict(), "id": ph_id}
    except oracledb.DatabaseError as e_db:
        error_obj, = e_db.args
        print(f"Oracle Error creating policyholder: {error_obj.message} (Code: {error_obj.code})")
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error creating policyholder: {error_obj.message}")
    except Exception as e_general:
        print(f"General Error creating policyholder: {str(e_general)}")
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {type(e_general).__name__}")
    finally:
        if cur: cur.close()
        if conn: conn.close()

@app.get("/policyholders/", response_model=List[PolicyholderOut], tags=["Policyholders"])
def list_policyholders():
    """Retrieves a list of all policyholders."""
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, age, policy_type, sum_insured FROM policyholders ORDER BY id")
        rows = cur.fetchall()
        return [
            {"id": r[0], "name": r[1], "age": r[2], "policy_type": r[3], "sum_insured": r[4]}
            for r in rows
        ]
    except oracledb.DatabaseError as e_db:
        error_obj, = e_db.args
        print(f"Oracle Error listing policyholders: {error_obj.message}")
        raise HTTPException(status_code=500, detail=f"Database error listing policyholders: {error_obj.message}")
    except Exception as e_general:
        print(f"General Error listing policyholders: {str(e_general)}")
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {type(e_general).__name__}")
    finally:
        if cur: cur.close()
        if conn: conn.close()

@app.post("/claims/", response_model=ClaimOut, status_code=201, tags=["Claims"])
def create_claim(cl: ClaimIn):
    """Submits a new claim for a policyholder."""
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cl_id_var = cur.var(oracledb.NUMBER)
        cur.execute("""
            INSERT INTO claims (policyholder_id, amount, reason, status, date_of_claim)
            VALUES (:policyholder_id, :amount, :reason, :status, :date_of_claim)
            RETURNING id INTO :out_id
        """, {
            'policyholder_id': cl.policyholder_id, 'amount': cl.amount, 'reason': cl.reason,
            'status': cl.status, 'date_of_claim': cl.date_of_claim,
            'out_id': cl_id_var
        })
        cl_id_result = cl_id_var.getvalue()
        if cl_id_result is None or not cl_id_result:
            raise HTTPException(status_code=500, detail="Failed to retrieve claim ID after insert.")
        cl_id = cl_id_result[0]
        conn.commit()
        return {**cl.dict(), "id": cl_id, "date_of_claim": cl.date_of_claim.isoformat()}
    except oracledb.DatabaseError as e_db:
        error_obj, = e_db.args
        print(f"Oracle Error creating claim: {error_obj.message} (Code: {error_obj.code})")
        if conn: conn.rollback()
        if error_obj.code == 2291:
             raise HTTPException(status_code=404, detail=f"Policyholder with ID {cl.policyholder_id} not found.")
        raise HTTPException(status_code=500, detail=f"Database error creating claim: {error_obj.message}")
    except Exception as e_general:
        print(f"General Error creating claim: {str(e_general)}")
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {type(e_general).__name__}")
    finally:
        if cur: cur.close()
        if conn: conn.close()

@app.get("/claims/", response_model=List[ClaimOut], tags=["Claims"])
def list_claims():
    """Retrieves a list of all claims."""
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, policyholder_id, amount, reason, status, date_of_claim FROM claims ORDER BY date_of_claim DESC, id DESC")
        rows = cur.fetchall()
        return [
            {
                "id": r[0], "policyholder_id": r[1], "amount": r[2], "reason": r[3],
                "status": r[4],
                "date_of_claim": r[5].isoformat() if isinstance(r[5], (datetime, date)) else str(r[5])
            }
            for r in rows
        ]
    except oracledb.DatabaseError as e_db:
        error_obj, = e_db.args
        print(f"Oracle Error listing claims: {error_obj.message}")
        raise HTTPException(status_code=500, detail=f"Database error listing claims: {error_obj.message}")
    except Exception as e_general:
        print(f"General Error listing claims: {str(e_general)}")
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {type(e_general).__name__}")
    finally:
        if cur: cur.close()
        if conn: conn.close()


@app.get("/risk_analysis/", tags=["Analysis & Reports"])
async def risk_analysis_endpoint():
    """
    Performs risk analysis on policyholders based on their claims history.
    - Identifies policyholders with rejected claims > 80% of sum insured (assessment skipped for these).
    - Flags high-risk policyholders based on:
        1. More than 3 approved claims in the last year.
        2. An approved claim amount exceeding 80% of their sum insured.
    - Provides a summary of approved claims by policy type.
    - Provides a summary of ALL claims by policy type.
    """
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        now = datetime.now()
        one_year_ago_target_date = (now - timedelta(days=365)).date()

        cur.execute("SELECT id, name, sum_insured, policy_type FROM policyholders")
        policyholders_data = cur.fetchall()
        policyholder_map = {
            ph_id: {"name": name, "sum_insured": si, "policy_type": pt}
            for ph_id, name, si, pt in policyholders_data
        }

        cur.execute("SELECT id, policyholder_id, amount, status, date_of_claim FROM claims")
        all_claims_rows = cur.fetchall()

        global_approved_claims_by_policy_type = defaultdict(int)
        for claim_row_tuple in all_claims_rows:
            claim_status = claim_row_tuple[3]
            if claim_status == 'Approved':
                policyholder_id_for_claim = claim_row_tuple[1]
                if policyholder_id_for_claim in policyholder_map:
                    policy_type = policyholder_map[policyholder_id_for_claim]["policy_type"]
                    global_approved_claims_by_policy_type[policy_type] += 1
        
        # total claims by policy type
        total_claims_by_policy_type = defaultdict(int)
        for claim_row_tuple in all_claims_rows:
            policyholder_id_for_claim = claim_row_tuple[1] # policyholder_id
            if policyholder_id_for_claim in policyholder_map:
                policy_type = policyholder_map[policyholder_id_for_claim]["policy_type"]
                total_claims_by_policy_type[policy_type] += 1

        risk_report = []
        high_risk_policyholders_details = []

        for ph_id, ph_info in policyholder_map.items():
            policyholder_all_claims_tuples = [
                claim_row for claim_row in all_claims_rows if claim_row[1] == ph_id
            ]

            has_rejected_claim_over_80_percent = False
            if ph_info["sum_insured"] and ph_info["sum_insured"] > 0:
                for claim_tuple in policyholder_all_claims_tuples:
                    claim_amount = claim_tuple[2]
                    claim_status = claim_tuple[3]
                    if claim_status == 'Rejected' and (claim_amount / ph_info["sum_insured"]) > 0.80:
                        has_rejected_claim_over_80_percent = True
                        break
            
            if has_rejected_claim_over_80_percent:
                risk_report.append({
                    'policyholder_id': ph_id, 'name': ph_info["name"],
                    'risk_status_message': "Risk assessment skipped: Policyholder has a rejected claim exceeding 80% of sum insured.",
                    'high_risk': False,
                    'reason': "A rejected claim >80% of sum insured exists."
                })
                continue

            ph_approved_claims_tuples = [
                claim_tuple for claim_tuple in policyholder_all_claims_tuples if claim_tuple[3] == 'Approved'
            ]

            recent_approved_claims_count = 0
            for app_claim_tuple in ph_approved_claims_tuples:
                claim_date_val = app_claim_tuple[4]
                current_claim_date_obj = None
                if isinstance(claim_date_val, datetime): current_claim_date_obj = claim_date_val.date()
                elif isinstance(claim_date_val, date): current_claim_date_obj = claim_date_val
                
                if current_claim_date_obj and current_claim_date_obj >= one_year_ago_target_date:
                    recent_approved_claims_count += 1
            
            is_high_risk = False
            risk_reasons = []

            if recent_approved_claims_count > 3:
                is_high_risk = True
                risk_reasons.append(f"{recent_approved_claims_count} approved claims in the last year.")

            if ph_info["sum_insured"] and ph_info["sum_insured"] > 0:
                for app_claim_tuple in ph_approved_claims_tuples:
                    app_claim_id = app_claim_tuple[0]
                    app_claim_amount = app_claim_tuple[2]
                    if (app_claim_amount / ph_info["sum_insured"]) > 0.80:
                        is_high_risk = True
                        risk_reasons.append(f"An approved claim (ID: {app_claim_id}, Amount: {app_claim_amount:.2f}) exceeds 80% of sum insured ({ph_info['sum_insured']:.2f}).")
                        break

            if is_high_risk:
                risk_report.append({
                    'policyholder_id': ph_id, 'name': ph_info["name"],
                    'risk_status_message': "High Risk", 'high_risk': True,
                    'reason': "; ".join(risk_reasons) if risk_reasons else "High risk conditions met."
                })
                high_risk_policyholders_details.append({
                    'policyholder_id': ph_id, 'name': ph_info["name"],
                    'reason_for_high_risk': "; ".join(risk_reasons) if risk_reasons else "High risk conditions met.",
                    'recent_accepted_claims_count': recent_approved_claims_count
                })
            else:
                risk_report.append({
                    'policyholder_id': ph_id, 'name': ph_info["name"],
                    'risk_status_message': "Standard Risk", 'high_risk': False,
                    'reason': "No high-risk conditions met based on approved claims."
                })

        return {
            "risk_analysis_report": risk_report,
            "high_risk_summary": high_risk_policyholders_details,
            "claims_by_policy_type_approved": dict(global_approved_claims_by_policy_type),
            "total_claims_by_policy_type": dict(total_claims_by_policy_type) # ADDED THIS LINE
        }

    except oracledb.DatabaseError as e_db:
        error_obj, = e_db.args
        detail_message = f"Database error during risk analysis (Code: {error_obj.code}): {error_obj.message}"
        print(f"Oracle Error in risk analysis: {detail_message}")
        raise HTTPException(status_code=500, detail=detail_message)
    except Exception as e_general:
        error_type_name = type(e_general).__name__
        error_message = str(e_general)
        print(f"General Error in risk analysis ({error_type_name}): {error_message}")
        raise HTTPException(status_code=500, detail=f"An unexpected error in risk analysis: {error_type_name}.")
    finally:
        if cur: cur.close()
        if conn: conn.close()

@app.get("/reports/", tags=["Analysis & Reports"])
def reports_endpoint():
    """Generates various reports based on claims and policyholder data."""
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT TO_CHAR(date_of_claim, 'YYYY-MM') AS claim_month, COUNT(*) AS claim_count
            FROM claims
            GROUP BY TO_CHAR(date_of_claim, 'YYYY-MM')
            ORDER BY claim_month
        """)
        claims_per_month = {row[0]: row[1] for row in cur.fetchall()}
        
        cur.execute("""
            SELECT p.policy_type, NVL(AVG(c.amount), 0) AS avg_amount
            FROM policyholders p
            LEFT JOIN claims c ON c.policyholder_id = p.id AND c.status = 'Approved'
            GROUP BY p.policy_type
        """)
        avg_claim_by_type = {row[0]: round(float(row[1]), 2) for row in cur.fetchall()}
        
        cur.execute("""
            SELECT id, amount, policyholder_id
            FROM claims
            ORDER BY amount DESC
            FETCH FIRST 1 ROWS ONLY
        """)
        row = cur.fetchone()
        highest_claim_info = {'id': row[0], 'amount': float(row[1]), 'policyholder_id': row[2]} if row else None
        
        cur.execute("SELECT DISTINCT policyholder_id FROM claims WHERE status = 'Pending'")
        pending_ph_ids_tuples = cur.fetchall()
        pending_ph_ids = [item[0] for item in pending_ph_ids_tuples]

        pending_names = []
        if pending_ph_ids:
            bind_names = [f":id{i+1}" for i in range(len(pending_ph_ids))]
            bind_values = {f"id{i+1}": ph_id for i, ph_id in enumerate(pending_ph_ids)}
            if bind_names:
                query = f"SELECT name FROM policyholders WHERE id IN ({','.join(bind_names)})"
                cur.execute(query, bind_values)
                pending_names = [r[0] for r in cur.fetchall()]
            
        return {
            'claims_per_month': claims_per_month,
            'avg_claim_by_type': avg_claim_by_type,
            'highest_claim': highest_claim_info,
            'policyholders_with_pending_claims': pending_names
        }
    except oracledb.DatabaseError as e_db:
        error_obj, = e_db.args
        detail_message = f"Database error during report generation (Code: {error_obj.code}): {error_obj.message}"
        print(f"Oracle Error in reports: {detail_message}")
        raise HTTPException(status_code=500, detail=detail_message)
    except Exception as e_general:
        error_type_name = type(e_general).__name__
        error_message = str(e_general)
        print(f"General Error in reports ({error_type_name}): {error_message}")
        raise HTTPException(status_code=500, detail=f"An unexpected error during report generation: {error_type_name}.")
    finally:
        if cur: cur.close()
        if conn: conn.close()

# To run: uvicorn api:app --reload