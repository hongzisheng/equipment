from flask import Flask
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure, ServerSelectionTimeoutError

current_app: Flask | None = None


def connect_mongodb():
    config = current_app.config
    host = config["MONGODB_HOST"]
    port = config["MONGODB_PORT"]
    username = config.get("MONGODB_USER", "")
    password = config.get("MONGODB_PASSWORD", "")

    if username and password:
        connection_string = f"mongodb://{username}:{password}@{host}:{port}/"
    else:
        connection_string = f"mongodb://{host}:{port}/"

    return MongoClient(connection_string, serverSelectionTimeoutMS=5000)


def get_connected_mongodb_database():
    client = connect_mongodb()
    return client[current_app.config["MONGODB_DATABASE"]]


def check_mongodb_status(app: Flask):
    global current_app
    current_app = app
    try:
        client = connect_mongodb()
        client.admin.command("ping")
        client.close()
        current_app.logger.info("MongoDB Connect Status: SUCCESS")
        return True
    except ConnectionFailure as e:
        current_app.logger.error(f"MongoDB Connect Status: FAILED, cannot connect to MongoDB - {str(e)}")
        return False
    except OperationFailure as e:
        current_app.logger.error(f"MongoDB Connect Status: FAILED, operation failed - {str(e)}")
        return False
    except ServerSelectionTimeoutError as e:
        current_app.logger.error(f"MongoDB Connect Status: FAILED, connection timeout - {str(e)}")
        return False
    except Exception as e:
        current_app.logger.error(f"MongoDB Connect Status: FAILED, {str(e)}")
        return False


def get_reports_collection():
    database = get_connected_mongodb_database()
    return database[current_app.config["MONGODB_REPORTS_COLLECTION"]]


def get_extract_result_collection():
    database = get_connected_mongodb_database()
    return database[current_app.config["MONGODB_EXTRACT_RESULT_COLLECTION"]]


def get_event_link_collection():
    database = get_connected_mongodb_database()
    return database[current_app.config["MONGODB_EVENT_LINK_COLLECTION"]]


def get_sub_graph_collection():
    database = get_connected_mongodb_database()
    return database[current_app.config["MONGODB_SUB_GRAPH_COLLECTION"]]


def get_event_link_rules_collection():
    database = get_connected_mongodb_database()
    return database[current_app.config["MONGODB_EVENT_LINK_RULES_COLLECTION"]]
