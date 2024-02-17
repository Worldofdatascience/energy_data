import pandas as pd
import os
import sys
import seaborn as sns
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image


start_time = pd.to_datetime('2023-01-01 00:00:00+00:00')
end_time = pd.to_datetime('2024-01-01 00:00:00+00:00')

duration_in_days = (end_time- start_time).days


file_path_to_data_elec = "data/raw/consumption_elec_2023.csv"
file_path_to_data_gas = "data/raw/consumption_gas_2023.csv"

def make_into_dataframe(file_path_to_data):
    file_path = os.path.join(os.getcwd(), file_path_to_data)
    dataFrame = pd.read_csv(file_path)
    return dataFrame

def preprocess_dataframe(dataFrame):
    dataFrame = dataFrame.rename(columns={' Start': 'Start'})
    dataFrame = dataFrame.rename(columns={' End': 'End'})
    dataFrame['Start'] = pd.to_datetime(dataFrame['Start'])
    dataFrame['End'] = pd.to_datetime(dataFrame['End'])
    print(dataFrame)
    return dataFrame


def lineplot_for_data(dataFrame, name_of_plot, column_to_plot):
    # Plot the data
    sns.set(style="whitegrid")
    sns.lineplot(x='Start', y= column_to_plot, \
                 data = dataFrame,label = name_of_plot)
    plt.title('Energy Consumption Over Time')
    plt.xlabel('Time')
    plt.ylabel(column_to_plot)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.legend()

def convert_m3_to_kwh(dataFrame):
    conversion_factor = 38  # MJ per cubic meter
    # 1 MJ is approximately equal to 0.2778 kWh.
    dataFrame['Consumption (kWh)'] = dataFrame['Consumption (m³)'] \
        * conversion_factor  * 0.2778
    return dataFrame

def cost_data(dataFrame, cost_per_kwh):
    dataFrame["Consumption (£)"] = dataFrame['Consumption (kWh)']* cost_per_kwh

def standing_charge(dataFrame, stading_charge, duration_in_days):
    return stading_charge * duration_in_days


elecDataFrame = make_into_dataframe(file_path_to_data_elec)
gasDataFrame = make_into_dataframe(file_path_to_data_gas)

elecDataFrame = preprocess_dataframe(elecDataFrame)
gasDataFrame = preprocess_dataframe(gasDataFrame)

gasDataFrame = convert_m3_to_kwh(gasDataFrame)

elecDataFrame = elecDataFrame[(elecDataFrame['Start'] >= start_time) \
                              & (elecDataFrame['Start'] <= end_time)]

gasDataFrame = gasDataFrame[(gasDataFrame['Start'] >= start_time) \
                              & (gasDataFrame['Start'] <= end_time)]

lineplot_for_data(elecDataFrame, "elec", 'Consumption (kWh)')
lineplot_for_data(gasDataFrame, "gas", 'Consumption (kWh)')
plt.savefig('plots/plot_dataFrame_elec_gas.png')
plt.close()

cost_data(elecDataFrame, 0.2922)
cost_data(gasDataFrame, 0.0731)
standing_charge_elec = standing_charge(elecDataFrame, 0.42, duration_in_days)
standing_charge_gas = standing_charge(gasDataFrame,0.2747, duration_in_days)

lineplot_for_data(elecDataFrame, "elec", 'Consumption (£)')
lineplot_for_data(gasDataFrame, "gas", 'Consumption (£)')
plt.savefig('plots/plot_dataFrame_elec_gas_cost.png')
plt.close()

# Create a PDF report
doc = SimpleDocTemplate("report.pdf", pagesize=letter)
content = []

def reportdata(dataFrame, plottype, standing_charge):
    # Calculate key statistics
    total_consumption = dataFrame['Consumption (kWh)'].sum()
    average_consumption = dataFrame['Consumption (kWh)'].mean()
    max_consumption = dataFrame['Consumption (kWh)'].max()

    total_consumption_cost = dataFrame['Consumption (£)'].sum()
    average_consumption_cost = dataFrame['Consumption (£)'].mean()
    max_consumption_cost = dataFrame['Consumption (£)'].max()

    # Add key statistics to the report
    key_statistics = [
        ["Total Consumption " +str(plottype), f"{total_consumption:.2f} kWh"],
        ["Average Consumption "+str(plottype), f"{average_consumption:.2f} kWh"],
        ["Maximum Consumption "+str(plottype), f"{max_consumption:.2f} kWh"],
        ["Total Consumption " +str(plottype), f"£{total_consumption_cost:.2f}"],
        ["Average Consumption "+str(plottype), f"£{average_consumption_cost:2f}"],
        ["Maximum Consumption "+str(plottype), f"£{max_consumption_cost:.2f}"],
        ["Standing Charge "+str(plottype), f"£{standing_charge:.2f}"]
    ]
    return key_statistics

key_statistics_elec = reportdata(elecDataFrame, "elec", standing_charge_elec)
key_statistics_gas = reportdata(gasDataFrame, "gas", standing_charge_gas)

content.append(Table(key_statistics_elec, colWidths=[200, 100]))
content.append(Table(key_statistics_gas, colWidths=[200, 100]))

# Add plot to the report using Image class
content.append(Image('plots/plot_dataFrame_elec_gas_cost.png', width=400, height=300))
content.append(Image('plots/plot_dataFrame_elec_gas.png', width=400, height=300))

style = TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
])

content[0].setStyle(style)
content[1].setStyle(style)

# Build the PDF report
doc.build(content)