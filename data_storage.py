import pandas as pd

def save_to_csv(data):
    df = pd.DataFrame(data)
    df.to_csv('scraped_data.csv', index=False)