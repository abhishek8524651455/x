#
# Copyright 2022 Google Inc. All rights reserved.
#
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
#

# [START setup]
# [START imports]
import json
import os
import uuid

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
from google.auth import jwt, crypt


# [END imports]


class DemoEventTicket:
    """Demo class for creating and managing Event tickets in Google Wallet.

    Attributes:
        key_file_path: Path to service account key file from Google Cloud
            Console. Environment variable: GOOGLE_APPLICATION_CREDENTIALS.
        base_url: Base URL for Google Wallet API requests.
    """

    def __init__(self, credentials):
        self.key_file_path = credentials
        # Set up authenticated client
        self.auth()

    # [END setup]

    # [START auth]
    def auth(self):
        """Create authenticated HTTP client using a service account file."""
        self.credentials = Credentials.from_service_account_file(
            self.key_file_path,
            scopes=['https://www.googleapis.com/auth/wallet_object.issuer'])

        self.client = build('walletobjects', 'v1', credentials=self.credentials)

    # [END auth]

    # [START createClass]
    def create_class(self, issuer_id: str, class_suffix: str, data: dict) -> dict:
        """Create a class.

        Args:
            issuer_id (str): The issuer ID being used for this request.
            class_suffix (str): Developer-defined unique ID for this pass class.

        Returns:
            The pass class ID: f"{issuer_id}.{class_suffix}"
        """

        # Check if the class exists
        try:
            self.client.eventticketclass().get(resourceId=f'{issuer_id}.{class_suffix}').execute()
        except HttpError as e:
            if e.status_code == 400:
                return {
                    'status': 'invalid_request',
                    'message': 'Invalid resource ID.',
                    'error': e.error_details,
                    "has_error": True
                }

            if e.status_code != 404:
                # Something else went wrong...
                return {
                    "status": "error",
                    "message": "An unexpected error occurred while checking class existence. Please try again later.",
                    "has_error": True
                }
        else:
            return {
                "status": "exists",
                "message": "The class already exists.",
                "issuer_id": issuer_id,
                "class_suffix": class_suffix,
                "class_id": f"{issuer_id}.{class_suffix}",
                "has_error": True
            }

        # See link below for more information on required properties
        # https://developers.google.com/wallet/tickets/events/rest/v1/eventticketclass
        new_class = {
            'eventId': f'{issuer_id}.{class_suffix}',
            'eventName': {
                'defaultValue': {
                    'language': 'en-US',
                    'value': f'{data["event_name"]}'
                }
            },
            'id': f'{issuer_id}.{class_suffix}',
            'issuerName': f'{data['issuer_name']}',
            'reviewStatus': 'UNDER_REVIEW'
        }

        response = self.client.eventticketclass().insert(body=new_class).execute()

        return {
            "status": "created",
            "message": "Class successfully created.",
            "issuer_id": issuer_id,
            "class_suffix": class_suffix,
            "class_id": f"{issuer_id}.{class_suffix}",
            "response": response,
            "has_error": False
        }

    # [END createClass]

    # [START updateClass]
    def update_class(self, issuer_id: str, class_suffix: str) -> str:
        """Update a class.

        **Warning:** This replaces all existing class attributes!

        Args:
            issuer_id (str): The issuer ID being used for this request.
            class_suffix (str): Developer-defined unique ID for this pass class.

        Returns:
            The pass class ID: f"{issuer_id}.{class_suffix}"
        """

        # Check if the class exists
        try:
            response = self.client.eventticketclass().get(resourceId=f'{issuer_id}.{class_suffix}').execute()
        except HttpError as e:
            if e.status_code == 404:
                print(f'Class {issuer_id}.{class_suffix} not found!')
                return f'{issuer_id}.{class_suffix}'
            else:
                # Something else went wrong...
                print(e.error_details)
                return f'{issuer_id}.{class_suffix}'

        # Class exists
        updated_class = response

        # Update the class by adding a homepage
        updated_class['homepageUri'] = {
            'uri': 'https://developers.google.com/wallet',
            'description': 'Homepage description'
        }

        # Note: reviewStatus must be 'UNDER_REVIEW' or 'DRAFT' for updates
        updated_class['reviewStatus'] = 'UNDER_REVIEW'

        response = self.client.eventticketclass().update(
            resourceId=f'{issuer_id}.{class_suffix}',
            body=updated_class).execute()

        print('Class update response')
        print(response)

        return f'{issuer_id}.{class_suffix}'

    # [END updateClass]

    # [START patchClass]
    def patch_class(self, issuer_id: str, class_suffix: str) -> str:
        """Patch a class.

        The PATCH method supports patch semantics.

        Args:
            issuer_id (str): The issuer ID being used for this request.
            class_suffix (str): Developer-defined unique ID for this pass class.

        Returns:
            The pass class ID: f"{issuer_id}.{class_suffix}"
        """

        # Check if the class exists
        try:
            response = self.client.eventticketclass().get(resourceId=f'{issuer_id}.{class_suffix}').execute()
        except HttpError as e:
            if e.status_code == 404:
                print(f'Class {issuer_id}.{class_suffix} not found!')
                return f'{issuer_id}.{class_suffix}'
            else:
                # Something else went wrong...
                print(e.error_details)
                return f'{issuer_id}.{class_suffix}'

        # Patch the class by adding a homepage
        patch_body = {
            'homepageUri': {
                'uri': 'https://developers.google.com/wallet',
                'description': 'Homepage description'
            },

            # Note: reviewStatus must be 'UNDER_REVIEW' or 'DRAFT' for patches
            'reviewStatus': 'UNDER_REVIEW'
        }

        response = self.client.eventticketclass().patch(
            resourceId=f'{issuer_id}.{class_suffix}',
            body=patch_body).execute()

        print('Class patch response')
        print(response)

        return f'{issuer_id}.{class_suffix}'

    # [END patchClass]

    # [START addMessageClass]
    def add_class_message(self, issuer_id: str, class_suffix: str, header: str,
                          body: str) -> str:
        """Add a message to a pass class.

        Args:
            issuer_id (str): The issuer ID being used for this request.
            class_suffix (str): Developer-defined unique ID for this pass class.
            header (str): The message header.
            body (str): The message body.

        Returns:
            The pass class ID: f"{issuer_id}.{class_suffix}"
        """

        # Check if the class exists
        try:
            response = self.client.eventticketclass().get(resourceId=f'{issuer_id}.{class_suffix}').execute()
        except HttpError as e:
            if e.status_code == 404:
                print(f'Class {issuer_id}.{class_suffix} not found!')
                return f'{issuer_id}.{class_suffix}'
            else:
                # Something else went wrong...
                print(e.error_details)
                return f'{issuer_id}.{class_suffix}'

        response = self.client.eventticketclass().addmessage(
            resourceId=f'{issuer_id}.{class_suffix}',
            body={'message': {
                'header': header,
                'body': body
            }}).execute()

        print('Class addMessage response')
        print(response)

        return f'{issuer_id}.{class_suffix}'

    # [END addMessageClass]

    # [START createObject]
    def create_object(self, issuer_id: str, class_suffix: str,
                      object_suffix: str, data: dict) -> dict:
        """Create an object.

        Args:
            issuer_id (str): The issuer ID being used for this request.
            class_suffix (str): Developer-defined unique ID for the pass class.
            object_suffix (str): Developer-defined unique ID for the pass object.

        Returns:
            The pass object ID: f"{issuer_id}.{object_suffix}"
        """

        response_details = {
            'object_id': f"{issuer_id}.{object_suffix}",
            'status': 'unknown',
            'message': '',
            "has_error": True
        }

        # Check if the object exists
        try:
            self.client.eventticketobject().get(resourceId=f'{issuer_id}.{object_suffix}').execute()
        except HttpError as e:
            if e.status_code == 400:
                return {
                    'status': 'invalid_request',
                    'message': 'Invalid resource ID.',
                    'error': e.error_details,
                    "has_error": True
                }

            if e.status_code != 404:
                # Something else went wrong...
                response_details['error'] = e.error_details
                response_details['status'] = 'error'
                response_details['message'] = 'An error occurred while checking the object existence.'
                response_details["has_error"] = True
                return response_details
        else:
            response_details['status'] = 'exists'
            response_details['message'] = f'Object {response_details["object_id"]} already exists!'
            response_details["has_error"] = True
            return response_details

        # See link below for more information on required properties
        # https://developers.google.com/wallet/tickets/events/rest/v1/eventticketobject
        new_object = {
            'id': f'{issuer_id}.{object_suffix}',
            'classId': f'{issuer_id}.{class_suffix}',
            'state': 'ACTIVE',
            'heroImage': {
                'sourceUri': {
                    'uri': data["banner"]
                },
                'contentDescription': {
                    'defaultValue': {
                        'language': 'en-US',
                        'value': 'By selecting Place Order, I agree to all Terms and Conditions'
                    }
                }
            },
            "logoImage": {
                'sourceUri': {
                    'uri': data["banner"]
                },
            },
            'textModulesData': [{
                'header': data["header_text"],
                'body': data["body_text"],
                'id': 'TEXT_MODULE_ID'
            }],
            'linksModuleData': {
                'uris': [{
                    'uri': data["google_map_url"],
                    'description': 'Link module URI description',
                    'id': 'LINK_MODULE_URI_ID'
                }, {
                    'uri': f'tel:{data["phone_number"]}',
                    'description': 'Link module tel description',
                    'id': 'LINK_MODULE_TEL_ID'
                }]
            },
            'imageModulesData': [{
                'mainImage': {
                    'sourceUri': {
                        'uri': data["main_image"]
                    },
                    'contentDescription': {
                        'defaultValue': {
                            'language': 'en-US',
                            'value': 'Image module description'
                        }
                    }
                },
                'id': 'IMAGE_MODULE_ID'
            }],
            'barcode': {
                'type': 'QR_CODE',
                'value': 'QR code'
            },
            'locations': [{
                'latitude': 37.424015499999996,
                'longitude': -122.09259560000001
            }],
            'seatInfo': {
                'seat': {
                    'defaultValue': {
                        'language': 'en-US',
                        'value': f'{data["seat"]["seat_no"]}'
                    }
                },
                'row': {
                    'defaultValue': {
                        'language': 'en-US',
                        'value': f'{data["seat"]["row"]}'
                    }
                },
                'section': {
                    'defaultValue': {
                        'language': 'en-US',
                        'value': f'{data["section"]}'
                    }
                },
                'gate': {
                    'defaultValue': {
                        'language': 'en-US',
                        'value': f'{data["gate"]}'
                    }
                }
            },
            'ticketHolderName': f'{data['ticket_holder_name']}',
            'ticketNumber': f'{data['ticket_number']}'
        }

        # Create the object

        try:
            response = self.client.eventticketobject().insert(body=new_object).execute()
            response_details['status'] = 'created'
            response_details['message'] = 'Object created successfully.'
            response_details['response'] = response
            response_details["has_error"] = False

        except HttpError as e:
            if e.status_code == 404:
                response_details['status'] = 'class_not_found'
                response_details['message'] = f'Wallet Object Class {issuer_id}.{class_suffix} not found.'
                response_details["has_error"] = True
                return response_details

        return response_details

    # [END createObject]

    # [START updateObject]
    def update_object(self, issuer_id: str, object_suffix: str) -> str:
        """Update an object.

        **Warning:** This replaces all existing object attributes!

        Args:
            issuer_id (str): The issuer ID being used for this request.
            object_suffix (str): Developer-defined unique ID for the pass object.

        Returns:
            The pass object ID: f"{issuer_id}.{object_suffix}"
        """

        # Check if the object exists
        try:
            response = self.client.eventticketobject().get(resourceId=f'{issuer_id}.{object_suffix}').execute()
        except HttpError as e:
            if e.status_code == 404:
                print(f'Object {issuer_id}.{object_suffix} not found!')
                return f'{issuer_id}.{object_suffix}'
            else:
                # Something else went wrong...
                print(e.error_details)
                return f'{issuer_id}.{object_suffix}'

        # Object exists
        updated_object = response

        # Update the object by adding a link
        new_link = {
            'uri': 'https://developers.google.com/wallet',
            'description': 'New link description'
        }
        if not updated_object.get('linksModuleData'):
            updated_object['linksModuleData'] = {'uris': []}
        updated_object['linksModuleData']['uris'].append(new_link)

        response = self.client.eventticketobject().update(
            resourceId=f'{issuer_id}.{object_suffix}',
            body=updated_object).execute()

        print('Object update response')
        print(response)

        return f'{issuer_id}.{object_suffix}'

        # [END updateObject]

    # [START patchObject]
    def patch_object(self, issuer_id: str, object_suffix: str) -> str:
        """Patch an object.

        Args:
            issuer_id (str): The issuer ID being used for this request.
            object_suffix (str): Developer-defined unique ID for the pass object.

        Returns:
            The pass object ID: f"{issuer_id}.{object_suffix}"
        """

        # Check if the object exists
        try:
            response = self.client.eventticketobject().get(resourceId=f'{issuer_id}.{object_suffix}').execute()
        except HttpError as e:
            if e.status_code == 404:
                print(f'Object {issuer_id}.{object_suffix} not found!')
                return f'{issuer_id}.{object_suffix}'
            else:
                # Something else went wrong...
                print(e.error_details)
                return f'{issuer_id}.{object_suffix}'

        # Object exists
        existing_object = response

        # Patch the object by adding a link
        patch_body = {}
        new_link = {
            'uri': 'https://developers.google.com/wallet',
            'description': 'New link description'
        }

        if existing_object.get('linksModuleData'):
            patch_body['linksModuleData'] = existing_object['linksModuleData']
        else:
            patch_body['linksModuleData'] = {'uris': []}
        patch_body['linksModuleData']['uris'].append(new_link)

        response = self.client.eventticketobject().patch(
            resourceId=f'{issuer_id}.{object_suffix}',
            body=patch_body).execute()

        print('Object patch response')
        print(response)

        return f'{issuer_id}.{object_suffix}'

    # [END patchObject]

    # [START expireObject]
    def expire_object(self, issuer_id: str, object_suffix: str) -> str:
        """Expire an object.

        Sets the object's state to Expired. If the valid time interval is
        already set, the pass will expire automatically up to 24 hours after.

        Args:
            issuer_id (str): The issuer ID being used for this request.
            object_suffix (str): Developer-defined unique ID for the pass object.

        Returns:
            The pass object ID: f"{issuer_id}.{object_suffix}"
        """

        # Check if the object exists
        try:
            response = self.client.eventticketobject().get(resourceId=f'{issuer_id}.{object_suffix}').execute()
        except HttpError as e:
            if e.status_code == 404:
                print(f'Object {issuer_id}.{object_suffix} not found!')
                return f'{issuer_id}.{object_suffix}'
            else:
                # Something else went wrong...
                print(e.error_details)
                return f'{issuer_id}.{object_suffix}'

        # Patch the object, setting the pass as expired
        patch_body = {'state': 'EXPIRED'}

        response = self.client.eventticketobject().patch(
            resourceId=f'{issuer_id}.{object_suffix}',
            body=patch_body).execute()

        print('Object expiration response')
        print(response)

        return f'{issuer_id}.{object_suffix}'

    # [END expireObject]

    # [START addMessageObject]
    def add_object_message(self, issuer_id: str, object_suffix: str,
                           header: str, body: str) -> str:
        """Add a message to a pass object.

        Args:
            issuer_id (str): The issuer ID being used for this request.
            object_suffix (str): Developer-defined unique ID for this pass object.
            header (str): The message header.
            body (str): The message body.

        Returns:
            The pass class ID: f"{issuer_id}.{class_suffix}"
        """

        # Check if the object exists
        try:
            response = self.client.eventticketobject().get(resourceId=f'{issuer_id}.{object_suffix}').execute()
        except HttpError as e:
            if e.status_code == 404:
                print(f'Object {issuer_id}.{object_suffix} not found!')
                return f'{issuer_id}.{object_suffix}'
            else:
                # Something else went wrong...
                print(e.error_details)
                return f'{issuer_id}.{object_suffix}'

        response = self.client.eventticketobject().addmessage(
            resourceId=f'{issuer_id}.{object_suffix}',
            body={'message': {
                'header': header,
                'body': body
            }}).execute()

        print('Object addMessage response')
        print(response)

        return f'{issuer_id}.{object_suffix}'

    # [END addMessageObject]

    # [START jwtNew]
    def create_jwt_new_objects(self, issuer_id: str, class_suffix: str,
                               object_suffix: str) -> str:
        """Generate a signed JWT that creates a new pass class and object.

        When the user opens the "Add to Google Wallet" URL and saves the pass to
        their wallet, the pass class and object defined in the JWT are
        created. This allows you to create multiple pass classes and objects in
        one API call when the user saves the pass to their wallet.

        Args:
            issuer_id (str): The issuer ID being used for this request.
            class_suffix (str): Developer-defined unique ID for the pass class.
            object_suffix (str): Developer-defined unique ID for the pass object.

        Returns:
            An "Add to Google Wallet" link.
        """

        # See link below for more information on required properties
        # https://developers.google.com/wallet/tickets/events/rest/v1/eventticketclass
        new_class = {
            'id': f'{issuer_id}.{class_suffix}',
            'issuerName': 'Issuer name',
            'reviewStatus': 'UNDER_REVIEW',
            'eventName': {
                'defaultValue': {
                    'language': 'en-US',
                    'value': 'my event 025415'
                }
            }
        }

        # See link below for more information on required properties
        # https://developers.google.com/wallet/tickets/events/rest/v1/eventticketobject
        new_object = {
            'id': f'{issuer_id}.{object_suffix}',
            'classId': f'{issuer_id}.{class_suffix}',
            'state': 'ACTIVE',
            'heroImage': {
                'sourceUri': {
                    'uri':
                        'https://caribbeanairforce.com/wp-content/uploads/2024/04/2.png'
                },
                'contentDescription': {
                    'defaultValue': {
                        'language': 'en-US',
                        'value': 'Hero image description'
                    }
                }
            },
            'textModulesData': [{
                'header': 'Text module header',
                'body': 'Text module body',
                'id': 'TEXT_MODULE_ID'
            }],
            'linksModuleData': {
                'uris': [{
                    'uri': 'http://maps.google.com/',
                    'description': 'Link module URI description',
                    'id': 'LINK_MODULE_URI_ID'
                }, {
                    'uri': 'tel:6505555555',
                    'description': 'Link module tel description',
                    'id': 'LINK_MODULE_TEL_ID'
                }]
            },
            'imageModulesData': [{
                'mainImage': {
                    'sourceUri': {
                        'uri':
                            'http://farm4.staticflickr.com/3738/12440799783_3dc3c20606_b.jpg'
                    },
                    'contentDescription': {
                        'defaultValue': {
                            'language': 'en-US',
                            'value': 'Image module description'
                        }
                    }
                },
                'id': 'IMAGE_MODULE_ID'
            }],
            'barcode': {
                'type': 'QR_CODE',
                'value': 'QR code'
            },
            'locations': [{
                'latitude': 37.424015499999996,
                'longitude': -122.09259560000001
            }],
            'seatInfo': {
                'seat': {
                    'defaultValue': {
                        'language': 'en-US',
                        'value': '42'
                    }
                },
                'row': {
                    'defaultValue': {
                        'language': 'en-US',
                        'value': 'G3'
                    }
                },
                'section': {
                    'defaultValue': {
                        'language': 'en-US',
                        'value': '5'
                    }
                },
                'gate': {
                    'defaultValue': {
                        'language': 'en-US',
                        'value': 'A'
                    }
                }
            },
            'ticketHolderName': 'Ticket holder name',
            'ticketNumber': 'Ticket number'
        }

        # Create the JWT claims
        claims = {
            'iss': self.credentials.service_account_email,
            'aud': 'google',
            'origins': ['www.example.com'],
            'typ': 'savetowallet',
            'payload': {
                # The listed classes and objects will be created
                'eventTicketClasses': [new_class],
                'eventTicketObjects': [new_object]
            }
        }

        # The service account credentials are used to sign the JWT
        signer = crypt.RSASigner.from_service_account_file(self.key_file_path)
        token = jwt.encode(signer, claims).decode('utf-8')

        print('Add to Google Wallet link')
        print(f'https://pay.google.com/gp/v/save/{token}')

        return f'https://pay.google.com/gp/v/save/{token}'

    # [END jwtNew]

    # [START jwtExisting]
    def create_jwt_existing_objects(self, issuer_id: str, object_suffix: str, class_suffix: str) -> dict:
        """Generate a signed JWT that references an existing pass object.

        When the user opens the "Add to Google Wallet" URL and saves the pass to
        their wallet, the pass objects defined in the JWT are added to the
        user's Google Wallet app. This allows the user to save multiple pass
        objects in one API call.

        The objects to add must follow the below format:

        {
            'id': 'ISSUER_ID.OBJECT_SUFFIX',
            'classId': 'ISSUER_ID.CLASS_SUFFIX'
        }

        Args:
            issuer_id (str): The issuer ID being used for this request.

        Returns:
            An "Add to Google Wallet" link
        """

        # Multiple pass types can be added at the same time
        # At least one type must be specified in the JWT claims
        # Note: Make sure to replace the placeholder class and object suffixes
        objects_to_add = {
            # Event tickets
            'eventTicketObjects': [{
                'id': f'{issuer_id}.{object_suffix}',
                'classId': f'{issuer_id}.{class_suffix}'
            }],

            # Boarding passes
            # 'flightObjects': [{
            #     'id': f'{issuer_id}.FLIGHT_OBJECT_SUFFIX',
            #     'classId': f'{issuer_id}.FLIGHT_CLASS_SUFFIX'
            # }],

            # Generic passes
            # 'genericObjects': [{
            #     'id': f'{issuer_id}.GENERIC_OBJECT_SUFFIX',
            #     'classId': f'{issuer_id}.GENERIC_CLASS_SUFFIX'
            # }],

            # Gift cards
            # 'giftCardObjects': [{
            #     'id': f'{issuer_id}.GIFT_CARD_OBJECT_SUFFIX',
            #     'classId': f'{issuer_id}.GIFT_CARD_CLASS_SUFFIX'
            # }],

            # Loyalty cards
            # 'loyaltyObjects': [{
            #     'id': f'{issuer_id}.LOYALTY_OBJECT_SUFFIX',
            #     'classId': f'{issuer_id}.LOYALTY_CLASS_SUFFIX'
            # }],

            # Offers
            # 'offerObjects': [{
            #     'id': f'{issuer_id}.OFFER_OBJECT_SUFFIX',
            #     'classId': f'{issuer_id}.OFFER_CLASS_SUFFIX'
            # }],

            # Transit passes
            # 'transitObjects': [{
            #     'id': f'{issuer_id}.TRANSIT_OBJECT_SUFFIX',
            #     'classId': f'{issuer_id}.TRANSIT_CLASS_SUFFIX'
            # }]
        }

        # Create the JWT claims
        claims = {
            'iss': self.credentials.service_account_email,
            'aud': 'google',
            'origins': ['www.example.com'],
            'typ': 'savetowallet',
            'payload': objects_to_add
        }

        # The service account credentials are used to sign the JWT
        signer = crypt.RSASigner.from_service_account_file(self.key_file_path)
        token = jwt.encode(signer, claims).decode('utf-8')

        # Generate the Add to Google Wallet link
        wallet_link = f'https://pay.google.com/gp/v/save/{token}'

        return {
            "status": "success",
            "message": "JWT successfully generated.",
            "wallet_link": wallet_link
        }

    # [END jwtExisting]

    # [START batch]
    def batch_create_objects(self, issuer_id: str, class_suffix: str):
        """Batch create Google Wallet objects from an existing class.

        The request body will be a multiline string. See below for information.

        https://cloud.google.com/compute/docs/api/how-tos/batch#example

        Args:
            issuer_id (str): The issuer ID being used for this request.
            class_suffix (str): Developer-defined unique ID for this pass class.
        """
        batch = self.client.new_batch_http_request()

        # Example: Generate three new pass objects
        for _ in range(3):
            # Generate a random object suffix
            object_suffix = str(uuid.uuid4()).replace('[^\\w.-]', '_')

            # See link below for more information on required properties
            # https://developers.google.com/wallet/tickets/events/rest/v1/eventticketobject
            batch_object = {
                'id': f'{issuer_id}.{object_suffix}',
                'classId': f'{issuer_id}.{class_suffix}',
                'state': 'ACTIVE',
                'heroImage': {
                    'sourceUri': {
                        'uri':
                            'https://farm4.staticflickr.com/3723/11177041115_6e6a3b6f49_o.jpg'
                    },
                    'contentDescription': {
                        'defaultValue': {
                            'language': 'en-US',
                            'value': 'Hero image description'
                        }
                    }
                },
                'textModulesData': [{
                    'header': 'Text module header',
                    'body': 'Text module body',
                    'id': 'TEXT_MODULE_ID'
                }],
                'linksModuleData': {
                    'uris': [{
                        'uri': 'http://maps.google.com/',
                        'description': 'Link module URI description',
                        'id': 'LINK_MODULE_URI_ID'
                    }, {
                        'uri': 'tel:6505555555',
                        'description': 'Link module tel description',
                        'id': 'LINK_MODULE_TEL_ID'
                    }]
                },
                'imageModulesData': [{
                    'mainImage': {
                        'sourceUri': {
                            'uri':
                                'http://farm4.staticflickr.com/3738/12440799783_3dc3c20606_b.jpg'
                        },
                        'contentDescription': {
                            'defaultValue': {
                                'language': 'en-US',
                                'value': 'Image module description'
                            }
                        }
                    },
                    'id': 'IMAGE_MODULE_ID'
                }],
                'barcode': {
                    'type': 'QR_CODE',
                    'value': 'QR code'
                },
                'locations': [{
                    'latitude': 37.424015499999996,
                    'longitude': -122.09259560000001
                }],
                'seatInfo': {
                    'seat': {
                        'defaultValue': {
                            'language': 'en-US',
                            'value': '42'
                        }
                    },
                    'row': {
                        'defaultValue': {
                            'language': 'en-US',
                            'value': 'G3'
                        }
                    },
                    'section': {
                        'defaultValue': {
                            'language': 'en-US',
                            'value': '5'
                        }
                    },
                    'gate': {
                        'defaultValue': {
                            'language': 'en-US',
                            'value': 'A'
                        }
                    }
                },
                'ticketHolderName': 'Ticket holder name',
                'ticketNumber': 'Ticket number'
            }

            batch.add(self.client.eventticketobject().insert(body=batch_object))

        # Invoke the batch API calls
        response = batch.execute()

        print('Batch complete')

    # [END batch]

# ticket = DemoEventTicket(credentials="./credentials.json")
#
# issuer_id = "3388000000022797841"
# class_suffix = "stereo-sonic-reunion132"
# object_suffix = "stereo-sonic-reunion-12"
#
# a = ticket.create_class(issuer_id=issuer_id, class_suffix=class_suffix)
# b = ticket.create_object(issuer_id=issuer_id, class_suffix=class_suffix, object_suffix=object_suffix)
# c = ticket.create_jwt_existing_objects(issuer_id=issuer_id, class_suffix=class_suffix, object_suffix=object_suffix)
#
# print(a)
# print(b)
# print(c)
