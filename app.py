from datetime import datetime
from bson.json_util import dumps
from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, join_room, leave_room
from pymongo.errors import DuplicateKeyError
from dotenv import load_dotenv
from db import *
import os 

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

@app.route('/')
def home():
    message= ''
    if session.get('user'):
        return redirect(url_for('select_admin'))
    return redirect(url_for('user_auth'))

#---------- USER AUTH ----------#
@app.route('/user/auth', methods=['GET', 'POST'])
def user_auth():
    if session.get('user'):
        return redirect(url_for('select_admin'))

    message = ''
    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'login':
            username = request.form.get('username')
            password_input = request.form.get('password')
            user = get_user(username)

            if user and user.check_password(password_input):
                session['user'] = {'username': user.username, 'email': user.email}
                return redirect(url_for('select_admin'))
            else:
                message = 'Failed to login!'

        elif form_type == 'signup':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')

            try:
                save_user(username, email, password)
                session['user'] = {'username': username, 'email': email}
                return redirect(url_for('select_admin'))
            except DuplicateKeyError:
                message = 'User already exists!'

    return render_template('user_signin.html', message=message)


@app.route('/user/logout')
def user_logout():
    session.pop('user', None)
    return redirect(url_for('user_auth'))


#---------- ADMIN AUTH ----------#


@app.route('/admin/auth', methods=['GET', 'POST'])
def admin_auth():
    if session.get('admin'):
        return redirect(url_for('admin_dashboard'))

    message = ''

    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'signup':
            # Handle signup
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            admin_type = request.form.get('admin_type')  # Default type if missing

            try:
                save_admin(username, email, password, admin_type)
                session['admin'] = {'username': username, 'email': email, 'admin_type': admin_type}
                return redirect(url_for('admin_dashboard'))
            except DuplicateKeyError:
                message = "Admin already exists!"

        elif form_type == 'login':
            # Handle login
            username = request.form.get('username')
            password_input = request.form.get('password')
            admin = get_admin(username)

            if admin and admin.check_password(password_input):
                session['admin'] = {
                    'username': admin.username,
                    'email': admin.email,
                    'admin_type': admin.admin_type
                }
                return redirect(url_for('admin_dashboard'))
            else:
                message = 'Failed to login!'

    # For GET request, or POST failure
    return render_template('admin_signin.html', message=message)




@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_auth'))

