from flask import Flask, request, redirect, url_for, render_template,flash, session, jsonify
from datetime import datetime
import sqlite3
import base64
from win10toast import ToastNotifier
from PIL import Image
import io
import os
import socket
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox

arduino_ip = '192.168.1.177'  # IP address of your Arduino
arduino_port = 80  # Port number the Arduino server is listening on

app = Flask(__name__)
app.secret_key = '123456'
def show_notification(message):
    hr = ToastNotifier()
    hr.show_toast("Notification", message)


notification_displayed = False  # Global flag to track if a notification is being displayed

def show_general_notification(message):
    global notification_displayed
    if not notification_displayed:
        notification_displayed = True
        # Create a new Tk instance
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        # Display the notification message box
        messagebox.showinfo("Intruder", "Someone enter school without permission")
        # Reset the flag after the message box is closed
        notification_displayed = False
        # Run the Tkinter main loop
        root.mainloop()


# Route to handle the notification request from Arduino for general notification
@app.route('/general_notification', methods=['GET'])
def general_notification_route():
    message = request.args.get('message')
    threading.Thread(target=show_general_notification, args=(message,)).start()
    return jsonify({'success': True, 'message': 'General notification received!'})


@app.route('/')
def home():
    return render_template('login.html')
@app.route('/back')
def back():
    return render_template('index.html')

@app.route('/logout')
def logout():
    return render_template('login.html')

