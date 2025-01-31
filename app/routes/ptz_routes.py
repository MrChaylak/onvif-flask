from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.schemas.camera_schema import CameraSchema
from app.schemas.profile_token_schema import ProfileTokenSchema
from app.schemas.ptz_schema import PTZSchema
from app.services.onvif_service import ptz_move, ptz_stop

ptz_bp = Blueprint('ptz', __name__)


@ptz_bp.route('/move', methods=['POST'])
def ptz_move_onvif_camera():
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

    schema = PTZSchema()

    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400
    
    pan_speed = validated_data['pan_speed']
    tilt_speed = validated_data['tilt_speed']
    zoom_speed = validated_data['zoom_speed']

    # Call service function
    response = ptz_move(ip, username, password, profile_token, pan_speed, tilt_speed, zoom_speed)

    if "error" in response:
        return jsonify(response), response[1] if isinstance(response, tuple) else 500
    
    return jsonify(response), 200


@ptz_bp.route('/stop', methods=['POST'])
def ptz_stop_onvif_camera():
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
    response = ptz_stop(ip, username, password, profile_token)

    if "error" in response:
        return jsonify(response), response[1] if isinstance(response, tuple) else 500
    
    return jsonify(response), 200
