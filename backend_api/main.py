from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

app = FastAPI(title="HCL Smart Patient Queue API")

# --- Request Data Models ---
class PatientBooking(BaseModel):
    name: str
    phone: str
    age: int
    doctor_id: str
    symptoms: str

# --- API Endpoints ---

@app.get("/")
def health_check():
    return {"status": "API is running", "role": "Data Engineering & Backend"}

@app.post("/book_appointment")
def book_appointment(booking: PatientBooking):
    """Books a new patient and adds them to the live queue."""
    try:
        # 1. Create the Patient Record
        patient_res = supabase.table("patients").insert({
            "name": booking.name,
            "phone": booking.phone,
            "age": booking.age
        }).execute()
        patient_id = patient_res.data[0]['id']

        # 2. Calculate the next Token Number for this doctor
        queue_count = supabase.table("appointments").select("id", count="exact").eq("doctor_id", booking.doctor_id).eq("status", "waiting").execute()
        next_token = queue_count.count + 1

        # 3. Create the Appointment Record
        appt_res = supabase.table("appointments").insert({
            "patient_id": patient_id,
            "doctor_id": booking.doctor_id,
            "symptoms": booking.symptoms,
            "status": "waiting",
            "token_number": next_token
        }).execute()

        return {
            "message": "Booking Successful!",
            "token_number": next_token,
            "appointment_id": appt_res.data[0]['id']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/live_queue/{doctor_id}")
def get_live_queue(doctor_id: str):
    """Fetches the live waiting queue for the doctor's dashboard."""
    try:
        # Fetch waiting appointments and join with patient details
        response = supabase.table("appointments").select(
            "id, token_number, symptoms, priority_score, predicted_wait_time_mins, patients(name, age)"
        ).eq("doctor_id", doctor_id).eq("status", "waiting").order("token_number").execute()
        
        return {"queue_length": len(response.data), "queue": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))