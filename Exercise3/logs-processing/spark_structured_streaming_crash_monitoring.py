#Exercise 3: Assignment 3
#Spark Structured Streaming Application for Monitoring User Crashes from Kafka Logs

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, lower, count, desc, window
from pyspark.sql.types import StructType, StructField, StringType, LongType

# 1. Configuration & Session Setup
CHECKPOINT_PATH = "/tmp/spark-checkpoints/logs-processing"

spark = ( 
    SparkSession.builder
    .appName("LogsProcessor")
    .config("spark.sql.streaming.checkpointLocation", CHECKPOINT_PATH)
    .getOrCreate()
)
spark.conf.set("spark.sql.shuffle.partitions", "8")
spark.sparkContext.setLogLevel("ERROR")

# 2. Define schema
schema = StructType([
    StructField("timestamp", LongType()), #timestamp in milliseconds
    StructField("status", StringType()),
    StructField("severity", StringType()),
    StructField("source_ip", StringType()),
    StructField("user_id", StringType()),
    StructField("content", StringType())
])

# 3. Read Stream
raw_df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "kafka:9092")
    .option("subscribe", "logs")
    .option("startingOffsets", "earliest")
    .option("failOnDataLoss", "false")
    .load()
)

# 4. Processing, Filtering & Aggregation
# We filter first to keep the state store small, then group and count.
analysis_df = (
    raw_df.select(from_json(col("value").cast("string"), schema).alias("data"))
    .select("data.*")
    .filter(
        (lower(col("content")).contains("crash")) & 
        ((col("severity") == "High") | (col("severity") == "Critical"))
    )
    #convert timestamp from milliseconds to Spark TimestampType
    .withColumn("event_time", (col("timestamp") / 1000).cast("timestamp"))
    #watermark to allow late records up to 10 seconds
    .withWatermark("event_time", "10 seconds")
    #group by 10-second windows and user_id
    .groupBy(window(col("event_time"), "10 seconds"),
        col("user_id")
    )
    .agg(count("*").alias("crash_count"))
)

# 5. Writing
#Only output users with more than 2 crashes
query = (
    analysis_df.select(
        col("window.start").alias("window_start"),
        col("window.end").alias("window_end"),
        col("user_id"),
        col("crash_count")
    )
    .filter(col("crash_count") > 2)
    .writeStream
    .outputMode("update") #only updates changed rows per window
    .format("console")
    .option("truncate", "false")
    .start()
)


query.awaitTermination()
