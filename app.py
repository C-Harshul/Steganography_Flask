from flask import Flask, jsonify, request
import wave
from random import randint
import os 
import datetime
import pyrebase
import cv2
import numpy as np


def to_bin(data):
    """Convert `data` to binary format as string"""
    if isinstance(data, str):
        return ''.join([ format(ord(i), "08b") for i in data ])
    elif isinstance(data, bytes) or isinstance(data, np.ndarray):
        return [ format(i, "08b") for i in data ]
    elif isinstance(data, int) or isinstance(data, np.uint8):
        return format(data, "08b")
    else:
        raise TypeError("Type not supported.")

def encode(image_name, secret_data):
    # read the image
    image = cv2.imread(image_name)
    # maximum bytes to encode
    n_bytes = image.shape[0] * image.shape[1] * 3 // 8
    print("[*] Maximum bytes to encode:", n_bytes)
    if len(secret_data) > n_bytes:
        raise ValueError("[!] Insufficient bytes, need bigger image or less data.")
    print("[*] Encoding data...")
    # add stopping criteria
    secret_data += "====="
    data_index = 0
    # convert data to binary
    binary_secret_data = to_bin(secret_data)
    # size of data to hide
    data_len = len(binary_secret_data)
    for row in image:
        for pixel in row:
            # convert RGB values to binary format
            r, g, b = to_bin(pixel)
            # modify the least significant bit only if there is still data to store
            if data_index < data_len:
                # least significant red pixel bit
                pixel[0] = int(r[:-1] + binary_secret_data[data_index], 2)
                data_index += 1
            if data_index < data_len:
                # least significant green pixel bit
                pixel[1] = int(g[:-1] + binary_secret_data[data_index], 2)
                data_index += 1
            if data_index < data_len:
                # least significant blue pixel bit
                pixel[2] = int(b[:-1] + binary_secret_data[data_index], 2)
                data_index += 1
            # if data is encoded, just break out of the loop
            if data_index >= data_len:
                break
    return image

def decode(image_name):
    print("[+] Decoding...")
    # read the image
    image = cv2.imread(image_name)
    binary_data = ""
    for row in image:
        for pixel in row:
            r, g, b = to_bin(pixel)
            binary_data += r[-1]
            binary_data += g[-1]
            binary_data += b[-1]
    # split by 8-bits
    all_bytes = [ binary_data[i: i+8] for i in range(0, len(binary_data), 8) ]
    # convert from bits to characters
    decoded_data = ""
    for byte in all_bytes:
        decoded_data += chr(int(byte, 2))
        if decoded_data[-5:] == "=====":
            break
    return decoded_data[:-5]

config = {
    "apiKey": "AIzaSyB7wxqgXupAMqE31FJwnoDNb-t3eKTHCqk",
    "authDomain": "steganography-fafb3.firebaseapp.com",
    "databaseURL":"https://steganography-fafb3-default-rtdb.asia-southeast1.firebasedatabase.app/",
    "projectId": "steganography-fafb3",
    "storageBucket": "steganography-fafb3.appspot.com",
    "messagingSenderId": "747245124931",
    "appId": "1:747245124931:web:640cac52195cd38fbf03f6",
}

firebase = pyrebase.initialize_app(config)

storage = firebase.storage()

# creating a Flask app
app = Flask(__name__)
songList = ['song.wav','song2.wav','song3.wav']
imageList = ['firebase.png','mongo.png','node.png']

@app.route('/read/<string:timestamp>', methods=['GET'])
async def read(timestamp):

    fileName = timestamp + ".wav"
    print(fileName)
    storageLocation = "audio/" + fileName
  
    storage.child(storageLocation).download(fileName)
    song = wave.open(fileName, mode='rb')
# Convert audio to byte array
    frame_bytes = bytearray(list(song.readframes(song.getnframes())))

# Extract the LSB of each byte
    extracted = [frame_bytes[i] & 1 for i in range(len(frame_bytes))]
# Convert byte array back to string
    string = "".join(chr(
        int("".join(map(str, extracted[i:i+8])), 2)) for i in range(0, len(extracted), 8))
# Cut off at the filler characters
    decoded = string.split("###")[0]

# Print the extracted text
    print("Sucessfully decoded: "+decoded)
    song.close()
    os.remove(fileName)
    return jsonify({'data': decoded})

@app.route('/read_image/<string:timestamp>', methods=['GET'])
async def read_image(timestamp):
    image = timestamp + ".png"
    
    storageLocation = "images/" + image
  
    storage.child(storageLocation).download(image)
    decoded_data = decode(image)
    os.remove(image)
    return jsonify({'data': decoded_data})



@app.route('/hide/<string:message>', methods=['GET'])
async def disp(message):
    ts = datetime.datetime.now().strftime("%m:%d:%Y %H:%M:%S")
    print(ts)
    fileName = ts + ".wav"
    print(fileName)
    index = randint(0, 2)
    print(index)
    songName = songList[index]
    song = wave.open(songName, mode='rb')
    frame_bytes = bytearray(list(song.readframes(song.getnframes())))
    print(frame_bytes)
    string = message
    string = string + int((len(frame_bytes)-(len(string)*8*8))/8) * '#'
    bits = list(
        map(int, ''.join([bin(ord(i)).lstrip('0b').rjust(8, '0') for i in string])))

    for i, bit in enumerate(bits):
        frame_bytes[i] = (frame_bytes[i] & 254) | bit
    frame_modified = bytes(frame_bytes)
    with wave.open(fileName, 'wb') as fd:
        fd.setparams(song.getparams())
        fd.writeframes(frame_modified)
    song.close()
    storageLocation = "audio/" + fileName
    storage.child(storageLocation).put(fileName)
    print("Uploaded")
    os.remove(fileName)
    return jsonify({'data': message,'timestamp':ts})



@app.route('/hide_in_image/<string:message>', methods=['GET'])
async def upload_file(message):
    ts = datetime.datetime.now().strftime("%m:%d:%Y %H:%M:%S")
    index = randint(0,2)
    imageName = imageList[index]
    encoded_image = encode(image_name=imageName, secret_data=message)
    output_image = ts+".png"
    cv2.imwrite(output_image, encoded_image)
    # decode the secret data from the image
    decoded_data = decode(output_image)
    storageLocation = "images/" + output_image
    storage.child(storageLocation).put(output_image)
    print("Uploaded")
    os.remove(output_image)
    return jsonify({"data":message,"timestamp":ts})
    
# driver function
if __name__ == '__main__':

    app.run(debug=True)
