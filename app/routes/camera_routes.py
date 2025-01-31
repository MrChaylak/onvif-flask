from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.schemas.camera_schema import CameraSchema
from app.schemas.profile_token_schema import ProfileTokenSchema
from app.services.onvif_service import get_camera_data, set_camera_profile

camera_bp = Blueprint('camera', __name__)


@camera_bp.route('/data', methods=['POST'])
def get_onvif_camera_data():
    data = request.json
    schema = CameraSchema()

    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400

    ip = validated_data['ip']
    username = validated_data['username']
    password = validated_data['password']

    # Call service function
    response = get_camera_data(ip, username, password)

    # Check if response contains an error
    if isinstance(response, tuple) and "error" in response[0]:
        # Return the error message with its associated status code
        return jsonify(response[0]), response[1]

    # If no error, return the successful response
    return jsonify(response), 200


@camera_bp.route('/set-profile', methods=['POST'])
def set_onvif_camera_profile():
    data = request.json
    
    schema = CameraSchema()

    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400

    ip = validated_data['ip']
    username = validated_data['username']
    password = validated_data['password']

    schema = ProfileTokenSchema()

    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400
    
    profile_token = validated_data['profile_token']

    # Call service function
    response = set_camera_profile(ip, username, password, profile_token)

    # Check if response contains an error
    if isinstance(response, tuple) and "error" in response[0]:
        # Return the error message with its associated status code
        return jsonify(response[0]), response[1]

    # If no error, return the successful response
    return jsonify(response), 200
