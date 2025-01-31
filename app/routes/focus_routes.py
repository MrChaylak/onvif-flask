from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.schemas.camera_schema import CameraSchema
from app.schemas.focus_schema import FocusMoveSchema
from app.services.onvif_service import move_focus, stop_focus

focus_bp = Blueprint('focus', __name__)


@focus_bp.route('/move', methods=['POST'])
def move_focus_onvif_camera():
    data = request.json
    
    schema = CameraSchema()

    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400

    ip = validated_data['ip']
    username = validated_data['username']
    password = validated_data['password']

    schema = FocusMoveSchema()

    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400
    
    focus_speed = validated_data['focus_speed']
    
    # Call service function
    response = move_focus(ip, username, password, focus_speed)
    
    # Check if response contains an error
    if isinstance(response, tuple) and "error" in response[0]:
        # Return the error message with its associated status code
        return jsonify(response[0]), response[1]

    # If no error, return the successful response
    return jsonify(response), 200


@focus_bp.route('/stop', methods=['POST'])
def stop_focus_onvif_camera():
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
    response = stop_focus(ip, username, password)
    
    # Check if response contains an error
    if isinstance(response, tuple) and "error" in response[0]:
        # Return the error message with its associated status code
        return jsonify(response[0]), response[1]

    # If no error, return the successful response
    return jsonify(response), 200
