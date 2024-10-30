from flask import Flask, request, jsonify
from utils.event_ticket import DemoEventTicket
import os
import json
import re

app = Flask(__name__)

ticket = DemoEventTicket(credentials="./utils/credentials.json")


@app.route('/create-ticket/', methods=['POST'])
def create_class():
    # Access optional dict
    issuer_id = request.args.get('issuer_id')
    class_suffix = request.args.get('class_suffix')
    object_suffix = request.args.get('object_suffix')

    missing_params = []

    if not issuer_id:
        missing_params.append("issuer_id")

    if not class_suffix:
        missing_params.append("class_suffix")

    if not object_suffix:
        missing_params.append("object_suffix")

    if missing_params:
        return jsonify(
            error="Missing parameters",
            missing=missing_params,
            message="Please provide the required parameters: issuer_id, class_suffix, object_suffix."
        ), 400

    data = dict()

    try:
        data = handle_options(request.get_json())
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        print(e)

        data = handle_options(data)

    print(data)

    try:
        create_class = ticket.create_class(issuer_id=issuer_id, class_suffix=class_suffix, data=data)
        create_object = ticket.create_object(issuer_id=issuer_id, class_suffix=class_suffix,
                                             object_suffix=object_suffix, data=data)
        create_existing = ticket.create_jwt_existing_objects(issuer_id=issuer_id, class_suffix=class_suffix,
                                                             object_suffix=object_suffix)

        if create_object["has_error"]:
            return jsonify(create_object)

        else:
            return jsonify(create_existing)

        # return jsonify(result)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        print(e)
        return jsonify(error="An error occurred while creating the class."), 500


@app.errorhandler(404)
def not_found(error):
    # List all available endpoints
    available_endpoints = ["/create-ticket/ (POST)"]
    return jsonify(
        error="Not Found",
        message="The requested resource was not found.",
        available_endpoints=available_endpoints
    ), 404


def handle_options(data: dict) -> dict:
    # Default values
    defaults = {
        "event_name": "Event Name",
        "banner": "https://farm4.staticflickr.com/3723/11177041115_6e6a3b6f49_o.jpg",
        "main_image": "http://farm4.staticflickr.com/3738/12440799783_3dc3c20606_b.jpg",
        "google_map_url": "http://maps.google.com/",
        "header_text": "Text module header",
        "body_text": "Text module body",
        "phone_number": "9876543210",
        "section": "0",
        "issuer_name": "Issuer Name",
        "gate": "0",
        "ticket_number": "ABC123456789",
        "ticket_holder_name": "Ticket Holder Name",
        "seat": {
            "row": "0",
            "seat_no": "0"
        }
    }

    # Create a new dictionary to hold the final result
    result = defaults.copy()

    # Update result with data
    for key, default_value in defaults.items():
        if key in data:
            value = data[key]
            if isinstance(value, str):
                if value == "":
                    # If the value is an empty string, use the default value
                    result[key] = default_value
                else:
                    result[key] = value
            elif isinstance(value, dict):
                # Handle nested dictionaries
                result[key] = {**default_value, **value}  # Start with default values
                for sub_key in default_value:
                    if sub_key in value and value[sub_key] == "":
                        result[key][sub_key] = default_value[sub_key]
                    # If sub_key not in value, retain the original value
            else:
                result[key] = value

    return result


if __name__ == '__main__':
    app.run(debug=True)
