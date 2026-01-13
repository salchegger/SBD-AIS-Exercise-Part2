#This agent uses a sliding window (simulated) to perform velocity checks and score the transaction

import json
from collections import deque
import time
from kafka import KafkaConsumer

#added - for helper functions
#from decimal import Decimal
#import base64

# Simulated In-Memory State for Velocity Checks.
user_history = {} 


def analyze_fraud(transaction):
    user_id = transaction['user_id']
    amount = float(transaction['amount'])
    
    # 1. Velocity Check (Recent transaction count)
    now = time.time()
    if user_id not in user_history:
        user_history[user_id] = deque()
    
    # Keep only last 60 seconds of history
    user_history[user_id].append(now)
    while user_history[user_id] and user_history[user_id][0] < now - 60:
        user_history[user_id].popleft()

    velocity = len(user_history[user_id])
    
    # 2. Heuristic Fraud Scoring
    score = 0
    if velocity > 5: score += 40  # Too many transactions in a minute
    if amount > 4000: score += 50 # High value transaction
    
    # 3. Simulate ML Model Hand-off
    # model.predict([[velocity, amount]])
    
    return score

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

print("Agent started. Listening for CDC events...")
for message in consumer:  #consumer has to be implemented before!
    # Debezium wraps data in an 'after' block
    payload = message.value.get('payload', {})
    data = payload.get('after')
    
    if data:
        fraud_score = analyze_fraud(data)
        if fraud_score > 70:
            print(f"⚠️ HIGH FRAUD ALERT: User {data['user_id']} | Score: {fraud_score} | Amt: {data['amount']}")
        else:
            print(f"✅ Transaction OK: {data['id']} (Score: {fraud_score})")