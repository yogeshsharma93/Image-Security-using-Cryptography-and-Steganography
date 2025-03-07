import os
from flask import Flask, request, redirect, url_for, render_template, flash, send_file
from PIL import Image
from Crypto.Cipher import AES
import hashlib
from performance_metrics import calculate_mse_psnr
from histogram_analysis import plot_image_histograms

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Folder for uploaded files

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def pad_data(data):
    # Padding data to make it a multiple of 16 bytes (AES block size)
    padding_len = 16 - len(data) % 16
    return data + bytes([padding_len] * padding_len)

def unpad_data(data):
    # Remove the padding added during encryption
    padding_len = data[-1]
    return data[:-padding_len]

def encrypt_image(image_path, password):
    key = hashlib.sha256(password.encode()).digest()
    with open(image_path, 'rb') as file:
        data = file.read()
    
    padded_data = pad_data(data)  # Pad the data to block boundary
    cipher = AES.new(key, AES.MODE_ECB)
    encrypted = cipher.encrypt(padded_data)
    
    encrypted_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'encrypted_image.enc')
    with open(encrypted_image_path, 'wb') as enc_file:
        enc_file.write(encrypted)
    
    return encrypted_image_path

def decrypt_image_data(encrypted_data, password):
    key = hashlib.sha256(password.encode()).digest()
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted = cipher.decrypt(encrypted_data)
    
    # Unpad the decrypted data
    decrypted = unpad_data(decrypted)
    
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

# Function to calculate the secret data length based on stego image size
def get_secret_data_length(stego_image_path):
    stego_image = Image.open(stego_image_path)
    width, height = stego_image.size
    return width * height * 3  # 3 channels per pixel, 1 bit per channel

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
    password = request.form['password']

    if cover_image.filename == '' or encrypted_image.filename == '':
        flash('No selected files')
        return redirect(url_for('index'))

    # Save uploaded files
    cover_image_path = os.path.join(app.config['UPLOAD_FOLDER'], cover_image.filename)
    encrypted_image_path = os.path.join(app.config['UPLOAD_FOLDER'], encrypted_image.filename)
    cover_image.save(cover_image_path)
    encrypted_image.save(encrypted_image_path)

    try:
        # First decrypt the encrypted image
        decrypted_image_path = decrypt_image(encrypted_image_path, password)
        
        # Then perform steganography with the decrypted image
        stego_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'stego_image.png')
        lsb_hide(cover_image_path, decrypted_image_path, stego_image_path)
        
        flash(f'Steganography completed successfully. <a href="{url_for("download_file", filename="stego_image.png")}">Download Stego Image</a>', 'success')
    except Exception as e:
        flash(f'Error during steganography process: {str(e)}')
    
    return redirect(url_for('index'))

@app.route('/retrieve_encrypted_image', methods=['POST'])
def retrieve_encrypted_image():
    if 'stego_image' not in request.files:
        flash('Please provide a stego image.')
        return redirect(url_for('index'))

    stego_image = request.files['stego_image']

    if stego_image.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))

    stego_image_path = os.path.join(app.config['UPLOAD_FOLDER'], stego_image.filename)
    stego_image.save(stego_image_path)

    try:
        # Calculate the length of hidden data
        secret_data_length = get_secret_data_length(stego_image_path)

        # Extract the hidden image from stego image
        extracted_data = lsb_retrieve(stego_image_path, secret_data_length)

        # Save the extracted image
        extracted_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'extracted_image.png')
        with open(extracted_image_path, 'wb') as ext_file:
            ext_file.write(extracted_data)

        flash(f'Image extracted successfully. <a href="{url_for("download_file", filename="extracted_image.png")}">Download Extracted Image</a>', 'success')
    except Exception as e:
        flash(f'Error during extraction process: {str(e)}')

    return redirect(url_for('index'))

@app.route('/metrics', methods=['POST'])
def metrics():
    if 'cover_image' not in request.files or 'stego_image' not in request.files:
        flash('Please provide both a cover image and a stego image.')
        return redirect(url_for('index'))

    cover_image = request.files['cover_image']
    stego_image = request.files['stego_image']

    if cover_image.filename == '' or stego_image.filename == '':
        flash('No selected files')
        return redirect(url_for('index'))

    cover_image_path = os.path.join(app.config['UPLOAD_FOLDER'], cover_image.filename)
    stego_image_path = os.path.join(app.config['UPLOAD_FOLDER'], stego_image.filename)
    cover_image.save(cover_image_path)
    stego_image.save(stego_image_path)

    # Calculate MSE and PSNR
    mse, psnr = calculate_mse_psnr(cover_image_path, stego_image_path)

    # Perform histogram analysis
    output_histogram_path = os.path.join(app.config['UPLOAD_FOLDER'], 'histogram_comparison.png')
    plot_image_histograms(cover_image_path, stego_image_path, output_histogram_path)

    # Display results on the web page
    flash(f'MSE: {mse:.6f}, PSNR: {psnr:.6f} dB')
    flash(f'Histogram analysis image generated. <a href="{url_for("download_file", filename="histogram_comparison.png")}">Download Histogram Image</a>', 'success')

    return redirect(url_for('index'))

@app.route('/download_file/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
