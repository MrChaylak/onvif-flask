from flask import Flask, request, jsonify
from flask_cors import CORS
from wsdiscovery.discovery import ThreadedWSDiscovery as WSDiscovery
from wsdiscovery import Scope
import re
from onvif import ONVIFCamera
import logging

# Suppress warnings from the daemon logger
logging.getLogger('daemon').setLevel(logging.ERROR)

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
                # print("START----------")
                # print(f"IP: {ipaddress.group(0)}")

        # Display device scopes for debugging
        # print("Scopes:")
        # display(service.getScopes())
        # print('------------END')

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

        # Check if PTZ is available
        ptz_available = False
        try:
            ptz_service = camera.create_ptz_service()
            ptz_configurations = ptz_service.GetConfigurations()
            ptz_available = len(ptz_configurations) > 0
        except Exception as ptz_error:
            print(f"PTZ not available: {ptz_error}")

        # Check if the camera is running (e.g., by fetching the system date and time)
        camera_running = False
        system_date_time = None
        try:
            system_date_time = camera.devicemgmt.GetSystemDateAndTime()
            camera_running = True
        except Exception as system_error:
            print(f"Camera not running: {system_error}")

        # Format the system date and time
        formatted_date_time = None
        if system_date_time:
            utc_date_time = system_date_time.UTCDateTime
            if utc_date_time:
                formatted_date_time = (
                    f"{utc_date_time.Date.Year}-{utc_date_time.Date.Month:02d}-{utc_date_time.Date.Day:02d} "
                    f"{utc_date_time.Time.Hour:02d}:{utc_date_time.Time.Minute:02d}:{utc_date_time.Time.Second:02d}"
                )

        # Get encoder details for each profile
        profile_details = []
        for profile in profiles:
            try:
                # Get the video encoder configuration for the profile
                encoder_config = media_service.GetVideoEncoderConfiguration({
                    'ConfigurationToken': profile.VideoEncoderConfiguration.token
                })
                profile_details.append({
                    'name': profile.Name,
                    'token': profile.token,
                    'encoder': encoder_config.Encoding,  # H.264, H.265, etc.
                    'resolution': f"{encoder_config.Resolution.Width}x{encoder_config.Resolution.Height}",
                    'frame_rate': encoder_config.RateControl.FrameRateLimit,
                    'bitrate': encoder_config.RateControl.BitrateLimit,
                })
            except Exception as encoder_error:
                print(f"Failed to fetch encoder details for profile {profile.Name}: {encoder_error}")
                profile_details.append({
                    'name': profile.Name,
                    'token': profile.token,
                    'encoder': 'Unknown',
                    'resolution': 'Unknown',
                    'frame_rate': 'Unknown',
                    'bitrate': 'Unknown',
                })

        # Return the data
        return jsonify({
            'device_info': {
                'manufacturer': device_info.Manufacturer,
                'model': device_info.Model,
                'firmware_version': device_info.FirmwareVersion,
                'serial_number': device_info.SerialNumber,
                'hardware_id': device_info.HardwareId,
            },
            'profiles': profile_details,
            'ptz_available': ptz_available,
            'camera_running': camera_running,
            'system_date_time': formatted_date_time,  # Include the formatted date and time
        })
    except Exception as e:
        # Handle specific authentication errors
        if "Unauthorized" in str(e) or "401" in str(e):
            print(f"Authentication failed: Incorrect username or password for camera at {ip}")
            return jsonify({'error': 'Incorrect username or password'}), 401
        else:
            print(f"Error fetching ONVIF camera data: {e}")
            return jsonify({'error': str(e)}), 500


