import subprocess
import sys
import os
import csv
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(filename='setup_log.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install required packages
packages = ['pandas', 'faker', 'sqlalchemy', 'psycopg2-binary', 'polars', 'seaborn', 'plotly', 'pyspark']
for package in packages:
    try:
        install(package)
        logging.info(f"Successfully installed {package}")
    except Exception as e:
        logging.error(f"Failed to install {package}: {str(e)}")

logging.info("All required packages installed")

# Import required libraries
import pandas as pd
from faker import Faker

# Create dummy_data folder
dummy_data_folder = "dummy_data"
os.makedirs(dummy_data_folder, exist_ok=True)
logging.info(f"Created folder: {dummy_data_folder}")

# Initialize Faker
fake = Faker()

# Function to create dummy data
def create_dummy_data(filename, num_records, fields):
    data = []
    for _ in range(num_records):
        record = {field: getattr(fake, field)() for field in fields}
        data.append(record)
    
    df = pd.DataFrame(data)
    
    # Add date to filename
    date_str = datetime.now().strftime("%Y%m%d")
    full_filename = f"{filename}_{date_str}.csv"
    file_path = os.path.join(dummy_data_folder, full_filename)
    
    df.to_csv(file_path, index=False)
    logging.info(f"Created dummy data file: {full_filename}")

# Function to generate NINO (National Insurance Number)
def generate_nino():
    return f"{fake.random_letter()}{fake.random_letter()}{fake.random_int(min=100000, max=999999)}{fake.random_letter()}"

# Create dummy data for PER_ALL_PEOPLE_F
people_data = []
for _ in range(1000):
    people_data.append({
        'name': fake.name(),
        'nino': generate_nino(),
        'job': fake.job(),
        'company': fake.company(),
        'date_of_birth': fake.date_of_birth()
    })

df_people = pd.DataFrame(people_data)
date_str = datetime.now().strftime("%Y%m%d")
people_filename = f"PER_ALL_PEOPLE_F_{date_str}.csv"
df_people.to_csv(os.path.join(dummy_data_folder, people_filename), index=False)
logging.info(f"Created dummy data file: {people_filename}")

# Create dummy data for PER_ALL_ASSIGNMENTS_F
create_dummy_data("PER_ALL_ASSIGNMENTS_F", 1000, 
                  ['job', 'company', 'date_joined'])

# Create dummy data for PER_ALL_ADDRESS or HR_ALL_ADDRESSES
create_dummy_data("HR_ALL_ADDRESSES", 1000, 
                  ['street_address', 'city', 'country', 'postcode'])

# Example code for each component

# 1. SQL
logging.info("Running SQL example")
import sqlite3

conn = sqlite3.connect('example.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)''')
c.execute("INSERT INTO users (name, age) VALUES (?, ?)", ('Alice', 30))
conn.commit()

df = pd.read_sql_query("SELECT * FROM users", conn)
logging.info("SQL example completed")

conn.close()

# 2. Faker
logging.info("Running Faker example")
data = [{'name': fake.name(), 'email': fake.email()} for _ in range(5)]
df_fake = pd.DataFrame(data)
logging.info("Faker example completed")

# 3. Pandas
logging.info("Running Pandas example")
import numpy as np

df = pd.DataFrame({'A': np.random.rand(5), 'B': np.random.rand(5)})
logging.info("Pandas example completed")

# 4. Polars
logging.info("Running Polars example")
import polars as pl

df_polars = pl.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
logging.info("Polars example completed")

# 5. Visualization with Seaborn and Plotly Express
logging.info("Running Visualization example")
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px

sns.set_theme()
tips = sns.load_dataset("tips")
sns.scatterplot(data=tips, x="total_bill", y="tip")
plt.savefig('seaborn_plot.png')
plt.close()
logging.info("Seaborn plot saved as 'seaborn_plot.png'")

fig = px.scatter(tips, x="total_bill", y="tip", color="size")
fig.write_html("plotly_plot.html")
logging.info("Plotly plot saved as 'plotly_plot.html'")

# 6. Simulating Databricks-like Environment Locally (Spark)
logging.info("Running PySpark example")
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .master("local[*]") \
    .appName("Local Spark") \
    .getOrCreate()

df_spark = spark.createDataFrame([(1, "Alice"), (2, "Bob")], ["id", "name"])
df_spark.show()

spark.stop()
logging.info("PySpark example completed")

logging.info("Environment setup complete")
print("Environment setup complete. Check setup_log.log for details.")