#---------- CHAT HANDLER ----------#
@app.route('/check_or_create_room/<admin_type>', methods=['GET'])
def check_or_create_room(admin_type):
    if not session.get('user'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    username = session['user']['username']

    room_id = get_or_create_room_for_user(username, admin_type)

    if room_id:
        return jsonify({'success': True, 'room_id': str(room_id)})
    else:
        return jsonify({'success': False, 'message': 'Room creation failed'}), 500



@app.route('/user/chat/<admin_type>', methods=['GET', 'POST'])
def user_chat_with_admin(admin_type):
    if not session.get('user'):
        return redirect(url_for('user_login'))

    username = session['user']['username']
    user_id = username

    room_id = get_or_create_room_for_user(user_id, admin_type)  # <-- use your function!
    mark_messages_as_read(room_id, username)
    room = get_room(room_id)
    messages = get_room_messages(room_id)

    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            save_message(room_id, message, username)
            socketio.emit('receive_message', {'username': username, 'message': message, 'room': str(room_id)}, room=str(room_id))

    return render_template('view_room.html', username=username, room=room, messages=messages, role="User")


@app.route('/admin/chat/<admin_type>', methods=['GET', 'POST'])
def admin_chat_with_user(admin_type):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    admin_username = session['admin']['username']
    user_username = request.args.get('user')  # passed as query parameter ?user=username

    if not user_username:
        return "User not specified.", 400

    room_id = get_room_for_admin(admin_username, user_username)  # <-- use your function!

    if not room_id:
        return "No chat room exists with this user.", 404
    mark_messages_as_read(room_id, admin_username)
    room = get_room(room_id)
    messages = get_room_messages(room_id)
    
    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            save_message(room_id, message, admin_username)
            socketio.emit('receive_message', {'username': admin_username, 'message': message, 'room': str(room_id)}, room=str(room_id))

    return render_template('view_room.html', username=admin_username, room=room, messages=messages, role="Admin")


@app.route('/get_room_messages/<room_id>')
def get_room_messages_api(room_id):
    if not session.get('admin') and not session.get('user'):
        return jsonify({'error': 'Unauthorized'}), 401
    messages = get_room_messages(room_id)
    # Convert ObjectId and datetime to string for JSON
    def serialize(msg):
        return {
            'sender': msg.get('sender'),
            'text': msg.get('text'),
            'created_at': msg.get('created_at').strftime('%d %b, %H:%M') if msg.get('created_at') else '',
        }
    return jsonify([serialize(m) for m in messages])

#---------- SOCKETIO EVENTS ----------#
@socketio.on('send_message')
def handle_send_message_event(data):
    app.logger.info(f"{data['username']} sent message to room {data['room']}: {data['message']}")
    data['created_at'] = datetime.now().strftime("%d %b, %H:%M")
    save_message(data['room'], data['message'], data['username'])
    socketio.emit('receive_message', data, room=data['room'])

@socketio.on('join_room')
def handle_join_room_event(data):
    join_room(data['room'])
    socketio.emit('join_room_announcement', data, room=data['room'])

@socketio.on('leave_room')
def handle_leave_room_event(data):
    leave_room(data['room'])
    socketio.emit('leave_room_announcement', data, room=data['room'])

#---------- ADMIN DASH + USER SELECTION ----------#
@app.route('/select_admin')
def select_admin():
    if not session.get('user'):
        return redirect(url_for('user_login'))
    
    admin_types = ['Billing Support', 'Technical Support', 'Account Manager', 'Sales Rep', 'HR']
    user_username = session['user']['username']

    user_chats = []  # <-- make a list of dictionaries
    total_unread_chats = 0

    for admin_type in admin_types:
        # Get room for this admin type
        room_id = get_room_for_user(user_username, admin_type)

        if not room_id:
            continue  # If no room exists, skip
        

        summary = get_room_summary(room_id, user_username)
        chat = {}
        chat['user'] = admin_type
        chat['room_id'] = str(room_id)
        chat['unread_count'] = summary['unread_count']
        chat['last_message'] = summary['last_message']
        chat['last_time'] = str(summary['last_time']) if summary['last_time'] else None
        print('user last_time', chat['last_time'])
        chat['last_sender'] = summary['last_sender']
        print('last_sender', chat['last_sender'])
        chat['last_message_read'] = summary['last_message_read']

        if summary['unread_count'] > 0:
            total_unread_chats += 1

        user_chats.append(chat)

    return render_template(
        #'select_admin.html',
        'user_dashboard.html', 
        admin_types=admin_types,
        current_admin=session['user'],
        user_chats=user_chats,
        total_unread_chats=total_unread_chats
    )


@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('admin'):
        user_chats = get_room_admin_type(session['admin']['admin_type'])

        total_unread_chats = 0  # Count of chats that have any unread messages

        for chat in user_chats:
            room_id = get_room_for_admin(
                session['admin']['username'],
                chat['user']
            )
            summary = get_room_summary(room_id, session['admin']['username'])
            chat['room_id'] = str(room_id)
            chat['unread_count'] = summary['unread_count']
            chat['last_message'] = summary['last_message']
            chat['last_time'] = summary['last_time'] if summary['last_time'] else None
            print('admin last_time', chat['last_time'])
            chat['last_sender'] = summary['last_sender']
            chat['last_message_read'] = summary['last_message_read']
            if summary['unread_count'] > 0:
                total_unread_chats += 1

        return render_template(
            #'admin_index.html',  # 
            'admin_dashboard.html',
            current_admin=session['admin'],
            user_chats=user_chats,
            total_unread_chats=total_unread_chats
        )
    
    return redirect(url_for('admin_auth'))

@app.route('/get_chat_updates')
def get_chat_updates():
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    admin_username = session['admin']['username']
    admin_type = session['admin']['admin_type']
    
    user_chats = []
    rooms = rooms_collection.find({'admin_type': admin_type})
    
    for room in rooms:
        summary = get_room_summary(room['_id'], admin_username)
        user_chats.append({
            'user': room['user_id'],
            'room_id': str(room['_id']),
            'unread_count': summary['unread_count'],
            'last_message': summary['last_message'],
            'last_time': summary['last_time'],
            'last_sender': summary['last_sender'],
            'last_message_read': summary['last_message_read']
        })
    
    return jsonify(user_chats)

@app.route('/get_user_chat_updates')
def get_user_chat_updates():
    if not session.get('user'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = session['user']['username']
    admin_types = ['Billing Support', 'Technical Support', 'Account Manager', 'Sales Rep', 'HR']
    
    user_chats = []
    for admin_type in admin_types:
        room = rooms_collection.find_one({"user_id": username, "admin_type": admin_type})
        if room:
            summary = get_room_summary(room['_id'], username)
            user_chats.append({
                'user': admin_type,  # Using admin_type as the display name
                'room_id': str(room['_id']),
                'unread_count': summary['unread_count'],
                'last_message': summary['last_message'],
                'last_time': summary['last_time'],
                'last_sender': summary['last_sender'],
                'last_message_read': summary['last_message_read']
            })
    
    return jsonify(user_chats)


@app.route('/mark_messages_as_read/<room_id>', methods=['POST'])
def mark_messages_as_read_endpoint(room_id):
    if not session.get('admin') and not session.get('user'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = None
    if session.get('admin'):
        username = session['admin']['username']
    elif session.get('user'):
        username = session['user']['username']
    
    if not username:
        return jsonify({'error': 'User not identified'}), 400

    count = mark_messages_as_read(room_id, username)
    return jsonify({'success': True, 'count': count})


if __name__ == '__main__':
    socketio.run(app, debug=True)