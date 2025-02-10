import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import time
import csv
import os
import flask
from datetime import datetime

# File paths
SENSOR_FILE = "data/sensor_readings.csv"
CALIBRATION_FILE = "data/calibration.csv"

# Initialize Dash app
server = flask.Flask(__name__)
app = dash.Dash(__name__, server=server)
app.title = "O₂ analyser"

# Layout
app.layout = html.Div([
    html.H1("O₂ analyser"),
    html.Pre(id='live-voltage-data'),  # Display live voltage data
    dcc.Interval(id='interval-component', interval=1000, n_intervals=0),

    html.Hr(),
    html.H2("Calibration"),
    html.Label("Calibration Gas O₂-%:"),
    dcc.Input(id='calibration-input', type='number', value=20.9, step=0.1),
    html.Button("Recalibrate", id='calibrate-button', n_clicks=0),
    html.Pre(id='calibration-result'),  # Display calibration response

    html.Hr(),
    html.H2("Log"),
    html.Pre(id='saved-results'),  # Display saved results (kept in session)

    html.Hr(),
    html.H2("Live Results"),
    html.Pre(id='live-results'),  # Display live results
    html.Button("Save Current Results", id='save-results-button', n_clicks=0),
    
    dcc.Store(id="n_calibrations", data=0),
])


def read_file():
    df = pd.read_csv(SENSOR_FILE, header=None)
    measurement_time = df.values[0][0]
    raw_readings = df.values[0][1:]
    return raw_readings, measurement_time


def read_voltage_data():
    raw_readings, measurement_time = read_file()
    duration = time.time() - measurement_time
    readings_display = "\n".join([f"Sensor {i}: {raw:.1f} mV" for i, raw in enumerate(raw_readings)])
    return f"Live Voltage Readings (measured {duration:.1f} sec ago):\n{readings_display}"


# Update live voltage data every second
@app.callback(
    Output('live-voltage-data', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_voltage_data(_):
    return read_voltage_data()


@app.callback(
    Output('live-results', 'children'),
    Input('interval-component', 'n_intervals'),
    Input("n_calibrations", "data"),
)
def update_live_results(_, n_clicks):
    calibration_data = get_current_calibration()
    raw_readings, measurement_time = read_file()
    
    o2_percentages = [raw * calibration_data.get(i, 0) for i, raw in enumerate(raw_readings)]
    measurement_dt = datetime.utcfromtimestamp(measurement_time).strftime('%H:%M:%S.%f')[:8]
    readings_display = "\n".join([f"Sensor {i}: {raw:.1f} mV, O₂: {o2:.1f}%" for i, (raw, o2) in enumerate(zip(raw_readings, o2_percentages))])
    
    return f"Results at {measurement_dt}:\n{readings_display}\n\n"


def get_current_calibration():
    try:
        with open(CALIBRATION_FILE, "r") as f:
            reader = csv.reader(f)
            last_row = list(reader)[-1]
            calibration_data = {i: float(last_row[i + 1]) for i in range(len(last_row) - 2)}
            return calibration_data
    except Exception as e:
        print("Unable to load calibration data")
        return {}


def calibration_warning(old_gain, new_gain, mv_limit=40, change_limit=0.05):
    result = ""
    if abs(new_gain-old_gain)/new_gain > change_limit:
        result += f"\n ⚠️Warning: calibration has changed by {(new_gain-old_gain)/new_gain*100:.1f}%"
    if 100/new_gain < mv_limit:
        result += f"\n ❌Error: Corresponding 100% O₂ voltage {100/new_gain:.1f} mV (should be over {mv_limit}mV). Get a new cell."
    elif 100/new_gain < mv_limit+5:
        result += f"\n ⚠️Warning: Corresponding 100% O₂ voltage {100/new_gain:.1f} mV (should be over {mv_limit}mV)"

    return result


@app.callback(
    Output('calibration-result', 'children'),
    Output("n_calibrations", "data"),
    Input('calibration-result', 'children'),
    Input('saved-results', 'children'),
    Input('calibrate-button', 'n_clicks'),
    State('calibration-input', 'value'),
    State('n_calibrations', 'data'),
)
def recalibrate(calibration_results, saved_results, n_clicks, calibration_value, n_calibrations):
    if n_clicks > n_calibrations:
        df = pd.read_csv(SENSOR_FILE, header=None)
        raw_readings = df.values[0][1:]
        new_gains = {i: calibration_value / raw if raw else 1 for i, raw in enumerate(raw_readings)}
        calibration_data = get_current_calibration()
        
        with open(CALIBRATION_FILE, "a") as f:
            writer = csv.writer(f)
            writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S")] + [new_gains[i] for i in range(len(raw_readings))] + ["accepted"])
        
        calibration_display = "\n".join([
            f"Sensor {i}: {raw:.1f} mV, Gain: {gain:.2f} (old gain {calibration_data.get(i, 0):.2f})"
            + calibration_warning(calibration_data.get(i, 0), gain)
            for i, (raw, gain) in enumerate(zip(raw_readings, new_gains.values()))
        ])

        # saved_results += calibration_display

        return f"✅ Calibrated with {calibration_value:.1f}% oxygen:\n{calibration_display}", n_calibrations+1 #, saved_results

    return calibration_results, n_calibrations#, saved_results

# Save current results in session
@app.callback(
    Output('saved-results', 'children'),
    Input('saved-results', 'children'),
    Input('save-results-button', 'n_clicks'),
    State('live-results', 'children')
)
def save_results(saved_results, n_clicks, live_results):
    if n_clicks > 0 and live_results:
        return saved_results + live_results
    return ""

# Run the app
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=80, debug=True)
