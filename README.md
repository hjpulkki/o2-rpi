Below is an example of how you can replace Apache with a Python-based Dash application served by Gunicorn to create a captive portal on your Raspberry Pi. The overall captive portal network setup (using hostapd and dnsmasq) remains the same; you’re simply swapping out Apache for your Dash/Gunicorn app.

In summary, you’ll:

Set up your RPi as an access point with hostapd and dnsmasq (as described previously).
Create a Dash app (your captive portal page).
Serve the Dash app with Gunicorn (listening on all interfaces, port 80) so that when a device connects, any HTTP request is redirected to your Dash application.
Below are the detailed steps:

1. Configure the Raspberry Pi as an Access Point
(If you already have this set up, you can skip to Section 2.)

Install Required Packages:

bash
Kopioi
Muokkaa
sudo apt-get update
sudo apt-get install hostapd dnsmasq
Configure hostapd:
Create or edit /etc/hostapd/hostapd.conf with settings similar to:

ini
Kopioi
Muokkaa
interface=wlan0
driver=nl80211
ssid=O2-analyser         # Change to your desired SSID
hw_mode=g
channel=6
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
Then, in /etc/default/hostapd, set:

bash
Kopioi
Muokkaa
DAEMON_CONF="/etc/hostapd/hostapd.conf"
Configure dnsmasq:
Backup the original configuration and create a new one:

bash
Kopioi
Muokkaa
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
sudo nano /etc/dnsmasq.conf
Add:

ini
Kopioi
Muokkaa
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
# Redirect all DNS queries to the Pi’s IP address
address=/#/192.168.4.1
Set a Static IP for wlan0:
Edit /etc/dhcpcd.conf:

ini
Kopioi
Muokkaa
interface wlan0
    static ip_address=192.168.4.1/24
Start the Services:

bash
Kopioi
Muokkaa
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl start hostapd
sudo systemctl restart dnsmasq
At this point, your RPi broadcasts the SSID “O2-analyser” and assigns clients IPs from 192.168.4.2 to 192.168.4.20. The dnsmasq setting forces every DNS request to resolve to 192.168.4.1, which is where your captive portal will be running.

2. Create Your Dash Application
You can build your captive portal page using Dash, a Python framework for building web applications.

a. Install Dash and Gunicorn
Make sure you have Python 3 and pip installed. Then, install Dash and Gunicorn in your virtual environment or system-wide:

bash
Kopioi
Muokkaa
pip3 install dash gunicorn
b. Write a Minimal Dash App
Create a file called app.py (for example, in your home directory or a dedicated project folder):

python
Kopioi
Muokkaa
# app.py
import dash
from dash import html

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of your captive portal page
app.layout = html.Div(
    style={'textAlign': 'center', 'marginTop': '50px'},
    children=[
        html.H1("Welcome to the Raspberry Pi Captive Portal"),
        html.P("You are now connected to the Pi network. Enjoy your stay!"),
        # Add more components or instructions as needed
    ]
)

# Expose the Flask server instance (needed by Gunicorn)
server = app.server

if __name__ == '__main__':
    # For debugging purposes; Gunicorn will be used in production.
    app.run_server(host='0.0.0.0', port=80)
In this example, the layout is very simple. You can customize it further as needed.

3. Serve the Dash App with Gunicorn
Gunicorn is a production-ready WSGI server that can serve your Dash (Flask) app.

a. Running Gunicorn Manually
Test your Dash app by running Gunicorn from the command line:

bash
Kopioi
Muokkaa
sudo gunicorn app:server -b 0.0.0.0:80
Note:

The argument app:server means “import the variable server from the module app.”
Running on port 80 requires root privileges or appropriate capability settings. Alternatively, you could choose a different port (like 8080) and adjust your dnsmasq configuration accordingly.
Once Gunicorn is running, any HTTP request to the Pi (192.168.4.1) will be served by your Dash application.

b. Creating a Systemd Service for Gunicorn (Optional)
To have Gunicorn start automatically when your Pi boots:

Create a systemd service file, e.g., /etc/systemd/system/dashapp.service:

ini
Kopioi
Muokkaa
[Unit]
Description=Gunicorn instance to serve Dash captive portal
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/path-to-your-app-directory
ExecStart=/usr/bin/gunicorn app:server -b 0.0.0.0:80
Restart=always

[Install]
WantedBy=multi-user.target
Make sure to adjust User and WorkingDirectory as appropriate for your setup.

Reload systemd, enable, and start the service:

bash
Kopioi
Muokkaa
sudo systemctl daemon-reload
sudo systemctl enable dashapp.service
sudo systemctl start dashapp.service
Check the status with:

bash
Kopioi
Muokkaa
sudo systemctl status dashapp.service
Now your Dash captive portal will start automatically on boot.

4. How It All Works Together
Client Connection:
When a device (e.g., your phone) connects to the “O2-analyser” network, it is assigned an IP address (e.g., 192.168.4.5).

DNS Redirection:
The dnsmasq configuration (address=/#/192.168.4.1) forces every DNS query to resolve to 192.168.4.1. This means that regardless of which URL is entered, the client is directed to your Pi.

Captive Portal Serving:
Gunicorn is listening on port 80 and serving your Dash app. When the client’s browser makes any HTTP request, it reaches your Dash application, and the captive portal page is displayed.

Device Behavior:
Modern devices often automatically detect captive portals and open a special browser window for authentication or information. In your case, the Dash app serves as the portal page.

Summary
Replacing Apache:
Instead of Apache, you build a Dash app (in app.py) to serve your captive portal page and use Gunicorn to run it.

Serving the App:
Run Gunicorn with the command:

bash
Kopioi
Muokkaa
sudo gunicorn app:server -b 0.0.0.0:80
or set it up as a systemd service for automatic startup.

Captive Portal Flow:
With dnsmasq redirecting all DNS queries to 192.168.4.1, any HTTP request from a connected device reaches your Dash app served by Gunicorn.

This configuration lets you use existing apps or a browser on your phone without writing a custom mobile app, while providing a modern Python-based captive portal.
