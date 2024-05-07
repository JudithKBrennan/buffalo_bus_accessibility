import pandas as pd

# Replace 'data.csv' with the actual path to your CSV file
file_path = './final_no_intermediate.csv'

# Read the CSV file into a DataFrame
df = pd.read_csv(file_path)

# Filter the DataFrame where Num_of_Buses = 1; change this according to the reqirement
filtered_df = df[df['Num_of_Buses'] == 1]

# Specify the path for the output CSV file
output_file_path = './filtered_data.csv'

# Export the filtered DataFrame to a CSV file
filtered_df.to_csv(output_file_path, index=False)

# Optionally, display the first few rows of the filtered DataFrame
# print(filtered_df.head())