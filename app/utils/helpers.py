def display(any_list):
    for item in any_list:
        print(item)


def handle_onvif_error(error_message):
    """
    Handles ONVIF errors by categorizing them and returning a proper error message and code.
    
    Args:
        error_message (str): The error message returned by the ONVIF service.
    
    Returns:
        tuple: A tuple containing the error message (dict) and an HTTP status code.
    """

    error_conditions = [
        (["Sender not Authorized", "Invalid username or password"], 
         {"error": "Invalid username or password. Please check your credentials."}, 401),
        (["Sender not Authorized"], 
         {"error": "Authorization failure. Please check your access rights."}, 403),
        (["Profile token does not exist"], 
         {"error": "The provided profile token does not exist. Please verify the token."}, 404)
    ]

    for substrings, error_resp, status in error_conditions:
        if all(sub in error_message for sub in substrings):
            return error_resp, status

    return {"error": error_message}, 500

