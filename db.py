import collections
import json
import os
import random
import sqlite3
import uuid
from datetime import datetime

HOME_DIR = os.environ.get("HOME_DIR")
if HOME_DIR == None:
    raise Exception("HOME_DIR environment variable not set")

WORDS_FILE = os.path.join(HOME_DIR, "rave-training/words.txt")
DB_PATH = os.path.join(HOME_DIR, "houseparty.db")
TIME_FMT = "%Y-%m-%d"
TIME_FMT_SYSTEM = "%Y%m%d%H%M"

"""
The database schema is as follows:
- WorkOrder Table
    - WorkOrderId
    - WorkOrderStatus
    - TrainingJobId
    - UserId
    - DatasetId
    - PriceId
    - StripeTransactionId
- TrainingJob Table
    - TrainingJobId
    - TrainingJobName
    - TrainingJobStatus
    - OutputS3LocationId
    - DatasetId
    - InstanceId
    - PriceId
- S3Location Table
    - S3LocationId
    - BucketName
    - ObjectName
- User Table
    - UserId
    - UserName
    - UserEmailAddress
- Dataset Table
    - DatasetId
    - DatasetS3LocationId
- Instance Table
    - InstanceId
    - LambdaInstanceId
- Price Table
    - PriceId
    - PriceMetadata

- WorkOrderStatus is an enum with the following possible values:
    - CREATED
    - PAID
    - FAILED
    - CANCELLED
    - COMPLETED
- TrainingJobStatus is an enum with the following possible values:
    - PENDING
    - RUNNING
    - COMPLETED
    - FAILED
    - CANCELLED
"""
WORK_ORDER_STATUS_CREATED = "CREATED"
WORK_ORDER_STATUS_PAID = "PAID"
WORK_ORDER_STATUS_FAILED = "FAILED"
WORK_ORDER_STATUS_CANCELLED = "CANCELLED"
WORK_ORDER_STATUS_COMPLETED = "COMPLETED"
WORK_ORDER_STATUS_LIST = [
    WORK_ORDER_STATUS_CREATED,
    WORK_ORDER_STATUS_PAID,
    WORK_ORDER_STATUS_FAILED,
    WORK_ORDER_STATUS_CANCELLED,
    WORK_ORDER_STATUS_COMPLETED,
]
TRAINING_JOB_STATUS_PENDING = "PENDING"
TRAINING_JOB_STATUS_RUNNING = "RUNNING"
TRAINING_JOB_STATUS_COMPLETED = "COMPLETED"
TRAINING_JOB_STATUS_FAILED = "FAILED"
TRAINING_JOB_STATUS_CANCELLED = "CANCELLED"
TRAINING_JOB_STATUS_LIST = [
    TRAINING_JOB_STATUS_PENDING,
    TRAINING_JOB_STATUS_RUNNING,
    TRAINING_JOB_STATUS_COMPLETED,
    TRAINING_JOB_STATUS_FAILED,
    TRAINING_JOB_STATUS_CANCELLED,
]


