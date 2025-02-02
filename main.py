from flask import Flask, request, jsonify
from flask_cors import CORS
from wsdiscovery.discovery import ThreadedWSDiscovery as WSDiscovery
from wsdiscovery import Scope
import re
from onvif import ONVIFCamera
import logging
from schemas import CameraSchema, PTZSchema, FocusMoveSchema
from marshmallow import ValidationError


# Suppress warnings from the daemon logger
logging.getLogger('daemon').setLevel(logging.ERROR)

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)


# Define a default profile schema
DEFAULT_PROFILE_SCHEMA = {
    'name': 'Unknown',
    'token': 'Unknown',
    'encoder': 'Unknown',
    'resolution': 'Unknown',
    'frame_rate': 'Unknown',
    'bitrate': 'Unknown',
}


def display(any_list):
    for item in any_list:
        print(item)


def fetch_devices():
    try:
        # Initialize WS-Discovery
        wsd = WSDiscovery()
        scope1 = Scope("onvif://www.onvif.org/Profile")
        wsd.start()

        # Search for ONVIF services
        services = wsd.searchServices(scopes=[scope1])

        # Extract device IP addresses
        ipaddresses = []
        for service in services:
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

        wsd.stop()
        return ipaddresses

    except Exception as e:
        print(f"Error fetching devices: {e}")
        return None  # Return None to indicate failure


@app.route("/")
def home():
    return "<h1>Flask is running!</h1>"


@app.route('/api/onvif-devices', methods=['GET'])
def get_onvif_devices():
    # Fetch ONVIF device IPs
    try:
        devices = fetch_devices()
        if devices is None:
            return jsonify({'error': 'Failed to fetch ONVIF devices'}), 500
        print(devices)
        return jsonify({'devices': devices})
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({'error': 'An unexpected error occurred'}), 500


@app.route('/api/onvif-camera-data', methods=['POST'])
def get_onvif_camera_data():
    data = request.json

    errors = {}

    # Create an instance of the CameraSchema
    camera_schema = CameraSchema()

    try:
        validated_camera_data = camera_schema.load(data)
    except ValidationError as err:
        errors.update(err.messages)  # Collect errors

    # If there are any errors, return them
    if errors:
        return jsonify({"error": errors}), 400

    # If validation passes, access the validated data
    ip = validated_camera_data['ip']
    username = validated_camera_data['username']
    password = validated_camera_data['password']

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
            profile_data = DEFAULT_PROFILE_SCHEMA.copy()  # Create a new instance with default values
            profile_data['name'] = profile.Name
            profile_data['token'] = profile.token

            try:
                # Get the video encoder configuration for the profile
                encoder_config = media_service.GetVideoEncoderConfiguration({
                    'ConfigurationToken': profile.VideoEncoderConfiguration.token
                })
                profile_data.update({  # Update only the known values
                    'encoder': encoder_config.Encoding,  # H.264, H.265, etc.
                    'resolution': f"{encoder_config.Resolution.Width}x{encoder_config.Resolution.Height}",
                    'frame_rate': encoder_config.RateControl.FrameRateLimit,
                    'bitrate': encoder_config.RateControl.BitrateLimit,
                })
            except Exception as encoder_error:
                print(f"Failed to fetch encoder details for profile {profile.Name}: {encoder_error}")

            profile_details.append(profile_data)

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


