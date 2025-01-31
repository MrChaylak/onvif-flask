def display(any_list):
    for item in any_list:
        print(item)


def handle_onvif_error(error_message):
    """
    Handles ONVIF errors by categorizing them and returning a proper error message and code.

    Args:
    - error_message (str): The error message returned by the ONVIF service.

    Returns:
    - tuple: A tuple containing the error message (dict) and an HTTP status code.
    """

    # Check if the error is related to authorization issues (invalid username/password)
    if "Sender not Authorized" in error_message:
        if "Invalid username or password" in error_message:
            # Return error for invalid username/password with a 401 status code
            return {"error": "Invalid username or password. Please check your credentials."}, 401
        else:
            # General authorization failure, could be other issues (e.g., network, permissions)
            return {"error": "Authorization failure. Please check your access rights."}, 403

    # Check if the error is related to an invalid profile token
    elif "Profile token does not exist" in error_message:
        return {"error": "The provided profile token does not exist. Please verify the token."}, 404

    # Handle general ONVIF errors
    else:
        return {"error": error_message}, 500

