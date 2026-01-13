#import os
#import subprocess
#import sys
import time
from datetime import datetime, timedelta
import psycopg 
from psycopg import sql

# PostgreSQL connection info
DB_NAME = "mydb"
DB_USER = "postgres"
DB_PASSWORD = "postgrespw"
DB_HOST = "127.0.0.1"
DB_PORT = 5433
DB_TABLE = "temperature_readings"


# -------------------------
# Periodically compute average over last 10 minutes
# -------------------------
try:
    while True:
        ten_minutes_ago = datetime.now() - timedelta(minutes=10)
        ## Fetch the data from the choosen source (to be implemented)
        
        #Connect to PostgreSQL
        with psycopg.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        ) as conn:
            #Using a context manager for the cursor
            with conn.cursor() as cursor:
                query = sql.SQL("SELECT * FROM {} ORDER BY id DESC LIMIT 10").format(sql.Identifier(DB_TABLE))
                cursor.execute(query)
                result = cursor.fetchall()
        
        if not result:
            print(f"{datetime.now()} - No data in last 10 minutes.")
        else:
            #Extract temperature values (assuming the temperature is in the 3rd column)
            temp_values = [record[2] for record in result]
            avg_temp = sum(temp_values) / len(temp_values)
            print(f"{datetime.now()} - Average temperature last 10 minutes: {avg_temp:.2f} °C")
        time.sleep(600) #every 10 minutes
except KeyboardInterrupt:
    print("Stopped consuming data.")
finally:
    print("Exiting.")
