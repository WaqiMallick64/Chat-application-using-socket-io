from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient, DESCENDING
from werkzeug.security import generate_password_hash
from cryptography.fernet import Fernet
from user import User
from admins import Admin
from dotenv import load_dotenv
import os 

load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)

chat_db = client.get_database("ChatDB")

# Collections
users_collection = chat_db.get_collection("Users")
admins_collection = chat_db.get_collection("admins")
rooms_collection = chat_db.get_collection("rooms")
messages_collection = chat_db.get_collection("messages")

# ------------------ USERS ------------------ #

def save_user(username, email, password):
    password_hash = generate_password_hash(password)
    users_collection.insert_one({
        '_id': username,
        'email': email,
        'password': password_hash
    })

def get_user(username):
    user_data = users_collection.find_one({'_id': username})
    return User(user_data['_id'], user_data['email'], user_data['password']) if user_data else None

# ------------------ ADMINS ------------------ #

def save_admin(username, email, password, admin_type):
    password_hash = generate_password_hash(password)
    admins_collection.insert_one({
        '_id': username,
        'email': email,
        'password': password_hash,
        'admin_type': admin_type  # E.g., 'OrderSupport', 'ProductManager'
    })

def get_admin(username):
    admin_data = admins_collection.find_one({'_id': username})
    return Admin(admin_data['_id'], admin_data['email'], admin_data['password'], admin_data['admin_type']) if admin_data else None

def get_admin_by_type(admin_type):
    return admins_collection.find_one({'admin_type': admin_type})

# ------------------ CHATROOM ------------------ #
def get_room_for_user(user, admin_type):
    # Check if the user already has a room with this admin_type
    existing_room = rooms_collection.find_one({"user_id": user, "admin_type": admin_type})
    if existing_room:
        return existing_room['_id']

    if existing_room:
        return existing_room['_id']
    else:
        return None


def get_or_create_room_for_user(user, admin_type):
    # Check if the user already has a room with this admin_type
    existing_room = rooms_collection.find_one({"user_id": user, "admin_type": admin_type})
    if existing_room:
        return existing_room['_id']

    # Find an available admin for this admin_type
    admin = admins_collection.find_one({"admin_type": admin_type})
    if not admin:
        raise ValueError(f"No admin available for {admin_type}.")

    # Create a new room
    new_room = {
        "user_id": user,
        "admin_username": admin['_id'],
        "admin_type": admin_type,
        "created_at": datetime.utcnow()
    }
    result = rooms_collection.insert_one(new_room)
    return result.inserted_id

"""def get_or_create_room_for_user(user, admin_type):
    existing_room = rooms_collection.find_one({"user_id": user, "admin_type": admin_type})
    if existing_room:
        return existing_room['_id']

    # Get all admins of this type
    admins = list(admins_collection.find({"admin_type": admin_type}))
    if not admins:
        return None

    # Find the least-loaded admin (fewest rooms)
    admin_loads = []
    for admin in admins:
        count = rooms_collection.count_documents({"admin_id": admin['_id']})
        admin_loads.append((admin, count))

    # Sort by load and pick the least loaded
    admin_loads.sort(key=lambda x: x[1])
    selected_admin = admin_loads[0][0]

    # Create the room
    room = {
        "user_id": user,
        "admin_id": selected_admin['_id'],
        "admin_type": admin_type,
        "created_at": datetime.utcnow()
    }
    result = rooms_collection.insert_one(room)
    return result.inserted_id"""


def get_room_for_admin(admin_username, user_username):
    # Admin should only retrieve existing rooms
    existing_room = rooms_collection.find_one({
        "user_id": user_username,
        "admin_username": admin_username
    })
    if existing_room:
        return existing_room['_id']
    else:
        return None




def get_room(room_id):
    return rooms_collection.find_one({'_id': ObjectId(room_id)})

def get_rooms_for_user(user_id):
    return list(rooms_collection.find({'user_id': user_id}))

def get_users_chatted_with_admin(admin_username):
    rooms = rooms_collection.find({'admin_username': admin_username})  # Use admin_username instead of admin
    return [{'user': room['user_id']} for room in rooms]