def create_db():
    with sqlite3.connect(DB_PATH) as db_connection:
        cursor = db_connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS WorkOrder (
                CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                WorkOrderId TEXT PRIMARY KEY,
                WorkOrderStatus TEXT,
                TrainingJobId TEXT,
                UserId TEXT,
                DatasetId TEXT,
                PriceId TEXT,
                StripeTransactionId TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS TrainingJob (
                CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                TrainingJobId TEXT PRIMARY KEY,
                TrainingJobName TEXT,
                TrainingJobStatus TEXT,
                TrainingJobSettings TEXT,
                OutputS3LocationId TEXT,
                DatasetId TEXT,
                InstanceId TEXT
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS S3Location (
                CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                S3LocationId TEXT PRIMARY KEY,
                BucketName TEXT,
                ObjectName TEXT
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS User (
                CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                UserId TEXT PRIMARY KEY,
                UserEmailAddress TEXT
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Dataset (
                CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                DatasetId TEXT PRIMARY KEY,
                DatasetS3LocationId TEXT
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Instance (
                CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                InstanceId TEXT PRIMARY KEY,
                LambdaInstanceId TEXT
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Price (
                CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                PriceId TEXT PRIMARY KEY,
                PriceMetadata TEXT
            )
        """
        )
        db_connection.commit()


def query(q):
    db_connection = sqlite3.connect(DB_PATH)
    cursor = db_connection.cursor()
    result = cursor.execute(q).fetchall()
    columns = [description[0] for description in cursor.description]
    db_connection.close()
    result_dicts = []
    for row in result:
        row_dict = {}
        for i in range(len(row)):
            row_dict[columns[i]] = row[i]
        result_dicts.append(row_dict)
    return result_dicts


def update(query, params):
    db_connection = sqlite3.connect(DB_PATH)
    cursor = db_connection.cursor()
    cursor.execute(query, params)
    db_connection.commit()
    db_connection.close()


def list_work_orders():
    return query("""select * from WorkOrder;""")


def get_unique_work_order_id():
    work_orders = list_work_orders()
    work_order_ids = [work_order["WorkOrderId"] for work_order in work_orders]
    work_order_id = str(uuid.uuid4())
    while work_order_id in work_order_ids:
        work_order_id = str(uuid.uuid4())
    return work_order_id


def insert_work_order(work_order_status, training_job_id, dataset_id, price_id):
    work_order_id = get_unique_work_order_id()
    update(
        """
        INSERT INTO WorkOrder (
            WorkOrderId,
            WorkOrderStatus,
            TrainingJobId,
            DatasetId,
            PriceId
        )
        VALUES (?, ?, ?, ?, ?);
    """,
        (work_order_id, work_order_status, training_job_id, dataset_id, price_id),
    )
    return work_order_id


def create_work_order(training_job_id, dataset_id, price_id):
    work_order_status = WORK_ORDER_STATUS_CREATED
    worker_order_id = insert_work_order(
        work_order_status, training_job_id, dataset_id, price_id
    )
    return worker_order_id


def get_work_order(work_order_id):
    work_orders = query(
        f"""select * from WorkOrder where WorkOrderId = "{work_order_id}";"""
    )
    if len(work_orders) == 0:
        return None
    else:
        return work_orders[0]


def get_work_order_by_stripe_transaction(stripe_transaction_id):
    work_orders = query(
        f"""select * from WorkOrder where StripeTransactionId = "{stripe_transaction_id}";"""
    )
    if len(work_orders) == 0:
        return None
    else:
        return work_orders[0]


def delete_work_order(work_order_id):
    update("""delete from WorkOrder where WorkOrderId = ?;""", (work_order_id,))
    return work_order_id


def delete_work_order_full(work_order_id):
    work_order = get_work_order(work_order_id)
    if work_order == None:
        return None
    else:
        training_job_id = work_order["TrainingJobId"]
        dataset_id = work_order["DatasetId"]
        price_id = work_order["PriceId"]
        dataset = get_dataset(dataset_id)
        dataset_s3_location_id = dataset["DatasetS3LocationId"]
        training_job = get_training_job(training_job_id)
        output_s3_location_id = training_job["OutputS3LocationId"]

        delete_s3_location(dataset_s3_location_id)
        delete_s3_location(output_s3_location_id)
        delete_training_job(training_job_id)
        delete_dataset(dataset_id)
        delete_price(price_id)
        delete_work_order(work_order_id)
        return work_order_id


def get_random_word():
    with open(WORDS_FILE) as f:
        words = f.readlines()
    return random.choice(words).strip()


def get_random_training_job_name():
    words = [get_random_word() for i in range(4)]
    return "-".join(words)


def get_unique_training_job_name():
    training_jobs = list_training_jobs()
    training_job_names = [
        training_job["TrainingJobName"] for training_job in training_jobs
    ]
    training_job_name = get_random_training_job_name()
    while training_job_name in training_job_names:
        training_job_name = get_random_training_job_name()
    return training_job_name


def get_unique_training_job_id():
    training_jobs = list_training_jobs()
    training_job_ids = [training_job["TrainingJobId"] for training_job in training_jobs]
    training_job_id = str(uuid.uuid4())
    while training_job_id in training_job_ids:
        training_job_id = str(uuid.uuid4())
    return training_job_id


def create_training_job(dataset_id, training_job_settings):
    training_job_id = get_unique_training_job_id()
    training_job_name = get_unique_training_job_name()
    training_job_status = TRAINING_JOB_STATUS_PENDING
    training_job_settings = json.dumps(training_job_settings)
    update(
        """
        INSERT INTO TrainingJob (
            TrainingJobId,
            TrainingJobName,
            TrainingJobStatus,
            TrainingJobSettings,
            DatasetId
        )
        VALUES (?, ?, ?, ?, ?);
        """,
        (
            training_job_id,
            training_job_name,
            training_job_status,
            json.dumps(training_job_settings),
            dataset_id,
        ),
    )
    return training_job_id


def get_training_job(training_job_id):
    training_jobs = query(
        f"""select * from TrainingJob where TrainingJobId = "{training_job_id}";"""
    )
    if len(training_jobs) == 0:
        return None
    else:
        return training_jobs[0]


def update_training_job_status(training_job_id, training_job_status):
    if training_job_status not in TRAINING_JOB_STATUS_LIST:
        raise Exception(f"Invalid training_job_status: {training_job_status}")

    update(
        """
        UPDATE TrainingJob
        SET TrainingJobStatus = ?
        WHERE TrainingJobId = ?;
        """,
        (training_job_status, training_job_id),
    )
    return training_job_id


def delete_training_job(training_job_id):
    update(
        """
        DELETE FROM TrainingJob
        WHERE TrainingJobId = ?;
        """,
        (training_job_id,),
    )
    return training_job_id


def list_training_jobs():
    return query("""select * from TrainingJob;""")


def list_training_jobs_by_status(training_job_status):
    if training_job_status not in TRAINING_JOB_STATUS_LIST:
        raise Exception(f"Invalid training_job_status: {training_job_status}")

    return query(
        f"""select * from TrainingJob where TrainingJobStatus = "{training_job_status}";"""
    )


def get_unique_s3_location_id():
    s3_locations = list_s3_locations()
    s3_location_ids = [s3_location["S3LocationId"] for s3_location in s3_locations]
    s3_location_id = str(uuid.uuid4())
    while s3_location_id in s3_location_ids:
        s3_location_id = str(uuid.uuid4())
    return s3_location_id


def insert_s3_location(bucket_name, object_name):
    s3_location_id = get_unique_s3_location_id()
    update(
        """
        INSERT INTO S3Location (
            S3LocationId,
            BucketName,
            ObjectName
        )
        VALUES (
            ?,
            ?,
            ?
        );
    """,
        (s3_location_id, bucket_name, object_name),
    )
    return s3_location_id


def get_s3_location(s3_location_id):
    return query(
        f"""select * from S3Location where S3LocationId = "{s3_location_id}";"""
    )


def delete_s3_location(s3_location_id):
    update("""delete from S3Location where S3LocationId = ?;""", (s3_location_id,))
    return s3_location_id


def list_s3_locations():
    return query("""select * from S3Location;""")


def get_unique_user_id():
    users = list_users()
    user_ids = [user["UserId"] for user in users]
    user_id = str(uuid.uuid4())
    while user_id in user_ids:
        user_id = str(uuid.uuid4())
    return user_id


def insert_user(user_email_address):
    # first check if user already exists
    user = query(
        """select * from User where UserEmailAddress = ?;""", (user_email_address,)
    )
    if len(user) > 0:
        return user[0]["UserId"]
    # if not, create a new user
    user_id = get_unique_user_id()
    update(
        """
        INSERT INTO User (
            UserId,
            UserEmailAddress
        )
        VALUES (
            ?,
            ?
        );
    """,
        (user_id, user_email_address),
    )
    return user_id


def get_user(user_id):
    return query(f"""select * from User where UserId = "{user_id}";""")


def delete_user(user_id):
    update("""delete from User where UserId = ?;""", (user_id,))
    return user_id


def list_users():
    return query("""select * from User;""")


def get_unique_dataset_id():
    datasets = list_datasets()
    dataset_ids = [dataset["DatasetId"] for dataset in datasets]
    dataset_id = str(uuid.uuid4())
    while dataset_id in dataset_ids:
        dataset_id = str(uuid.uuid4())
    return dataset_id


def insert_dataset(dataset_s3_location_id):
    dataset_id = get_unique_dataset_id()
    update(
        """
        INSERT INTO Dataset (
            DatasetId,
            DatasetS3LocationId
        )
        VALUES (
            ?,
            ?
        );
        """,
        (dataset_id, dataset_s3_location_id),
    )
    return dataset_id


def get_dataset(dataset_id):
    return query(f"""select * from Dataset where DatasetId = "{dataset_id}";""")


def delete_dataset(dataset_id):
    update("""delete from Dataset where DatasetId = ?;""", (dataset_id,))
    return dataset_id


def list_datasets():
    return query("""select * from Dataset;""")


def get_unique_instance_id():
    instances = list_instances()
    instance_ids = [instance["InstanceId"] for instance in instances]
    instance_id = str(uuid.uuid4())
    while instance_id in instance_ids:
        instance_id = str(uuid.uuid4())
    return instance_id


def insert_instance(lambda_instance_id):
    instance_id = get_unique_instance_id()
    update(
        """
        INSERT INTO Instance (
            InstanceId,
            LambdaInstanceId
        )
        VALUES (
            ?,
            ?
        );
        """,
        (instance_id, lambda_instance_id),
    )
    return instance_id


def get_instance(instance_id):
    return query(f"""select * from Instance where InstanceId = "{instance_id}";""")


def delete_instance(instance_id):
    update("""delete from Instance where InstanceId = ?;""", (instance_id,))
    return instance_id


def list_instances():
    return query("""select * from Instance;""")


def get_unique_price_id():
    prices = list_prices()
    price_ids = [price["PriceId"] for price in prices]
    price_id = str(uuid.uuid4())
    while price_id in price_ids:
        price_id = str(uuid.uuid4())
    return price_id


def insert_price(price_metadata):
    price_id = get_unique_price_id()
    update(
        """
        INSERT INTO Price (
            PriceId,
            PriceMetadata
        )
        VALUES (
            ?,
            ?
        );
        """,
        (price_id, json.dumps(price_metadata)),
    )
    return price_id


def get_price(price_id):
    return query(f"""select * from Price where PriceId = "{price_id}";""")


def delete_price(price_id):
    update("""delete from Price where PriceId = ?;""", (price_id,))
    return price_id


def list_prices():
    return query("""select * from Price;""")


def row_to_dict(row):
    pass


def update_dict_recursive(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping) and k in v:
            d[k] = update_dict_recursive(d.get(k, dict()), v)
        else:
            d[k] = v
    return d


def parse_string_to_json_until_list_or_dict(json_data):
    if json_data == "" or json_data == None:
        return None
    while not isinstance(json_data, list) and not isinstance(json_data, dict):
        if json_data == "" or json_data == None:
            return None
        else:
            json_data = json.loads(json_data)
    return json_data
