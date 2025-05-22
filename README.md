# 🔒 Secure Real-Time Chat System using Flask-SocketIO and MongoDB

A role-based, real-time chat system enabling seamless communication between users and admins. Built with **Flask**, **Flask-SocketIO**, and **MongoDB**, this application is designed to be scalable, modular, and ready for integration with full-stack platforms like e-commerce websites or support systems.

---

## 📌 Project Overview

### 🔹 Motivation

Traditional HTTP requests failed to deliver real-time chat performance. We adopted **WebSockets via Flask-SocketIO** to achieve instant bi-directional communication, drastically improving the user experience.

### 🔹 Description

- Users can chat with specific types of admins (e.g., Billing, Technical Support).
- A unique chatroom is created or reused per user-admin type pair.
- Real-time messaging is handled via SocketIO and stored persistently in MongoDB.

---

## 🚀 Features

- ⚡ **Real-time messaging** using WebSockets
- 👥 **Role-based access** with separate login for users and admins
- 🧠 **Dynamic room management** per user-admin-type pair
- 📩 **Unread message tracking** and real-time notifications
- 🔌 **Socket event handling** for efficient communication
- 🗂️ **Persistent message storage** using MongoDB
- 🔧 **Modular and extensible design**

---

## 🛠️ Technologies Used

- Flask
- Flask-SocketIO
- MongoDB
- PyMongo
- HTML, CSS, JavaScript

---

## ⚙️ How to Set Up

### 🔑 Step 1: Clone the Repo

git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name

### 🔑 Step 2: Install requirements

pip install -r requirements.txt

### 🔑 Step 3: Create MongoDB Account

1. Go to MongoDB Atlas and create a free account.
2. Create a cluster and a database named ChatDB.
3. Whitelist your IP and create a user with a strong password.
4. Get the connection string in this format: mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority

### 🔑 Step 4: Create .env file

Create a file named .env in the root folder of your project:
.env
MONGO_URI=your_mongodb_connection_string_here
SECRET_KEY=your_flask_secret_key_here

### 🔑 Step 5: Run the app 

python app.py

---

## 🧪 Project Modules

- User and Admin Auth: Secure, session-based login systems
- Chatrooms: Dynamically created per user-admin type
- Message System: Encrypted message storage and retrieval
- Real-time Engine: Flask-SocketIO event handlers for send, join, and notify

---

## 🤝 Connect with Us

Connect with us on Linkedin 
- Muhammad Waqi Mallick | Linkedin: https://www.linkedin.com/in/muhammad-waqi-mallick-4b7b912a3/
- Muhammad Usman | Linkedin: https://www.linkedin.com/in/muhahmmad-usman-91973b2b0/
