# ml_engine.py

def calculate_priority_score(symptoms: str) -> int:
    """
    Triage Pipeline: Assigns a priority score (1-10) based on symptom keywords.
    Higher score = Higher priority.
    """
    symptoms_lower = symptoms.lower()
    
    # Critical Keywords (Score 9-10)
    if any(word in symptoms_lower for word in ["chest pain", "heart", "breathing", "severe", "emergency", "unconscious"]):
        return 10
    
    # High Priority Keywords (Score 6-8)
    elif any(word in symptoms_lower for word in ["fever", "severe pain", "vomiting", "bleeding", "broken"]):
        return 7
    
    # Low Priority / Routine (Score 1-3)
    elif any(word in symptoms_lower for word in ["mild", "checkup", "routine", "cold", "slight"]):
        return 3
    
    # Default Average Score
    return 5

def predict_wait_time(doctor_id: str, queue_position: int, supabase_client) -> int:
    """
    Prediction Pipeline: Calculates predicted wait time based on historical 
    average consultation time multiplied by the patient's place in the queue.
    """
    try:
        # 1. Fetch historical data for this specific doctor
        res = supabase_client.table("queue_logs").select("duration_minutes").eq("doctor_id", doctor_id).execute()
        historical_logs = res.data
        
        # 2. Calculate average duration
        if not historical_logs:
            # Fallback if no data exists yet (15 mins default)
            avg_duration = 15 
        else:
            total_minutes = sum(log['duration_minutes'] for log in historical_logs)
            avg_duration = total_minutes / len(historical_logs)
            
        # 3. Calculate total predicted wait time
        # E.g., If average is 16 mins, and you are 3rd in line -> 48 mins wait
        predicted_time = int(avg_duration * queue_position)
        return predicted_time
        
    except Exception as e:
        print(f"ML Engine Error: {e}")
        return 15 * queue_position # Safe fallback