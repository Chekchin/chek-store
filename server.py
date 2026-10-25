from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import os
import asyncio
from telethon import TelegramClient
from telethon.tl.types import DocumentAttributeFilename

app = Flask(__name__)

# កូដ Route សម្រាប់បង្ហាញ Logo / Favicon លើ Tab Browser (គាំទ្រទាំង /cheklogo.png និង /favicon.ico)
@app.route('/cheklogo.png')
@app.route('/favicon.ico')
def serve_logo():
    return send_from_directory(app.root_path, 'cheklogo.png', max_age=0)

app.secret_key = 'chek-store-super-secret-key-change-this'

# Flask-Login Configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# បញ្ជីឈ្មោះ Account សម្រាប់លោកបង និងមិត្តភក្តិ
USERS_DATABASE = {
    "CHEK": "@chinchek55",   # Account របស់លោកបងផ្ទាល់
    "CHEK1": "123456"        # Account សម្រាប់មិត្តភក្តិ
}

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id in USERS_DATABASE:
        return User(user_id)
    return None

# Telegram Configuration
BOT_TOKEN = "8954959021:AAH2VL9Vf2DkLux7iGMdBTgW9wpukmfDnVc"
DEFAULT_CHAT_ID = -1002304422673
API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# LOGIN ROUTE
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # ពិនិត្យមើលថា Username មានក្នុង Database ហើយ Password ត្រូវគ្នាដែរឬទេ
        if username in USERS_DATABASE and USERS_DATABASE[username] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('index'))
        else:
            error = 'Invalid Username or Password!'
    return render_template('login.html', error=error)

# LOGOUT ROUTE
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# INDEX ROUTE (Protected)
@app.route('/')
@login_required
def index():
    return render_template('index.html')

# UPLOAD ROUTE (Protected)
@app.route('/upload', methods=['POST'])
@login_required
def upload():
    try:
        if 'ipa_file' not in request.files:
            return jsonify({"status": "error", "message": "មិនទាន់បានជ្រើសរើសហ្វាល IPA ទេ!"}), 400
        
        file = request.files['ipa_file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "ឈ្មោះហ្វាលទទេ!"}), 400

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        custom_name = request.form.get('custom_name', '').strip()
        if not custom_name:
            custom_name = file.filename

        if not custom_name.lower().endswith(".ipa"):
            custom_name += ".ipa"

        chat_id_input = request.form.get('chat_id')
        chat_id = int(chat_id_input) if chat_id_input else DEFAULT_CHAT_ID

        user_caption = request.form.get('caption', '').strip()

        thumb_file = request.files.get('thumb_file')
        thumb_path = None
        if thumb_file and thumb_file.filename != '':
            thumb_path = os.path.join(UPLOAD_FOLDER, thumb_file.filename)
            thumb_file.save(thumb_path)

        async def send_to_telegram():
            client = TelegramClient('nikk_bot_session', API_ID, API_HASH)
            await client.start(bot_token=BOT_TOKEN)
            
            attributes = [DocumentAttributeFilename(file_name=custom_name)]

            await client.send_file(
                chat_id,
                file_path,
                caption=user_caption,
                parse_mode='html',
                thumb=thumb_path if thumb_path else None,
                attributes=attributes,
                force_document=True
            )
            await client.disconnect()

        asyncio.run(send_to_telegram())
        
        if os.path.exists(file_path):
            os.remove(file_path)
        if thumb_path and os.path.exists(thumb_path):
            os.remove(thumb_path)

        return jsonify({"status": "success", "message": "Uploaded to Telegram Channel Successfully!"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8888)