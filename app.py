import requests
import pandas as pd
import streamlit as st
import plotly.express as px

def json_to_dataframe(json_data):
    # Extract the column names dynamically from the 'columns' key
    columns = [col['text'] for col in json_data['columns']]
    
    # Extract the rows dynamically from the 'data' key
    rows = []
    for entry in json_data['data']:
        # Combine the 'key' values (like region and year) with 'values' (like births)
        row = entry['key'] + entry['values']
        rows.append(row)
    
    # Create a DataFrame dynamically with the extracted columns and rows
    df = pd.DataFrame(rows, columns=columns)
    
    return df

region_codes = {
    "00": "Sverige",
    "01": "Region Stockholm",
    "03": "Region Uppsala",
    "04": "Region Södermanland",
    "05": "Region Östergötland",
    "06": "Region Jönköping",
    "07": "Region Kronoberg",
    "08": "Region Kalmar",
    "09": "Region Gotland",
    "10": "Region Blekinge",
    "12": "Region Skåne",
    "13": "Region Halland",
    "14": "Region Västra Götaland",
    "17": "Region Värmland",
    "18": "Region Örebro",
    "19": "Region Västmanland",
    "20": "Region Dalarna",
    "21": "Region Gävleborg",
    "22": "Region Västernorrland",
    "23": "Region Jämtland",
    "24": "Region Västerbotten",
    "25": "Region Norrbotten"
}

# Define the API endpoint
url = "https://api.scb.se/OV0104/v1/doris/sv/ssd/START/BE/BE0401/BE0401A/BefProgOsiktRegN"

# Define the payload (the query)
payload = {
  "query": [
    {
      "code": "Region",
      "selection": {
        "filter": "vs:RegionLän07EjAggr",
        "values": [
          "01", "03", "04", "05", "06", "07", "08", "09", "10", "12", "13", "14", "17", "18", "19", "20", "21", "22", "23", "24", "25"
        ]
      }
    },
    {
      "code": "ContentsCode",
      "selection": {
        "filter": "item",
        "values": [
          "000004LF"
        ]
      }
    },
    {
      "code": "Tid",
      "selection": {
        "filter": "item",
        "values": [
          "2024", "2025", "2026", "2027", "2028", "2029", "2030", "2031", "2032", "2033", "2034", "2035"
        ]
      }
    }
  ],
  "response": {
    "format": "json"
  }
}

# Send the POST request
response = requests.post(url, json=payload)

# Convert JSON to DataFrame
df = json_to_dataframe(response.json())

# Replace region codes with region names
df['region'] = df['region'].replace(region_codes)

# Round the 'Födda' column to zero decimals (first make sure the values are integers)
df['Födda'] = df['Födda'].astype(float).round(0)

# Calculate "Förändring i förhållande till basår" (change relative to base year 2024)
def calculate_percentage_change(df):
    # Convert 'år' to integers if not already
    df['år'] = df['år'].astype(int)

    # Create a new column for the percentage change relative to the base year (2024)
    base_year_df = df[df['år'] == 2024].set_index('region')['Födda']
    
    # Merge with the main DataFrame on 'region' to use base year values
    df = df.merge(base_year_df, on='region', suffixes=('', '_basår'))

    # Calculate the percentage change relative to the base year
    df['Förändring i förhållande till basår'] = ((df['Födda'] - df['Födda_basår']) / df['Födda_basår']) * 100

    # Format as percentages
    df['Förändring i förhållande till basår'] = df['Förändring i förhållande till basår'].round(1).astype(float)
    
    return df

# Apply the calculation to the DataFrame
df = calculate_percentage_change(df)




# Streamlit application
st.title("SCB Statistik - Prognos över antalet födda per region")

# Sidebar for selecting region
selected_region = st.sidebar.selectbox('Välj region', df['region'].unique())

# Filter the DataFrame based on the selected region
filtered_df = df[df['region'] == selected_region]

# Sort the DataFrame by 'år' in ascending order
filtered_df = filtered_df.sort_values(by='år', ascending=True)

# Create a bar chart based on "Förändring i förhållande till basår"
fig = px.bar(filtered_df, x='år', y='Förändring i förhållande till basår',
             title=f"Förändring i antal födda jämfört med basåret 2024 i {selected_region}")

# Customize x-axis to show only the values present in 'år'
fig.update_layout(
    xaxis=dict(
        tickmode='array',
        tickvals=filtered_df['år'].tolist(),
        title_text='År'
    ),
    yaxis=dict(
        title_text='Förändring i förhållande till basår (%)'
    )
)

# Show the bar chart on the app
st.plotly_chart(fig)

# Display the filtered data without thousand separators
st.subheader(f"Data för {selected_region}")
st.dataframe(filtered_df.style.format({"Födda": "{:.0f}"}))



