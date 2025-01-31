from onvif import ONVIFCamera
from app.utils.helpers import handle_onvif_error

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
        print(f"Error fetching ONVIF camera data: {e}")
        # If ONVIF error occurs, use the handle_onvif_error function to categorize and return error
        error_message = str(e)
        return handle_onvif_error(error_message)


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
        # If ONVIF error occurs, use the handle_onvif_error function to categorize and return error
        error_message = str(e)
        return handle_onvif_error(error_message)
    

def move_ptz(ip, username, password, profile_token, pan_speed, tilt_speed, zoom_speed):
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

        return {'message': 'PTZ movement started successfully'}
    except Exception as e:
        print(f"Error performing PTZ movement: {e}")
        # If ONVIF error occurs, use the handle_onvif_error function to categorize and return error
        error_message = str(e)
        return handle_onvif_error(error_message)


def stop_ptz(ip, username, password, profile_token):
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

        return {'message': 'PTZ movement stopped successfully'}
    except Exception as e:
        print(f"Error stopping PTZ movement: {e}")
        # If ONVIF error occurs, use the handle_onvif_error function to categorize and return error
        error_message = str(e)
        return handle_onvif_error(error_message)


def move_focus(ip, username, password, focus_speed):
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

        return {'message': 'Continuous focus adjustment started successfully'}
    except Exception as e:
        print(f"Error adjusting focus: {e}")
        # If ONVIF error occurs, use the handle_onvif_error function to categorize and return error
        error_message = str(e)
        return handle_onvif_error(error_message)


def stop_focus(ip, username, password):
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

        return {'message': 'Focus adjustment stopped successfully'}
    except Exception as e:
        print(f"Error stopping focus: {e}")
        # If ONVIF error occurs, use the handle_onvif_error function to categorize and return error
        error_message = str(e)
        return handle_onvif_error(error_message)
