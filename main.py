from flask import Flask, request, jsonify
from flask_cors import CORS
from wsdiscovery.discovery import ThreadedWSDiscovery as WSDiscovery
from wsdiscovery import Scope
import re
from onvif import ONVIFCamera

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)


def display(any_list):
    for item in any_list:
        print(item)


def fetch_devices():
    # Initialize WS-Discovery
    wsd = WSDiscovery()

    # Define an ONVIF scope for filtering
    scope1 = Scope("onvif://www.onvif.org/Profile")
    wsd.start()

    # Search for ONVIF services with the defined scope
    services = wsd.searchServices(scopes=[scope1])

    # Extract device IP addresses
    ipaddresses = []
    for service in services:
        # Extract IP address from XAddrs
        xaddrs = service.getXAddrs()
        if xaddrs:
            ipaddress = re.search(r'(\d+\.\d+\.\d+\.\d+)', xaddrs[0])
            if ipaddress:
                ipaddresses.append(ipaddress.group(0))
                print("START----------")
                print(f"IP: {ipaddress.group(0)}")

        # Display device scopes for debugging
        print("Scopes:")
        display(service.getScopes())
        print('------------END')

    print(f'\nNumber of devices detected: {len(services)}')

    # Stop WS-Discovery
    wsd.stop()
    return ipaddresses


@app.route('/api/onvif-devices', methods=['GET'])
def get_onvif_devices():
    # Fetch ONVIF device IPs
    devices = fetch_devices()
    print(devices)
    return jsonify({'devices': devices})


@app.route('/api/onvif-camera-data', methods=['POST'])
def get_onvif_camera_data():
    data = request.json
    ip = data.get('ip')
    username = data.get('username')
    password = data.get('password')

    if not ip or not username or not password:
        return jsonify({'error': 'IP, username, and password are required'}), 400

    try:
        # Connect to the ONVIF camera
        camera = ONVIFCamera(ip, 80, username, password)

        # Get device information
        device_info = camera.devicemgmt.GetDeviceInformation()

        # Get media profiles
        media_service = camera.create_media_service()
        profiles = media_service.GetProfiles()

        # Return the data
        return jsonify({
            'device_info': {
                'manufacturer': device_info.Manufacturer,
                'model': device_info.Model,
                'firmware_version': device_info.FirmwareVersion,
                'serial_number': device_info.SerialNumber,
            },
            'profiles': [{
                'name': profile.Name,
                'token': profile.token,
            } for profile in profiles],
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
