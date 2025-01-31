from flask import Blueprint, jsonify
from app.services.discovery_service import fetch_devices

discovery_bp = Blueprint('discovery', __name__)

@discovery_bp.route('/onvif-devices', methods=['GET'])
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
    