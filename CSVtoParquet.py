import pandas as pd

# Read the CSV file
csv_file = r"C:\Users\u2454346\Desktop\GenAI\SalesGPT\Parquet Approach\encquote.csv"
df = pd.read_csv(csv_file, encoding='ISO-8859-1', dtype={'Quote_NumberAndRev__c': str})

# Save as a Parquet file
parquet_file = 'encquote.parquet'
df.to_parquet(parquet_file, engine='pyarrow', index=False)

print(f"Converted {csv_file} to {parquet_file} successfully.")