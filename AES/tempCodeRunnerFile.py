import os
from flask import Flask, request, redirect, url_for, render_template, flash, send_file
from PIL import Image
from Crypto.Cipher import AES
import hashlib

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Folder for uploaded files

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def encrypt_image(image_path, password):
    key = hashlib.sha256(password.encode()).digest()
    with open(image_path, 'rb') as file:
        data = file.read()
    while len(data) % 16 != 0:
        data += b' '
    cipher = AES.new(key, AES.MODE_ECB)
    encrypted = cipher.encrypt(data)
    encrypted_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'encrypted_image.enc')
    with open(encrypted_image_path, 'wb') as enc_file:
        enc_file.write(encrypted)
    return encrypted_image_path

def decrypt_image_data(encrypted_data, password):
    key = hashlib.sha256(password.encode()).digest()
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted = cipher.decrypt(encrypted_data)
    decrypted = decrypted.rstrip(b' ')
    return decrypted

def decrypt_image(image_path, password):
    key = hashlib.sha256(password.encode()).digest()
    with open(image_path, 'rb') as file:
        encrypted_data = file.read()
    decrypted = decrypt_image_data(encrypted_data, password)
    decrypted_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'decrypted_image.png')
    with open(decrypted_image_path, 'wb') as dec_file:
        dec_file.write(decrypted)
    return decrypted_image_path

def lsb_hide(cover_image_path, secret_data_path, output_path):
    cover_image = Image.open(cover_image_path)
    cover_pixels = cover_image.load()
    
    with open(secret_data_path, 'rb') as file:
        secret_data = file.read()
    
    secret_bits = ''.join(format(byte, '08b') for byte in secret_data)
    secret_bits += '0' * (len(secret_bits) % 8)  # Ensure the length is a multiple of 8
    
    width, height = cover_image.size
    secret_index = 0
    for y in range(height):
        for x in range(width):
            pixel = list(cover_pixels[x, y])
            for i in range(3):
                if secret_index < len(secret_bits):
                    pixel[i] = (pixel[i] & ~1) | int(secret_bits[secret_index])
                    secret_index += 1
            cover_pixels[x, y] = tuple(pixel)
            if secret_index >= len(secret_bits):
                break
        if secret_index >= len(secret_bits):
            break

    cover_image.save(output_path)

def lsb_retrieve(stego_image_path, secret_data_length):
    stego_image = Image.open(stego_image_path)
    stego_pixels = stego_image.load()

    secret_bits = []
    width, height = stego_image.size
    for y in range(height):
        for x in range(width):
            pixel = stego_pixels[x, y]
            for i in range(3):
                secret_bits.append(pixel[i] & 1)
                if len(secret_bits) >= secret_data_length * 8:
                    break
            if len(secret_bits) >= secret_data_length * 8:
                break
        if len(secret_bits) >= secret_data_length * 8:
            break

    secret_data = bytearray()
    for i in range(0, len(secret_bits), 8):
        byte = 0
        for bit in secret_bits[i:i+8]:
            byte = (byte << 1) | bit
        secret_data.append(byte)

    return bytes(secret_data)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encrypt', methods=['POST'])
def encrypt():
    if 'image' not in request.files or 'encrypt_password' not in request.form:
        flash('Please provide both an image and a password.')
        return redirect(url_for('index'))

    file = request.files['image']
    encrypt_password = request.form['encrypt_password']

    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))

    image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(image_path)
    encrypted_image_path = encrypt_image(image_path, encrypt_password)
    flash(f'Image encrypted successfully. <a href="{url_for("download_file", filename="encrypted_image.enc")}">Download Encrypted Image</a>', 'success')
    return redirect(url_for('index'))

@app.route('/decrypt', methods=['POST'])
def decrypt():
    if 'secret_image' not in request.files or 'decrypt_password' not in request.form:
        flash('Please provide both a secret image and a password.')
        return redirect(url_for('index'))

    secret_file = request.files['secret_image']
    decrypt_password = request.form['decrypt_password']

    if secret_file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))

    secret_image_path = os.path.join(app.config['UPLOAD_FOLDER'], secret_file.filename)
    secret_file.save(secret_image_path)
    decrypted_image_path = decrypt_image(secret_image_path, decrypt_password)
    flash(f'Image decrypted successfully. <a href="{url_for("download_file", filename="decrypted_image.png")}">Download Decrypted Image</a>', 'success')
    return redirect(url_for('index'))

@app.route('/steganography', methods=['POST'])
def steganography():
    if 'cover_image' not in request.files or 'encrypted_image' not in request.files:
        flash('Please provide both a cover image and an encrypted image.')
        return redirect(url_for('index'))

    cover_image = request.files['cover_image']
    encrypted_image = request.files['encrypted_image']

    if cover_image.filename == '' or encrypted_image.filename == '':
        flash('No selected files')
        return redirect(url_for('index'))

    cover_image_path = os.path.join(app.config['UPLOAD_FOLDER'], cover_image.filename)
    encrypted_image_path = os.path.join(app.config['UPLOAD_FOLDER'], encrypted_image.filename)
    stego_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'stego_image.png')

    cover_image.save(cover_image_path)
    encrypted_image.save(encrypted_image_path)

    lsb_hide(cover_image_path, encrypted_image_path, stego_image_path)
    flash(f'Steganography completed successfully. <a href="{url_for("download_file", filename="stego_image.png")}">Download Stego Image</a>', 'success')
    return redirect(url_for('index'))

@app.route('/retrieve', methods=['POST'])
def retrieve():
    if 'stego_image' not in request.files or 'decrypt_password' not in request.form:
        flash('Please provide a stego image and the decryption password.')
        return redirect(url_for('index'))

    stego_image = request.files['stego_image']
    decrypt_password = request.form['decrypt_password']

    if stego_image.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))

    stego_image_path = os.path.join(app.config['UPLOAD_FOLDER'], stego_image.filename)
    stego_image.save(stego_image_path)
    retrieved_data = lsb_retrieve(stego_image_path, secret_data_length=len(decrypt_password)*16)  # Assuming secret data length to be the multiple of block size

    decrypted_image_data = decrypt_image_data(retrieved_data, decrypt_password)
    retrieved_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'retrieved_image.png')
    with open(retrieved_image_path, 'wb') as retrieved_image_file:
        retrieved_image_file.write(decrypted_image_data)

    flash(f'Secret data retrieved and decrypted successfully. <a href="{url_for("download_file", filename="retrieved_image.png")}">Download Retrieved Image</a>', 'success')
    return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
