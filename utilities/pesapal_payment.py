import os
from datetime import datetime

import json
import flask
import requests


def split_full_name(full_name):
    # Split the name by spaces
    name_parts = full_name.split()

    # Check how many parts the name has
    if len(name_parts) == 2:  # First and last name only
        first_name, last_name = name_parts
        middle_name = ""
    elif len(name_parts) > 2:  # First, middle, and last name
        first_name = name_parts[0]
        middle_name = " ".join(name_parts[1:-1])
        last_name = name_parts[-1]
    else:
        first_name = full_name
        middle_name = last_name = ""

    return first_name, middle_name, last_name


def get_access_token():
    """
    Retrieves 5 minute access token from PesaPal.
    :return: dict - Access token response
    """
    headers = {"accept": "text/plain", "content-type": "application/json"}
    post_data = {
        "consumer_key": flask.current_app.config["PESAPAL_CONSUMER_KEY"],
        "consumer_secret": flask.current_app.config["PESAPAL_CONSUMER_SECRET"],
    }
    end_point = os.path.join(
        flask.current_app.config["PESAPAL_BASE_URL"], "api/Auth/RequestToken"
    )
    return make_request(end_point, headers, post_data)


def get_registered_ipn(access_token):
    """
    :param access_token: Access token received from get_access_token
    :return: dict - Registered IPN response
    """
    headers = {
        "accept": "text/plain",
        "content-type": "application/json",
        "authorization": f"Bearer {access_token}",
    }
    end_point = os.path.join(
        flask.current_app.config["PESAPAL_BASE_URL"], "api/URLSetup/GetIpnList"
    )
    return make_request(end_point, headers)


def get_notification_id(access_token, callback_url):
    """
    :param access_token: Access token received from get_access_token
    :param callback_url: Callback URL for IPN
    :return: Notification ID response
    """
    headers = {
        "accept": "text/plain",
        "content-type": "application/json",
        "authorization": f"Bearer {access_token}",
    }
    post_data = {"ipn_notification_type": "GET", "url": callback_url}
    end_point = os.path.join(
        flask.current_app.config["PESAPAL_BASE_URL"],
        "api/URLSetup/RegisterIPN",
    )
    return make_request(end_point, headers, post_data)


def get_merchant_order_url(details, access_token, subscription_details=None):
    """
    :param details: Dict object containing order details
    :param access_token: Access token received from get_access_token
    :param subscription_details: Dict object containing subscription details

    :return: Merchant order URL response
    """
    headers = {
        "accept": "text/plain",
        "content-type": "application/json",
        "authorization": f"Bearer {access_token}",
    }
    post_data = {
        "language": details.get("language", "EN"),
        "currency": details.get("currency", "KES"),
        "amount": details.get("amount", 1.0),
        "id": details.get("id", datetime.now().strftime("%Y%m%d%H%M%S")),
        "description": details.get("description", ""),
        "billing_address": {
            "country_code": "KE",
            "phone_number": details.get("phone_number", ""),
            "email_address": details.get("email_address", ""),
            "first_name": details.get("first_name", ""),
            "middle_name": details.get("middle_name", ""),
            "last_name": details.get("last_name", ""),
            "line_1": details.get("line_1", ""),
            "line_2": details.get("line_2", ""),
            "city": details.get("city", ""),
            "state": details.get("state", ""),
            "postal_code": details.get("postal_code", ""),
            "zip_code": details.get("zip_code", ""),
        },
        "callback_url": details.get("callback_url"),
        "notification_id": details.get("notification_id"),
        "terms_and_conditions_id": details.get("terms_and_conditions_id"),
    }

    # Check if subscription is activated
    if subscription_details:
        post_data.update(subscription_details)

    # Send request
    end_point = os.path.join(
        flask.current_app.config["PESAPAL_BASE_URL"],
        "api/Transactions/SubmitOrderRequest",
    )
    return make_request(end_point, headers, post_data)


def get_transaction_status(order_tracking_id, access_token):
    """
    :param order_tracking_id: Order tracking ID from get_merchant_order_url
    :param access_token: Access token received from get_access_token
    :return: Transaction status response
    """
    headers = {
        "accept": "text/plain",
        "content-type": "application/json",
        "authorization": f"Bearer {access_token}",
    }
    end_point = (
        flask.current_app.config["PESAPAL_BASE_URL"]
        + "/api/Transactions/GetTransactionStatus?"
        + f"orderTrackingId={order_tracking_id}"
    )
    return make_request(end_point, headers)


def make_request(url, headers, post_data=None):
    """
    Helper function to make HTTP requests using requests module.

    :param url: string - Endpoint URL
    :param headers: dict - HTTP headers
    :param post_data: Data to be posted

    :return: dict - Decoded JSON response
    """
    try:
        if post_data:
            response = requests.post(
                url, headers=headers, data=json.dumps(post_data)
            )
        else:
            response = requests.get(url, headers=headers)

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