@app.route('/api/set-onvif-camera-profile', methods=['POST'])
def set_onvif_camera_profile():
    data = request.json

    errors = {}

    # Create an instance of the CameraSchema
    camera_schema = CameraSchema()
    # Create an instance of the PTZSchema
    ptz_schema = PTZSchema()

    try:
        validated_camera_data = camera_schema.load(data)
    except ValidationError as err:
        errors.update(err.messages)  # Collect errors

    try:
        validated_ptz_data = ptz_schema.load(data)
    except ValidationError as err:
        errors.update(err.messages)  # Collect errors

    # If there are any errors, return them
    if errors:
        return jsonify({"error": errors}), 400

    # If validation passes, access the validated data
    ip = validated_camera_data['ip']
    username = validated_camera_data['username']
    password = validated_camera_data['password']
    profile_token = validated_ptz_data['profile_token']

    try:
        # Connect to the ONVIF camera
        camera = ONVIFCamera(ip, 80, username, password)
        # Get the media service
        media_service = camera.create_media_service()
        # Get the stream URI for the selected profile
        stream_uri = media_service.GetStreamUri({
            'StreamSetup': {
                'Stream': 'RTP-Unicast',  # Use RTP-Unicast or RTP-Multicast
                'Transport': {
                    'Protocol': 'RTSP'  # Use RTSP, HTTP, or HTTPS
                }
            },
            'ProfileToken': profile_token,
        })
        print(stream_uri.Uri)
        return jsonify({
            'stream_uri': 'Stream URI fetched successfully',
            # 'stream_uri': stream_uri.Uri
        })
    except Exception as e:
        print(f"Error fetching stream URI for profile {profile_token}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ptz-move', methods=['POST'])
def ptz_move():
    data = request.json

    errors = {}

    missing_fields = [field for field in ['pan_speed', 'tilt_speed', 'zoom_speed'] if field not in data]

    if missing_fields:
        errors["missing_fields"] = f"missing: {', '.join(missing_fields)}"


    # Create an instance of the CameraSchema
    camera_schema = CameraSchema()
    # Create an instance of the PTZSchema
    ptz_schema = PTZSchema()

    try:
        validated_camera_data = camera_schema.load(data)
    except ValidationError as err:
        errors.update(err.messages)  # Collect errors

    try:
        validated_ptz_data = ptz_schema.load(data)
    except ValidationError as err:
        errors.update(err.messages)  # Collect errors

    # If there are any errors, return them
    if errors:
        return jsonify({"error": errors}), 400

    # If validation passes, access the validated data
    ip = validated_camera_data['ip']
    username = validated_camera_data['username']
    password = validated_camera_data['password']
    profile_token = validated_ptz_data['profile_token']
    pan_speed = validated_ptz_data['pan_speed']
    tilt_speed = validated_ptz_data['tilt_speed']
    zoom_speed = validated_ptz_data['zoom_speed']

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

    errors = {}

    # Create an instance of the CameraSchema
    camera_schema = CameraSchema()
    # Create an instance of the PTZSchema
    ptz_schema = PTZSchema()

    try:
        validated_camera_data = camera_schema.load(data)
    except ValidationError as err:
        errors.update(err.messages)  # Collect errors

    try:
        validated_ptz_data = ptz_schema.load(data)
    except ValidationError as err:
        errors.update(err.messages)  # Collect errors

    # If there are any errors, return them
    if errors:
        return jsonify({"error": errors}), 400

    # If validation passes, access the validated data
    ip = validated_camera_data['ip']
    username = validated_camera_data['username']
    password = validated_camera_data['password']
    profile_token = validated_ptz_data['profile_token']

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

    errors = {}

    # Create an instance of the CameraSchema
    camera_schema = CameraSchema()
    # Create an instance of the PTZSchema
    focus_move_schema = FocusMoveSchema()

    try:
        validated_camera_data = camera_schema.load(data)
    except ValidationError as err:
        errors.update(err.messages)  # Collect errors

    try:
        validated_focus_move_data = focus_move_schema.load(data)
    except ValidationError as err:
        errors.update(err.messages)  # Collect errors

    # If there are any errors, return them
    if errors:
        return jsonify({"error": errors}), 400

    # If validation passes, access the validated data
    ip = validated_camera_data['ip']
    username = validated_camera_data['username']
    password = validated_camera_data['password']
    focus_speed = validated_focus_move_data['focus_speed']

    try:
        # Connect to the ONVIF camera
        camera = ONVIFCamera(ip, 80, username, password)

        # Create Imaging service
        imaging_service = camera.create_imaging_service()

        # Get the video source token (required for focus control)
        media_service = camera.create_media_service()
        profiles = media_service.GetProfiles()

        if not profiles:
            raise ValueError("No ONVIF profiles found on the camera")
        video_source_token = profiles[0].VideoSourceConfiguration.SourceToken

        # Move focus continuously
        imaging_service.Move({
            'VideoSourceToken': video_source_token,
            'Focus': {
                'Continuous': {
                    'Speed': focus_speed
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

    errors = {}

    # Create an instance of the CameraSchema
    camera_schema = CameraSchema()

    try:
        validated_camera_data = camera_schema.load(data)
    except ValidationError as err:
        errors.update(err.messages)  # Collect errors

    # If there are any errors, return them
    if errors:
        return jsonify({"error": errors}), 400

    # If validation passes, access the validated data
    ip = validated_camera_data['ip']
    username = validated_camera_data['username']
    password = validated_camera_data['password']

    try:
        # Connect to the ONVIF camera
        camera = ONVIFCamera(ip, 80, username, password)

        # Create Imaging service
        imaging_service = camera.create_imaging_service()

        # Get the video source token (required for focus control)
        media_service = camera.create_media_service()
        profiles = media_service.GetProfiles()

        if not profiles:
            raise ValueError("No ONVIF profiles found on the camera")
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
