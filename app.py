import json
import os
import stripe
import boto3
import uuid
import requests
import db
import logging
import random
from botocore.exceptions import ClientError
from flask import Flask, render_template, jsonify, request, redirect

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

BUCKET = "rave-training-data"
BASE_PRICE = 8400
TOTAL_PRICE = 8700
STRIPE_FEE_PERCDNT = 2.9
STRIPE_FEE_FLAT = 30
PRICE_METADATA = {
    "total": TOTAL_PRICE,
    "base_price": BASE_PRICE,
    "stripe_fee_percent": STRIPE_FEE_PERCDNT,
    "stripe_fee_flat": STRIPE_FEE_FLAT,
}

app = Flask(
    __name__, static_folder="public", static_url_path="", template_folder="public"
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/request-upload")
def request_upload():
    filename = str(uuid.uuid4()) + ".mp3"
    response = create_presigned_post(BUCKET, filename)
    dataset_id = create_new_dataset(filename)
    response["datasetId"] = dataset_id
    return jsonify(response)


@app.route("/order", methods=["POST"])
def place_work_order():
    data = json.loads(request.data)
    dataset_id = data["datasetId"]
    training_job_settings = data["trainingJobSettings"]
    training_job_id = db.create_training_job(dataset_id, training_job_settings)
    price_metadata = PRICE_METADATA
    price_id = db.insert_price(price_metadata)
    work_order_id = db.create_work_order(
        training_job_id, dataset_id, price_id
    )
    print("**** work order id", work_order_id)
    training_job = db.get_training_job(training_job_id)
    training_job_name = training_job["TrainingJobName"]
    return jsonify({
        "workOrderId": work_order_id,
        "trainingJobName": training_job_name,
    })


@app.route("/order", methods=["GET"])
def get_work_order_by_stripe_transaction():
    stripe_transaction_id = request.args.get("stripeTransactionId")
    work_order = db.get_work_order_by_stripe_transaction(stripe_transaction_id)
    return redirect("/order/" + work_order["WorkOrderId"])


@app.route("/order/<work_order_id>", methods=["POST"])
def get_work_order(work_order_id):
    pass

@app.route("/test")
def test():
    # test the /order endpoint
    db.create_db()

    data = {
        "trainingJobName": "test",
        "trainingJobSettings": {"config": "v2-wasserstein"},
        "datasetId": "83cd82eb-acb8-4f87-a042-a9c0debcee09"
    }
    response = requests.post("http://localhost:4242/order", json=data)
    return response.text


def create_new_dataset(filename):
    # Create a new dataset in the database
    dataset_s3_location_id = db.insert_s3_location(BUCKET, filename)
    dataset_id = db.insert_dataset(dataset_s3_location_id)
    return dataset_id


def create_presigned_post(
    bucket_name, object_name, fields=None, conditions=None, expiration=3600
):
    """Generate a presigned URL S3 POST request to upload a file
    :param bucket_name: string
    :param object_name: string
    :param fields: Dictionary of prefilled form fields
    :param conditions: List of conditions to include in the policy
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Dictionary with the following keys:
        url: URL to post to
        fields: Dictionary of form fields and values to submit with the POST
    :return: None if error.
    """
    # Generate a presigned S3 POST URL
    s3_client = boto3.client("s3")
    try:
        response = s3_client.generate_presigned_post(
            bucket_name,
            object_name,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=expiration,
        )
    except ClientError as e:
        logging.error(e)
        return None
    # The response contains the presigned URL and required fields
    return response


if __name__ == "__main__":
    app.run(port=4242)
