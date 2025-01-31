from onvif import ONVIFCamera

# Define a default profile schema
DEFAULT_PROFILE_SCHEMA = {
    'name': 'Unknown',
    'token': 'Unknown',
    'encoder': 'Unknown',
    'resolution': 'Unknown',
    'frame_rate': 'Unknown',
    'bitrate': 'Unknown',
}


def get_camera_data(ip, username, password):
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
        return {
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
        }
    except Exception as e:
        # Handle specific authentication errors
        if "Unauthorized" in str(e) or "401" in str(e):
            print(f"Authentication failed: Incorrect username or password for camera at {ip}")
            return {'error': 'Incorrect username or password'}, 401
        else:
            print(f"Error fetching ONVIF camera data: {e}")
            return {'error': str(e)}, 500


def set_camera_profile(ip, username, password, profile_token):
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
        return {
            'stream_uri': 'Stream URI fetched successfully',
            # 'stream_uri': stream_uri.Uri
        }
    except Exception as e:
        print(f"Error fetching stream URI for profile {profile_token}: {e}")
        return {'error': str(e)}, 500
    