# Assuming you have a function to check the user's role or permissionsp
def get_user_role(username):
    # Logic to determine user's role goes here
    # For example, you might query the database
    # and check if the user is an admin or a regular user
    # This is just a placeholder implementation
    if username == "admin":
        return "admin"
    else:
        return "user"

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = sqlite3.connect('mydb.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
    user = c.fetchone()
    conn.close()
    if user:
        session['username'] = username  # Store username in session
        user_role = get_user_role(username)
        if user_role == "admin":
            return redirect(url_for('back'))
        else:
            return redirect(url_for('user_index'))
    else:
        return redirect(url_for('home'))



@app.route('/join', methods=['GET', 'POST'])
def join():
    if request.method == 'POST':
        Fname = request.form['Fname']
        Lname = request.form['Lname']
        Vtype = request.form['Vtype']
        Pnumber = request.form['Pnumber']
        Snumber = request.form['Snumber']
        age = request.form['age']
        gender = request.form['gender']
        PhoneNo = request.form['PhoneNo']

        with sqlite3.connect("mydb.db") as users:
            cursor = users.cursor()
            cursor.execute("SELECT * FROM car_user WHERE (Fname = ? AND Lname = ?) OR Pnumber = ?", (Fname, Lname, Pnumber))
            existing_user = cursor.fetchone()

            if existing_user:
                return jsonify({'success': False, 'message': 'User already exists. Please choose a different name or plate number.'})
            else:
                username = Fname
                password = Lname

                cursor.execute("INSERT INTO car_user \
                               (Fname, Lname, Vtype, Pnumber, Snumber, age, entry, one, gender, PhoneNo) VALUES (?,?,?,?,?,?,?,?,?,?)",
                               (Fname, Lname, Vtype, Pnumber,Snumber, age, 0, 0, gender, PhoneNo))
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                users.commit()
                return jsonify({'success': True, 'message': 'User successfully registered!'})

    return render_template('join.html')



@app.route('/participants', methods=['GET'])
def participants():
    search_query = request.args.get('search', '')
    filter_by = request.args.get('filter', '')

    conn = sqlite3.connect('mydb.db')
    cursor = conn.cursor()

    if search_query and filter_by:
        # Constructing the SQL query dynamically based on the selected filter
        query = f"SELECT * FROM car_user WHERE {filter_by} LIKE ?"
        cursor.execute(query, ('%' + search_query + '%',))
    else:
        cursor.execute('SELECT * FROM car_user')

    data = cursor.fetchall()
    conn.close()

    data_with_resized_images = []

    for participant in data:
        image_data = participant[8]
        if image_data:
            # Open the image using PIL
            img = Image.open(io.BytesIO(image_data))

            # Resize the image
            # Replace (100, 100) with the desired width and height
            img = img.resize((1080, 640))

            # Convert the resized image back to bytes
            output_buffer = io.BytesIO()
            img.save(output_buffer, format='PNG')
            image_data_resized = output_buffer.getvalue()

            # Convert resized image data to base64
            image_base64 = base64.b64encode(image_data_resized).decode('utf-8')
            participant_with_resized_image = list(participant)
            participant_with_resized_image[8] = image_base64
            data_with_resized_images.append(participant_with_resized_image)
        else:
            data_with_resized_images.append(participant)

    # Now use data_with_resized_images instead of data_with_base64_images
    return render_template("participants.html", data=data_with_resized_images)

@app.route('/user_participants', methods=['GET'])
def user_participants():
    # Check if the user is logged in
    if 'username' in session:
        username = session['username']
        # Fetch rows where username matches Fname
        conn = sqlite3.connect('mydb.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM car_user WHERE Fname=?', (username,))
        data = cursor.fetchall()  # Fetch all matching rows
        conn.close()

        data_with_resized_images = []

        for participant in data:
            image_data = participant[7]
            if image_data:
                # Open the image using PIL
                img = Image.open(io.BytesIO(image_data))

                # Resize the image
                # Replace (100, 100) with the desired width and height
                img = img.resize((1080, 640))

                # Convert the resized image back to bytes
                output_buffer = io.BytesIO()
                img.save(output_buffer, format='PNG')
                image_data_resized = output_buffer.getvalue()

                # Convert resized image data to base64
                image_base64 = base64.b64encode(image_data_resized).decode('utf-8')
                participant_with_resized_image = list(participant)
                participant_with_resized_image[7] = image_base64
                data_with_resized_images.append(participant_with_resized_image)
            else:
                data_with_resized_images.append(participant)

        return render_template('user_participants.html', data=data_with_resized_images)
    else:
        return redirect(url_for('login'))  # Redirect to login page if not logged in




@app.route('/timeLog', methods=['GET'])
def timeLog():
    search_query = request.args.get('search', '')
    filter_by = request.args.get('filter', '')

    conn = sqlite3.connect('mydb.db')
    cursor = conn.cursor()

    if search_query and filter_by:
        # Constructing the SQL query dynamically based on the selected filter
        query = f"SELECT * FROM timeDate WHERE {filter_by} LIKE ?"
        cursor.execute(query, ('%' + search_query + '%',))
    else:
        cursor.execute('SELECT * FROM timeDate')

    data = cursor.fetchall()
    data_with_resized_images = []

    for participant in data:
        image_data = participant[4]
        if image_data:
            # Open the image using PIL
            img = Image.open(io.BytesIO(image_data))

            # Resize the image
            # Replace (100, 100) with the desired width and height
            img = img.resize((1080, 640))

            # Convert the resized image back to bytes
            output_buffer = io.BytesIO()
            img.save(output_buffer, format='PNG')
            image_data_resized = output_buffer.getvalue()

            # Convert resized image data to base64
            image_base64 = base64.b64encode(image_data_resized).decode('utf-8')
            participant_with_resized_image = list(participant)
            participant_with_resized_image[4] = image_base64
            data_with_resized_images.append(participant_with_resized_image)
        else:
            data_with_resized_images.append(participant)
    conn.close()

    # Pass the data to the template for rendering
    return render_template("timeLog.html", data=data_with_resized_images)

@app.route('/user_timeLog', methods=['GET'])
def user_timeLog():
    search_query = request.args.get('search', '')
    filter_by = request.args.get('filter', '')

    # Fetch the username from the session
    if 'username' in session:
        username = session['username']
    else:
        return redirect(url_for('login'))  # Redirect to login page if not logged in

    conn = sqlite3.connect('mydb.db')
    cursor = conn.cursor()

    # Fetch the Pnumber based on the username
    cursor.execute('SELECT Pnumber FROM car_user WHERE Fname=?', (username,))
    pnumber = cursor.fetchone()[0]

    if search_query and filter_by:
        # Constructing the SQL query dynamically based on the selected filter
        query = f"SELECT * FROM timeDate WHERE {filter_by} LIKE ? AND Pnumber=?"
        cursor.execute(query, ('%' + search_query + '%', pnumber))
    else:
        cursor.execute('SELECT * FROM timeDate WHERE Pnumber=?', (pnumber,))

    data = cursor.fetchall()
    data_with_resized_images = []

    for participant in data:
        image_data = participant[4]
        if image_data:
            # Open the image using PIL
            img = Image.open(io.BytesIO(image_data))

            # Resize the image
            # Replace (100, 100) with the desired width and height
            img = img.resize((1080, 640))

            # Convert the resized image back to bytes
            output_buffer = io.BytesIO()
            img.save(output_buffer, format='PNG')
            image_data_resized = output_buffer.getvalue()

            # Convert resized image data to base64
            image_base64 = base64.b64encode(image_data_resized).decode('utf-8')
            participant_with_resized_image = list(participant)
            participant_with_resized_image[4] = image_base64
            data_with_resized_images.append(participant_with_resized_image)
        else:
            data_with_resized_images.append(participant)
    conn.close()

    # Pass the data to the template for rendering
    return render_template("user_timeLog.html",data=data_with_resized_images)

# Route to get all users
@app.route('/api/users', methods=['GET'])
def get_users():
    conn = sqlite3.connect('mydb.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()
    return jsonify(users)

# Route to get a specific user by ID
@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = sqlite3.connect('mydb.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id=?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return jsonify(user)
    else:
        return jsonify({"message": "User not found"}), 404

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        username = session.get('username')  # Assuming you store the username in session after login
        if not username:
            flash('You must be logged in to change your password!', 'error')
            return redirect(url_for('login',message = 'You must be logged in to change your password!'))  # Redirect to login page if user is not logged in

        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        # Verify if new password matches the confirm password
        if new_password != confirm_password:
            flash('New password and confirm password do not match!', 'error')
            return redirect(url_for('change_password', message='New password and confirm password do not match!'))

        # Retrieve the user's information from the database using the provided username
        provided_username = request.form['username']
        conn = sqlite3.connect('mydb.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (provided_username,))
        user = c.fetchone()

        if not user:  # If user is not found in the database
            flash('User not found!', 'error')
            conn.close()
            return redirect(url_for('change_password', message='User not found!'))

        # Check if the provided username matches the session username
        if provided_username != username:
            flash('You can only change your own password!', 'error')
            conn.close()
            return redirect(url_for('change_password', message='You can only change your own password!'))
        # Check if the current password matches the stored password
        if user[2] != current_password:  # Assuming the password is stored in the third column
            flash('Invalid current password!', 'error')
            conn.close()
            return redirect(url_for('change_password',message = 'Invalid current password!'))

        # Update the password in the database
        c.execute('UPDATE users SET password = ? WHERE username = ?', (new_password, username))
        conn.commit()
        conn.close()
        flash('Password updated successfully!', 'success')
        return redirect(url_for('home',message = 'Password updated successfully!'))

    return render_template('change_password.html')  # Assuming you have a template for change_password.html

    return render_template('change_password.html')


@app.route('/change_Plate_Number', methods=['GET', 'POST'])
def change_Plate_Number():
    if request.method == 'POST':
        username = session.get('username')  # Assuming you store the username in session after login
        if not username:
            flash('You must be logged in to change your plate number!', 'error')
            return redirect(url_for('login'))  # Redirect to login page if user is not logged in

        current_username = request.form['username']
        new_plate_number = request.form['new_plate_number'].upper()




        # Retrieve the user's information from the database using the provided username
        provided_username = request.form['username']
        conn = sqlite3.connect('mydb.db')
        c = conn.cursor()
        c.execute('SELECT * FROM car_user WHERE Fname = ?', (provided_username,))
        user = c.fetchone()

        if not user:  # If user is not found in the database
            flash('User not found!', 'error')
            conn.close()
            return jsonify({'success': False, 'message': 'User not found!'})



        # Update the password in the database
        c.execute('UPDATE car_user SET Pnumber = ? WHERE Fname = ?', (new_plate_number, current_username))
        conn.commit()
        conn.close()
        flash('Plate number updated successfully!', 'success')
        return jsonify({'success': True, 'message': 'Plate number updated successfully!'})

    return render_template('change_Plate_Number.html')

@app.route('/user_change_password', methods=['GET', 'POST'])
def user_change_password():
    if request.method == 'POST':
        username = session.get('username')  # Assuming you store the username in session after login
        if not username:
            flash('You must be logged in to change your password!', 'error')
            return redirect(url_for('login',message = 'You must be logged in to change your password!'))  # Redirect to login page if user is not logged in

        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        # Verify if new password matches the confirm password
        if new_password != confirm_password:
            flash('New password and confirm password do not match!', 'error')
            return redirect(url_for('user_change_password', message='New password and confirm password do not match!'))

        # Retrieve the user's information from the database using the provided username
        provided_username = request.form['username']
        conn = sqlite3.connect('mydb.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (provided_username,))
        user = c.fetchone()

        if not user:  # If user is not found in the database
            flash('User not found!', 'error')
            conn.close()
            return redirect(url_for('user_change_password', message='User not found!'))

        # Check if the provided username matches the session username
        if provided_username != username:
            flash('You can only change your own password!', 'error')
            conn.close()
            return redirect(url_for('user_change_password',message = 'Invalid current password!'))
        # Check if the current password matches the stored password
        if user[2] != current_password:  # Assuming the password is stored in the third column
            flash('Invalid current password!', 'error')
            conn.close()
            return redirect(url_for('user_change_password',message = 'Invalid current password!'))

        # Update the password in the database
        c.execute('UPDATE users SET password = ? WHERE username = ?', (new_password, username))
        conn.commit()
        conn.close()
        flash('Password updated successfully!', 'success')
        return redirect(url_for('home',message = 'Password updated successfully!'))

    return render_template('user_change_password.html')  # Assuming you have a template for change_password.html

    return render_template('user_change_password.html')


def check_plate_number_exit(extracted_text_str_exit):

    conn = sqlite3.connect('mydb.db')
    cursor = conn.cursor()
    # Check if the extracted text exists in the database and entry column is 0
    cursor.execute("SELECT Pnumber, entry FROM car_user WHERE Pnumber = ?", (extracted_text_str_exit,))
    result = cursor.fetchone()

    if result and result[1] == 1:  # Check if result exists and entry is 0
        conn = sqlite3.connect('mydb.db')
        cursor = conn.cursor()
        # If the extracted text exists and entry is 0, proceed to update the image column
        image_path = "captured_image_exit.jpg"
        # Read the image file as binary data
        with open(image_path, 'rb') as file:
            image_binary = file.read()
        cursor.execute("UPDATE car_user SET  entry = ?,one = 0 WHERE Pnumber = ?",
                       ( 0, extracted_text_str_exit))  # Update entry to 1

        # Look up the plate number in the car_user table's Snumber column
        cursor.execute("SELECT Snumber FROM car_user WHERE Pnumber = ?", (extracted_text_str_exit,))
        result = cursor.fetchone()

        if result:
            # Use the found plate number
            Snumber = result[0]

        # Insert current date and time into the table
        current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''INSERT INTO timeDate (TimeAndDate, Pnumber,Platenumber,Status,image) VALUES (?,?,?, ?,?)''',
                       (current_datetime, extracted_text_str_exit,Snumber,'Time out',image_binary))
        # Commit changes and close the connection
        conn.commit()



        print(f"car saved time and date exit '{extracted_text_str_exit}' in the database.")
        cursor.execute("SELECT Vtype FROM car_user WHERE Pnumber = ?", (extracted_text_str_exit,))
        vehicle_type = cursor.fetchone()[0]  # Fetch the vehicle type from the databass
        entry_or_exit = "exit"
        data = entry_or_exit + "," + extracted_text_str_exit + "," + vehicle_type

        print(f"Image saved for extracted text '{extracted_text_str_exit}' in the database.")
        #client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket object
        #client_socket.connect((arduino_ip, arduino_port))  # Connect to the Arduino server
        #client_socket.sendall(data.encode())  # Send the plate number to the Arduino server
        #client_socket.close()  # Close the socket connection
    elif result:
        print(f"Extracted text '{extracted_text_str_exit}' exists in the database, but the entry is not process.")
    else:
        print(f"Extracted text '{extracted_text_str_exit}' doesn't exist in the database.")

    conn.close()
    return False

@app.route('/check_plate_exit')
def check_plate_exit():
    extracted_text_str_exit = request.args.get('extracted_text_str_exit')
    if check_plate_number_exit(extracted_text_str_exit):
        print(">>>>>>>>>>>>>>>>>>>>>>>", extracted_text_str_exit)
        return "Plate number {} is registered.".format(extracted_text_str_exit)
    else:
        print(">>>>>>>>>>>>>>>>>>>>>>>", extracted_text_str_exit)
        return "Plate number {} is not registered.".format(extracted_text_str_exit)

@app.route('/update_exit', methods=['POST'])
def update_ext():
    plate_number = request.data.decode('utf-8')
    print("Received plate number:", plate_number)
    # Update entry in the database
    conn = sqlite3.connect('mydb.db')
    c = conn.cursor()
    c.execute("UPDATE car_user SET entry = 0 WHERE Pnumber = ?", (plate_number,))
    conn.commit()
    conn.close()
    return 'Data received and processed successfully'

@app.route('/receive_plate', methods=['POST'])
def receive_plate():
    plate_number = request.data.decode('utf-8')
    print("Received plate number:", plate_number)
    # Update entry in the database
    conn = sqlite3.connect('mydb.db')
    c = conn.cursor()
    c.execute("UPDATE car_user SET entry = 1 WHERE Pnumber = ?", (plate_number,))
    conn.commit()
    conn.close()
    return 'Data received and processed successfully'

@app.route('/update_one', methods=['POST'])
def receive_one():
    plate_number = request.data.decode('utf-8')
    print("Received plate number:", plate_number)
    # Update entry in the database
    conn = sqlite3.connect('mydb.db')
    c = conn.cursor()
    c.execute("UPDATE car_user SET one = 0 WHERE Pnumber = ?", (plate_number,))
    conn.commit()
    conn.close()
    return 'Data received and processed successfully'

@app.route('/capture', methods=['POST'])
def capture():
    plate_number = request.data.decode('utf-8')
    print("Received plate number:", plate_number)
    # Update entry in the database
    conn = sqlite3.connect('mydb.db')
    cursor = conn.cursor()

    # Look up the plate number in the car_user table's Snumber column
    cursor.execute("SELECT Snumber FROM car_user WHERE Pnumber = ?", (plate_number,))
    result = cursor.fetchone()

    if result:
        # Use the found plate number
        Snumber = result[0]


    # If the extracted text exists and entry is 0, proceed to update the image column
    image_path = "captured_image_entry.jpg"
    # Read the image file as binary data
    with open(image_path, 'rb') as file:
        image_binary = file.read()
    # Insert current date and time into the table
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''INSERT INTO timeDate (TimeAndDate, Pnumber,Platenumber,Status,image) VALUES (?,?,?,?, ?)''',
                   (current_datetime, plate_number,Snumber, 'Time in', image_binary))
    conn.commit()
    conn.close()
    return 'Data received and processed successfully'

def check_vType(extracted_text_str,vehicle_type):
    conn = sqlite3.connect('mydb.db')
    cursor = conn.cursor()
    cursor.execute("SELECT Vtype FROM car_user WHERE Pnumber = ?", (extracted_text_str,))
    vehicle_type = cursor.fetchone()
    conn.close()  # Close database connection
    if vehicle_type:  # Check if vehicle_type is not None
        vehicle_type = vehicle_type[0]  # Extract the string from the tuple
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((arduino_ip, arduino_port))
            if vehicle_type == "4wheels":
                client_socket.sendall("car".encode())
            elif vehicle_type == "2wheels":
                client_socket.sendall("motor".encode())
            client_socket.close()  # Close the socket connection
        except Exception as e:
            print("Error while communicating with Arduino:", e)
    else:
        print("No vehicle type found for extracted text:", extracted_text_str)

def check_plate_number(extracted_text_str):

    conn = sqlite3.connect('mydb.db')
    cursor = conn.cursor()
    # Check if the extracted text exists in the database and entry column is 0
    cursor.execute("SELECT Pnumber, one FROM car_user WHERE Pnumber = ?", (extracted_text_str,))
    result = cursor.fetchone()

    if result and result[1] == 0:  # Check if result exists and entry is 0
        # If the extracted text exists and entry is 0, proceed to update the image column
        image_path = "captured_image_entry.jpg"
        # Read the image file as binary data
        with open(image_path, 'rb') as file:
            image_binary = file.read()
            # Update the image binary data for a specific row in the database
        cursor.execute("UPDATE car_user SET image = ?, one = ? WHERE Pnumber = ?",
                       (image_binary, 1, extracted_text_str))  # Update entry to 1

        # Commit changes and close the connection
        conn.commit()
        cursor.execute("SELECT Vtype FROM car_user WHERE Pnumber = ?", (extracted_text_str,))
        vehicle_type = cursor.fetchone()[0]  # Fetch the vehicle type from the databass
        entry_or_exit = "entry"
        data = entry_or_exit + "," + extracted_text_str + "," + vehicle_type

        print(f"Image saved for extracted text '{extracted_text_str}' in the database.")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket object
        client_socket.connect((arduino_ip, arduino_port))  # Connect to the Arduino server
        client_socket.sendall(data.encode())  # Send the plate number to the Arduino server
        client_socket.close()  # Close the socket connection
    elif result:
        print(f"Extracted text '{extracted_text_str}' exists in the database, but the entry is already processed.")
    else:
        print(f"Extracted text '{extracted_text_str}' doesn't exist in the database.")
        # client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket object
        # client_socket.connect((arduino_ip, arduino_port))  # Connect to the Arduino server
        # client_socket.sendall("trigger".encode())  # Send the plate number to the Arduino server
        # client_socket.close()  # Close the socket connection

    conn.close()

    return False

@app.route('/check_plate')
def check_plate():
    extracted_text_str = request.args.get('extracted_text_str')
    if check_plate_number(extracted_text_str):
        print(">>>>>>>>>>>>>>>>>>>>>>>", extracted_text_str)
        return "Plate number {} is registered.".format(extracted_text_str)
    else:
        print(">>>>>>>>>>>>>>>>>>>>>>>", extracted_text_str)
        return "Plate number {} is not registered.".format(extracted_text_str)

@app.route('/close_gate')
def close_gate():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket object
    client_socket.connect((arduino_ip, arduino_port))  # Connect to the Arduino server
    client_socket.sendall("closegate".encode())  # Send the plate number to the Arduino server
    client_socket.close()  # Close the socket connection
    return render_template('index.html')
@app.route('/up_gate')
def open_gate():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket object
    client_socket.connect((arduino_ip, arduino_port))  # Connect to the Arduino server
    client_socket.sendall("opengate".encode())  # Send the plate number to the Arduino server
    client_socket.close()  # Close the socket connection
    return render_template('index.html')

# Flag to indicate if entry.py is already running
entry_running = False

# Path to the Python executable within your virtual environment
python_executable = r"C:\Users\EngrKurt\PycharmProjects\yolov5\.venv\Scripts\python.exe"


def run_entry():
    global entry_running
    if  entry_running:
        # Display a notification if entry.py is already running
        show_notification("entry.py is already running.")
        return

    try:
        entry_running = True
        #subprocess.run([python_executable, 'entry.py'])  # Assuming entry.py is in the same directory
        subprocess.run([python_executable, 'entry.py'], cwd=r"C:\Users\EngrKurt\PycharmProjects\yolov5")

    except Exception as e:
        print("Error running entry.py:", e)
    finally:
        entry_running = False

@app.route('/run_entry', methods=['POST'])
def run_entry_route():
    # Start a separate thread to run entry.py
    threading.Thread(target=run_entry).start()
    return jsonify({'success': True, 'message': 'Video will play soon!'})

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0', port='5000')
