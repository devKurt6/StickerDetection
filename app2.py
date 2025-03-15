from flask import Flask, request, redirect, url_for, render_template,flash, session, jsonify
import time
import sqlite3
import base64
from win10toast import ToastNotifier
from PIL import Image
import io
import threading
app = Flask(__name__)
app.secret_key = '123456'
def show_notification(message):
    hr = ToastNotifier()
    hr.show_toast("Notification", message)
@app.route('/')
@app.route('/')
def home():
    return render_template('login.html')
@app.route('/back')
def back():
    return render_template('index.html')

@app.route('/logout')
def logout():
    return render_template('login.html')

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
        return render_template("index.html")
    else:
        return redirect(url_for('home', message='Login failed. Invalid username or password.'))

@app.route('/join', methods=['GET', 'POST'])
def join():
    if request.method == 'POST':
        Fname = request.form['Fname']
        Lname = request.form['Lname']
        Vtype = request.form['Vtype']
        Pnumber = request.form['Pnumber']
        age = request.form['age']
        gender = request.form['gender']
        PhoneNo = request.form['PhoneNo']

        with sqlite3.connect("mydb.db") as users:
            cursor = users.cursor()
            cursor.execute("INSERT INTO car_user \
                           (Fname,Lname,Vtype,Pnumber,age,entry,gender,PhoneNo) VALUES (?,?,?,?,?,?,?,?)",
                           (Fname,Lname,Vtype,Pnumber,age,0,gender,PhoneNo))
            users.commit()
        return render_template("index.html")
    else:

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

    # Now use data_with_resized_images instead of data_with_base64_images
    return render_template("participants.html", data=data_with_resized_images)

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
        username = session['username']  # Assuming you store the username in session after login

        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        # Verify if new password matches the confirm password
        if new_password != confirm_password:
            flash('New password and confirm password do not match!', 'error')
            return redirect(url_for('change_password'))

        # Retrieve the user's information from the database using the username
        conn = sqlite3.connect('mydb.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()

        # Check if the current password matches the stored password
        if user and user[2] == current_password:  # Assuming the password is stored in the third column
            # Update the password in the database
            c.execute('UPDATE users SET password = ? WHERE username = ?', (new_password, username))
            conn.commit()
            conn.close()
            flash('Password updated successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid current password!', 'error')
            conn.close()
            return redirect(url_for('change_password'))

    return render_template('change_password.html')
def check_extracted_text_in_database(extracted_text):  ### DATABASE SQLITE3

    extracted_text_str = ' '.join(extracted_text) if isinstance(extracted_text, list) else extracted_text
    print(">>>>>>>>>>>>>>>>>>>>>>>", extracted_text_str)


def check_plate_number(extracted_text_str):

    conn = sqlite3.connect('mydb.db')
    cursor = conn.cursor()
    # Check if the extracted text exists in the database and entry column is 0
    cursor.execute("SELECT Pnumber, entry FROM car_user WHERE Pnumber = ?", (extracted_text_str,))
    result = cursor.fetchone()

    if result and result[1] == 0:  # Check if result exists and entry is 0
        # If the extracted text exists and entry is 0, proceed to update the image column
        image_path = "captured_image.jpg"
        # Read the image file as binary data
        with open(image_path, 'rb') as file:
            image_binary = file.read()
            # Update the image binary data for a specific row in the database
        cursor.execute("UPDATE car_user SET image = ?, entry = ? WHERE Pnumber = ?",
                       (image_binary, 1, extracted_text_str))  # Update entry to 1
        # Commit changes and close the connection
        conn.commit()
        print(f"Image saved for extracted text '{extracted_text_str}' in the database.")
    elif result:
        print(f"Extracted text '{extracted_text_str}' exists in the database, but the entry is already processed.")
    else:
        print(f"Extracted text '{extracted_text_str}' doesn't exist in the database.")

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



if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0', port='5000')
