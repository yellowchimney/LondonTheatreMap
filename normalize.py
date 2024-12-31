import pandas as pd

file_path = 'london_theatre_shows.csv'
data = pd.read_csv(file_path)

data.columns = data.columns.str.strip()
data['categories'] = data['categories'].str.split(',')
data_exploded = data.explode('categories')
data_exploded['categories'] = data_exploded['categories'].str.strip()
data_exploded['categories'] = data_exploded['categories'].str.strip('[]')

unique_categories = data_exploded['categories'].unique()
data_exploded = data_exploded.drop(columns=['description'])
processed_file_path = 'processed_data.csv'
data_exploded.to_csv(processed_file_path, index=False)
