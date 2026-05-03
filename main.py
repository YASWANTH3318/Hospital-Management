from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Import the ML Engine we just created!
from backend_api.ml_engine import calculate_priority_score, predict_wait_time

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

app = FastAPI(title="HCL Smart Patient Queue API")

class PatientBooking(BaseModel):
    name: str
    phone: str
    age: int
    doctor_id: str
    symptoms: str

@app.get("/")
def health_check():
    return {"status": "API is running with ML Engine Active"}

@app.post("/book_appointment")
def book_appointment(booking: PatientBooking):
    try:
        # 1. Create Patient
        patient_res = supabase.table("patients").insert({
            "name": booking.name,
            "phone": booking.phone,
            "age": booking.age
        }).execute()
        patient_id = patient_res.data[0]['id']

        # 2. Get Live Queue Position
        queue_count = supabase.table("appointments").select("id", count="exact").eq("doctor_id", booking.doctor_id).eq("status", "waiting").execute()
        patients_waiting = queue_count.count
        next_token = patients_waiting + 1

        # --- THE SMART ENGINE KICKS IN HERE ---
        
        # 3. Calculate Priority Score based on symptoms
        priority = calculate_priority_score(booking.symptoms)
        
        # 4. Predict Wait Time based on historical data
        wait_time = predict_wait_time(booking.doctor_id, patients_waiting, supabase)

        # --------------------------------------

        # 5. Save the Smart Appointment
        appt_res = supabase.table("appointments").insert({
            "patient_id": patient_id,
            "doctor_id": booking.doctor_id,
            "symptoms": booking.symptoms,
            "status": "waiting",
            "token_number": next_token,
            "priority_score": priority,           # New!
            "predicted_wait_time_mins": wait_time # New!
        }).execute()

        return {
            "message": "Smart Booking Successful!",
            "token_number": next_token,
            "priority_score": priority,
            "predicted_wait_time_mins": wait_time
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/live_queue/{doctor_id}")
def get_live_queue(doctor_id: str):
    try:
        # Notice we are now sorting by priority_score first, then token_number!
        response = supabase.table("appointments").select(
            "id, token_number, symptoms, priority_score, predicted_wait_time_mins, patients(name, age)"
        ).eq("doctor_id", doctor_id).eq("status", "waiting").order("priority_score", desc=True).order("token_number").execute()
        
        return {"queue_length": len(response.data), "queue": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))