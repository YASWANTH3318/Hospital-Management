import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client
from faker import Faker

# Load environment variables
load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
fake = Faker()

def generate_historical_data():
    print("Starting Data Pipeline: Generating Mock Healthcare Data...")

    # 1. Create a Doctor
    doc_response = supabase.table("doctors").insert({
        "name": "Dr. Smith",
        "specialization": "Cardiologist",
        "base_consultation_time_mins": 15
    }).execute()
    doctor_id = doc_response.data[0]['id']
    print(f"Created Doctor ID: {doctor_id}")

    # 2. Generate 50 historical queue logs for ML training
    logs = []
    base_time = datetime.now() - timedelta(days=7) # Start 7 days ago

    for i in range(50):
        # Create a fake patient
        patient_response = supabase.table("patients").insert({
            "name": fake.name(),
            "phone": fake.phone_number()[:15],
            "age": random.randint(18, 80)
        }).execute()
        patient_id = patient_response.data[0]['id']

        # Create a completed appointment
        appt_response = supabase.table("appointments").insert({
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "symptoms": fake.text(max_nb_chars=50),
            "status": "completed",
            "token_number": i + 1
        }).execute()
        appt_id = appt_response.data[0]['id']

        # Generate realistic consultation durations (e.g., normal dist around 15 mins)
        duration = int(random.gauss(15, 4)) 
        duration = max(5, duration) # Minimum 5 mins

        start_time = base_time + timedelta(minutes=random.randint(1, 10))
        end_time = start_time + timedelta(minutes=duration)
        base_time = end_time # Next patient starts after this one

        logs.append({
            "appointment_id": appt_id,
            "doctor_id": doctor_id,
            "actual_start_time": start_time.isoformat(),
            "actual_end_time": end_time.isoformat(),
            "duration_minutes": duration
        })

    # Bulk insert historical logs
    supabase.table("queue_logs").insert(logs).execute()
    print("Successfully loaded 50 historical records into PostgreSQL!")

if __name__ == "__main__":
    generate_historical_data()