def get_room_by_user_and_admin_type(username, admin_type):
    return rooms_collection.find_one({'user': username, 'admin_type': admin_type})

def get_room_admin_type(admin_type):
    rooms = rooms_collection.find({'admin_type': admin_type})
    return [{'user': room['user_id']} for room in rooms]



"""def create_user_admin_room(username, admin_type):
    room = {
        'user': username,
        'admin_type': admin_type,
        'name': f"{username}_{admin_type}_room"
    }
    room_id = rooms_collection.insert_one(room).inserted_id
    room['_id'] = room_id
    return room"""


# ------------------ MESSAGES ------------------ #
#------------------  my changes    ------------------#
def get_room_summary(room_id, current_user):
    room_obj_id = ObjectId(room_id)

    # Unread message count (excluding current user)
    unread_count = messages_collection.count_documents({
        'room_id': room_obj_id,
        'sender': {'$ne': current_user},
        'is_read': False
    })

    # Last message
    last_message_doc = messages_collection.find_one(
        {'room_id': room_obj_id},
        sort=[('created_at', DESCENDING)]
    )
    
    if last_message_doc:
        last_message = decrypt_message(last_message_doc['text'])
        last_time = last_message_doc['created_at'].strftime("%d %b, %H:%M")
        last_sender = last_message_doc['sender']
        last_message_read = last_message_doc.get('is_read', True)
    else:
        last_message = None
        last_time = None
        last_sender = None
        last_message_read = True

    return {
        'unread_count': unread_count,
        'last_message': last_message,
        'last_time': last_time,
        'last_sender': last_sender,
        'last_message_read': last_message_read
    }







#--------------------------- message old -------------------#
def mark_messages_as_read(room_id, username):
    # Mark all messages not sent by this user as read
    result = messages_collection.update_many(
        {
            'room_id': ObjectId(room_id),
            'sender': {'$ne': username},
            'is_read': False
        },
        {'$set': {'is_read': True}}
    )
    return result.modified_count  # Return how many messages were marked as read

def count_unread_messages(room_id, username):
    return messages_collection.count_documents({
        'room_id': ObjectId(room_id),
        'sender': {'$ne': username},
        'is_read': False
    })



SECRET_KEY = b'_ShXYTs-RdSQFcvyaU6IbBMYwMp1EBNDpBYPm8bEYsE=' #encryption key for message encryption can be changed
cipher_suite = Fernet(SECRET_KEY)

# Encrypting a message
def encrypt_message(plain_text):
    """ Encrypt the message using Fernet """
    encrypted_message = cipher_suite.encrypt(plain_text.encode('utf-8'))
    return encrypted_message.decode('utf-8')  # Return as string for storage

# Decrypting a message
def decrypt_message(encrypted_message):
    """ Decrypt the message using Fernet """
    decrypted_message = cipher_suite.decrypt(encrypted_message.encode('utf-8'))
    return decrypted_message.decode('utf-8')

def save_message(room_id, text, sender):
    encrypted_text = encrypt_message(text)
    messages_collection.insert_one({
        'room_id': ObjectId(room_id) if isinstance(room_id, str) else room_id,
        'text': encrypted_text,
        'sender': sender,
        'created_at': datetime.now(),
        'is_read': False  # NEW FIELD
    })


MESSAGE_FETCH_LIMIT = 3

def get_messages(room_id, page=0):
    offset = page * MESSAGE_FETCH_LIMIT
    messages = list(
        messages_collection.find({'room_id': ObjectId(room_id)})
        .sort('_id', DESCENDING)
        .limit(MESSAGE_FETCH_LIMIT)
        .skip(offset)
    )
    for message in messages:
        message['text'] = decrypt_message(message['text'])  # Decrypt the message
        message['created_at'] = message['created_at'].strftime("%d %b, %H:%M")
    return messages[::-1]

def get_room_messages(room_id, limit=20, page=0):
    skip = page * limit
    messages = messages_collection.find({'room_id': ObjectId(room_id)}).sort('created_at', -1).skip(skip).limit(limit)
    messages = list(messages)
    for message in messages:
        message['text'] = decrypt_message(message['text'])  # Decrypt the message
    return messages[::-1]  # Reverse to show oldest first
