import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from hr_data_loader import load_hr_data, get_data_summary

# Set style for better visualizations
plt.style.use('seaborn')

def clean_data(df):
    """Clean the dataframe by removing duplicate columns"""
    # Get list of duplicate columns
    cols = pd.Series(df.columns)
    duplicates = cols[cols.duplicated()].values
    
    # Drop duplicate columns
    for col in duplicates:
        df = df.loc[:, ~df.columns.duplicated()]
    
    return df

def analyze_hr_data():
    """Perform comprehensive HR data analysis"""
    # Load and clean the data
    print("Loading HR data...")
    df = load_hr_data()
    df = clean_data(df)
    
    # 1. Basic Statistics
    print("\n1. Basic Statistics")
    print("-" * 50)
    get_data_summary(df)
    
    # 2. Age Distribution Analysis
    plt.figure(figsize=(10, 6))
    plt.hist(df['age'].dropna(), bins=30, edgecolor='black')
    plt.title('Age Distribution of Employees')
    plt.xlabel('Age')
    plt.ylabel('Count')
    plt.savefig('age_distribution.png')
    plt.close()
    
    # 3. Job Distribution
    job_counts = df['job'].value_counts().head(10)
    plt.figure(figsize=(12, 6))
    job_counts.plot(kind='bar')
    plt.title('Top 10 Job Positions')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('job_distribution.png')
    plt.close()
    
    # 4. Company Analysis
    company_counts = df['company'].value_counts().head(10)
    plt.figure(figsize=(12, 6))
    company_counts.plot(kind='bar')
    plt.title('Top 10 Companies')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('company_distribution.png')
    plt.close()
    
    # 5. Geographic Analysis
    country_counts = df['country'].value_counts()
    print("\nGeographic Distribution:")
    print("-" * 50)
    print("\nTop 10 Countries:")
    print(country_counts.head(10))
    
    # 6. Age Statistics by Job
    age_by_job = df.groupby('job')['age'].agg(['mean', 'min', 'max']).round(2)
    print("\nAge Statistics by Job (Top 10):")
    print("-" * 50)
    print(age_by_job.head(10))
    
    # 7. City Distribution
    city_counts = df['city'].value_counts()
    print("\nTop 10 Cities:")
    print("-" * 50)
    print(city_counts.head(10))
    
    # 8. Summary Statistics
    print("\nSummary Statistics:")
    print("-" * 50)
    print(f"Total number of employees: {len(df)}")
    print(f"Number of unique companies: {df['company'].nunique()}")
    print(f"Number of unique job positions: {df['job'].nunique()}")
    print(f"Number of countries: {df['country'].nunique()}")
    print(f"Average age: {df['age'].mean():.2f}")
    
    return df

if __name__ == "__main__":
    df = analyze_hr_data()
