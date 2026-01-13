# This agent calculates a running average for each user and flags transactions 
# that are significantly higher than their usual behavior (e.g., $3\sigma$ outliers).

from kafka import KafkaConsumer
import json
import statistics

##added - for helper functions
#from decimal import Decimal
#import base64

# Configuration

# In-memory store for user spending patterns
user_spending_profiles = {} 

def analyze_pattern(data):
    user_id = data['user_id']
    amount = float(data['amount'])
    
    if user_id not in user_spending_profiles:
        user_spending_profiles[user_id] = []
    
    history = user_spending_profiles[user_id]
    
    # Analyze if transaction is an outlier (Need at least 3 transactions to judge)
    is_anomaly = False
    if len(history) >= 3:
        avg = statistics.mean(history)
        stdev = statistics.stdev(history) if len(history) > 1 else 0
        
        # If amount is > 3x the average (Simple heuristic)
        if amount > (avg * 3) and amount > 500:
            is_anomaly = True

    # Update profile
    history.append(amount)
    # Keep only last 50 transactions per user for memory efficiency
    if len(history) > 50: history.pop(0)
    
    return is_anomaly

print("🧬 Anomaly Detection Agent started...")


#####################################################################
### added - tried to fix it with this helper -> didn't help
# def decode_amount(amount_str, scale=2):
#     """Decode Debezium DECIMAL bytes (base64 string) to float."""
#     if amount_str is None:
#         return None
#     decoded_bytes = base64.b64decode(amount_str)
#     # Convert bytes to integer, then divide by scale
#     return float(Decimal(int.from_bytes(decoded_bytes, "big")) / (10**scale))

# def value_deserializer(m):
#     data = json.loads(m.decode("utf-8"))
#     after = data.get("payload", {}).get("after", {})
#     if "amount" in after:
#         after["amount"] = decode_amount(after["amount"])
#     return data

consumer = KafkaConsumer(
    "dbserver1.public.transactions", # Debezium topic
    bootstrap_servers="127.0.0.1:9094",
    auto_offset_reset="latest",
    enable_auto_commit=False,
    group_id="fraud-detection-group2",
    value_deserializer=lambda m: json.loads(m.decode("utf-8"))
)
######################################################


for message in consumer: #consumer has to be implemented before!
    payload = message.value.get('payload', {})
    data = payload.get('after')
    
    if data:
        # Match the variable name here...
        is_fraudulent_pattern = analyze_pattern(data)
        
        # ...with the variable name here
        if is_fraudulent_pattern:
            print(f"🚨 ANOMALY DETECTED: User {data['user_id']} spent ${data['amount']} (Significantly higher than average)")
        else:
            print(f"📊 Profile updated for User {data['user_id']}")