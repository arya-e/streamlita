import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff

# Function to load data
def load_data(file):
    data = pd.read_csv(file)
    data['Date'] = pd.to_datetime(data['Date'], dayfirst=True)
    return data

def generate_summary(data):
    total_plot_area = data['Plot Area in m2'].sum()
    num_farms = data['FarmName'].nunique()
    activities_summary = data['Activity'].value_counts()
    total_dap = data['DAP(kg)'].sum()
    total_mop = data['MOP(kg)'].sum()
    seed_varieties = data['Seed Variety'].dropna().unique()
    
    avg_germination_rate = data['GERMINATION VALUE(%)'].mean()
    max_germination_rate = data['GERMINATION VALUE(%)'].max()
    min_germination_rate = data['GERMINATION VALUE(%)'].min()
    
    num_irrigation_done = data['Irrigation Done'].notna().sum()
    num_sprinkler_installed = data['Sprinker installed'].notna().sum()
    total_seed_used = data['SEED'].sum()
    
    summary_data = {
        'Total Plot Area (m2)': total_plot_area,
        'Number of Farms': num_farms,
        'Total DAP (kg)': total_dap,
        'Total MOP (kg)': total_mop,
        'Total Seed Used (kg)': total_seed_used,
        'Average Germination Rate (%)': avg_germination_rate,
        'Maximum Germination Rate (%)': max_germination_rate,
        'Minimum Germination Rate (%)': min_germination_rate,
        'Irrigation Done': num_irrigation_done,
        'Sprinkler Installed': num_sprinkler_installed
    }
    summary_df = pd.DataFrame(list(summary_data.items()), columns=['Metric', 'Value'])
    return summary_df, activities_summary, seed_varieties

# Function to generate irrigation table
# def generate_irrigation_table(data):
#     irrigation_table = data[data['Irrigation Done'].notna()][['FarmName', 'Date', 'Irrigation Done']]
#     return irrigation_table

def generate_irrigation_table(data):
    # Create a table of irrigation details
    irrigation_done = data[data['Irrigation Done'].notna()][['FarmName', 'Date', 'Irrigation Done']]
    
    # Get a list of farms without any irrigation done
    farms_without_irrigation = data[~data['FarmName'].isin(irrigation_done['FarmName'].unique())]['FarmName'].unique()
    
    # Create a DataFrame for farms without irrigation
    no_irrigation_df = pd.DataFrame(farms_without_irrigation, columns=['FarmName'])
    no_irrigation_df['Irrigation Done'] = 'No'
    # no_irrigation_df['Channels Constructed'] = 'No'
    # no_irrigation_df['Sprinker installed'] = 'No'
    
    # Combine the two DataFrames
    irrigation_table = pd.concat([irrigation_done, no_irrigation_df], ignore_index=True)

    
    return irrigation_table


# Function to generate fertilizer table
def generate_fertilizer_table(data):
    fertilizer_table = data[['FarmName', 'Date', 'DAP(kg)', 'MOP(kg)']].dropna()
    return fertilizer_table

# Function to generate tillage operations table
def generate_tillage_operations(data):
    tillage_operations = data['tillage'].value_counts()
    return tillage_operations

# Function to generate germination percentage by farmer
def generate_germination_by_farmer(data):
    germination_by_farmer = data.groupby('FarmName')['GERMINATION VALUE(%)'].max().reset_index()
    return germination_by_farmer

# Function to generate activity occurrences over time
def generate_activity_over_time(data):
    activity_over_time = data.groupby(['Date', 'Activity']).size().reset_index(name='Counts')
    return activity_over_time

def generate_gantt_data(data):
    gantt_data = data[['Date', 'Activity', 'FarmName']].rename(columns={'Date': 'Start', 'Activity': 'Task', 'FarmName': 'Resource'})
    gantt_data['Finish'] = gantt_data['Start']  # Assuming activities are single-day events for now
    return gantt_data

# Streamlit app
st.sidebar.title('Dashboard Configuration')

uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv")
if uploaded_file is not None:
    data = load_data(uploaded_file)
    
    view = st.sidebar.radio("Select View", ('Macro View', 'Micro View'))
    
    if view == 'Macro View':
        st.sidebar.header('Filters')
        date_range = st.sidebar.date_input("Select Date Range", [])
        varieties = st.sidebar.multiselect("Select Seed Varieties", options=data['Seed Variety'].dropna().unique())
        
        if date_range:
            data = data[(data['Date'] >= pd.to_datetime(date_range[0])) & (data['Date'] <= pd.to_datetime(date_range[1]))]
        if varieties:
            data = data[data['Seed Variety'].isin(varieties)]
        
        st.header('Summarized View for Overall Farms')
        summary_df, activities_summary, seed_varieties = generate_summary(data)
        st.dataframe(summary_df)

        st.write('### Germination Percentage(latest) by Farmer')
        germination_by_farmer = generate_germination_by_farmer(data)
        st.dataframe(germination_by_farmer)

        st.write('### Activities Summary')
        st.bar_chart(activities_summary)
        st.write('### Activity Occurrences Over Time')
        activity_over_time = generate_activity_over_time(data)
        fig = px.line(activity_over_time, x='Date', y='Counts', color='Activity', title='Activity Occurrences Over Time')
        st.plotly_chart(fig)
        st.write('### Seed Varieties Used')
        st.write(seed_varieties)

        st.write('### Tillage Operations')
        tillage_operations = generate_tillage_operations(data)
        st.bar_chart(tillage_operations)

        # st.write('### Gantt Chart of Activities')
        # gantt_data = generate_gantt_data(data)
        # fig_gantt = ff.create_gantt(gantt_data, index_col='Resource', show_colorbar=True, group_tasks=True, title='Gantt Chart of Activities', showgrid_x=True, showgrid_y=True)
        # st.plotly_chart(fig_gantt)

        st.write('### Irrigation Details')
        irrigation_table = generate_irrigation_table(data)
        st.dataframe(irrigation_table)

        st.write('### Fertilizer Application Details')
        fertilizer_table = generate_fertilizer_table(data)
        st.dataframe(fertilizer_table)
        
    elif view == 'Micro View':
        st.header('Detailed View for Individual Farms')
        farmers = data['FarmName'].unique()
        selected_farmer = st.selectbox('Select Farmer', farmers)
        if selected_farmer:
            farms = data[data['FarmName'] == selected_farmer]['FarmName'].unique()
            selected_farm = st.selectbox('Select Farm', farms)
            if selected_farm:
                farm_data = data[data['FarmName'] == selected_farm]
                st.write('### Activity Details')
                st.dataframe(farm_data)

                st.write('### Detailed Metrics')

                st.write('### Germination Movement Over Time')
                germination_over_time = farm_data[['Date', 'GERMINATION VALUE(%)']].sort_values(by='Date')
                st.line_chart(germination_over_time.set_index('Date'))
                
                st.write('#### Fertilizer Usage')
                st.dataframe(farm_data[['Date', 'DAP(kg)', 'MOP(kg)']])

                st.write('#### Seed Usage')
                st.dataframe(farm_data[['Date', 'SEED', 'Seed Variety']])

                st.write('#### Germination Values')
                st.dataframe(farm_data[['Date', 'GERMINATION VALUE(%)']])

                st.write('#### Irrigation Status')
                st.dataframe(farm_data[['Date', 'Irrigation Done', 'Channels Constructed', 'Sprinker installed']])

                st.write('#### Tillage Operations')
                st.dataframe(farm_data[['Date', 'tillage']])
                
                st.write('### Gantt Chart of Activities')
                gantt_data = generate_gantt_data(farm_data)
                fig_gantt = ff.create_gantt(gantt_data, index_col='Resource', show_colorbar=True, group_tasks=True, title='Gantt Chart of Activities', showgrid_x=True, showgrid_y=True)
                st.plotly_chart(fig_gantt)
