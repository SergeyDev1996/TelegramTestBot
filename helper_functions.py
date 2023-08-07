import random

from config import redis_db


# Function to check if a user is an admin
def is_user_admin(user_id: str):
    return redis_db.sismember('admin_users', user_id)


def generate_random_8digit():
    return random.randint(10000000, 99999999)


def add_admin_user(user_id: str):
    # Add the user ID to the "admin_users" set
    redis_db.sadd('admin_users', user_id)