@app.route('/api/ptz-move', methods=['POST'])
def ptz_move():
    data = request.json
    ip = data.get('ip')
    username = data.get('username')
    password = data.get('password')
    profile_token = data.get('profileToken')
    pan_speed = data.get('panSpeed', 0.0)  # Default to 0.0 if not provided
    tilt_speed = data.get('tiltSpeed', 0.0)  # Default to 0.0 if not provided
    zoom_speed = data.get('zoomSpeed', 0.0)  # Default to 0.0 if not provided

    if not ip or not username or not password or not profile_token:
        return jsonify({'error': 'IP, username, password, and profileToken are required'}), 400

    try:
        # Connect to the ONVIF camera
        camera = ONVIFCamera(ip, 80, username, password)

        # Create PTZ service
        ptz_service = camera.create_ptz_service()

        # Send ContinuousMove command
        move_request = ptz_service.create_type('ContinuousMove')
        move_request.ProfileToken = profile_token
        move_request.Velocity = {
            'PanTilt': {
                'x': pan_speed,  # Pan speed (-1.0 to 1.0)
                'y': tilt_speed  # Tilt speed (-1.0 to 1.0)
            },
            'Zoom': {
                'x': zoom_speed  # Zoom speed (-1.0 to 1.0)
            }
        }
        ptz_service.ContinuousMove(move_request)

        return jsonify({'message': 'PTZ movement started successfully'})
    except Exception as e:
        print(f"Error performing PTZ movement: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ptz-stop', methods=['POST'])
def ptz_stop():
    data = request.json
    ip = data.get('ip')
    username = data.get('username')
    password = data.get('password')
    profile_token = data.get('profileToken')

    if not ip or not username or not password or not profile_token:
        return jsonify({'error': 'IP, username, password, and profileToken are required'}), 400

    try:
        # Connect to the ONVIF camera
        camera = ONVIFCamera(ip, 80, username, password)

        # Create PTZ service
        ptz_service = camera.create_ptz_service()

        # Send Stop command
        stop_request = ptz_service.create_type('Stop')
        stop_request.ProfileToken = profile_token
        stop_request.PanTilt = True  # Stop pan/tilt
        stop_request.Zoom = True  # Stop zoom
        ptz_service.Stop(stop_request)

        return jsonify({'message': 'PTZ movement stopped successfully'})
    except Exception as e:
        print(f"Error stopping PTZ movement: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/move-focus-continuous', methods=['POST'])
def move_focus_continuous():
    data = request.json
    ip = data.get('ip')
    username = data.get('username')
    password = data.get('password')
    speed = data.get('speed', 0.5)  # Focus speed (-1.0 to 1.0)

    if not ip or not username or not password:
        return jsonify({'error': 'IP, username, and password are required'}), 400

    try:
        # Connect to the ONVIF camera
        camera = ONVIFCamera(ip, 80, username, password)

        # Create Imaging service
        imaging_service = camera.create_imaging_service()

        # Get the video source token (required for focus control)
        media_service = camera.create_media_service()
        profiles = media_service.GetProfiles()
        video_source_token = profiles[0].VideoSourceConfiguration.SourceToken

        # Move focus continuously
        imaging_service.Move({
            'VideoSourceToken': video_source_token,
            'Focus': {
                'Continuous': {
                    'Speed': speed
                }
            }
        })

        return jsonify({'message': 'Continuous focus adjustment started successfully'})
    except Exception as e:
        print(f"Error adjusting focus: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stop-focus', methods=['POST'])
def stop_focus():
    data = request.json
    ip = data.get('ip')
    username = data.get('username')
    password = data.get('password')

    if not ip or not username or not password:
        return jsonify({'error': 'IP, username, and password are required'}), 400

    try:
        # Connect to the ONVIF camera
        camera = ONVIFCamera(ip, 80, username, password)

        # Create Imaging service
        imaging_service = camera.create_imaging_service()

        # Get the video source token (required for focus control)
        media_service = camera.create_media_service()
        profiles = media_service.GetProfiles()
        video_source_token = profiles[0].VideoSourceConfiguration.SourceToken

        # Stop focus adjustment
        imaging_service.Stop({
            'VideoSourceToken': video_source_token
        })

        return jsonify({'message': 'Focus adjustment stopped successfully'})
    except Exception as e:
        print(f"Error stopping focus: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
