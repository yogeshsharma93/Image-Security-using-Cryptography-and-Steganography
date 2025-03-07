Image Security Using Cryptography and Steganography

Overview

This project implements a hybrid approach to image security by integrating Advanced Encryption Standard (AES) cryptography with Least Significant Bit (LSB) steganography. AES ensures robust encryption of sensitive data, while LSB steganography conceals the encrypted data within an image, providing an additional layer of security. This dual-layer mechanism enhances confidentiality, making it resilient against cryptographic and steganographic attacks.

Features

AES Encryption: Encrypts image data for secure transmission.

LSB Steganography: Hides encrypted data within another image.

Dual-Layer Security: Provides both encryption and imperceptible data hiding.

Robustness Evaluation: Analyzes security and image quality using PSNR and MSE metrics.

Secure Image Transmission: Protects against unauthorized access and detection.

Technologies Used

Python

AES Encryption (PyCryptodome library)

LSB Steganography (PIL, NumPy)

OpenCV for image processing
