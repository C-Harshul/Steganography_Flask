import wave
import datetime
from flask import Flask, jsonify, request
  
# creating a Flask app
app = Flask(__name__)


@app.route('/read',methods = ['GET'])
def read():
    ts = datetime.datetime.now().timestamp()
    fileName = ts + ".wav"
    print(fileName)
    song = wave.open(fileName, mode='rb')
# Convert audio to byte array
    frame_bytes = bytearray(list(song.readframes(song.getnframes())))

# Extract the LSB of each byte
    extracted = [frame_bytes[i] & 1 for i in range(len(frame_bytes))]
# Convert byte array back to string
    string = "".join(chr(int("".join(map(str,extracted[i:i+8])),2)) for i in range(0,len(extracted),8))
# Cut off at the filler characters
    decoded = string.split("###")[0]

# Print the extracted text
    print("Sucessfully decoded: "+decoded)
    song.close()  
    return jsonify({'data': decoded}) 

@app.route('/hide/<string:message>', methods = ['GET'])
def disp(message):
    ts = datetime.datetime.now().strftime("%m:%d:%Y %H:%M:%S")
    print(ts)
    fileName = ts + ".wav"
    print(fileName)
    song = wave.open("song.wav", mode='rb')
    frame_bytes = bytearray(list(song.readframes(song.getnframes())))


    string=message
    string = string + int((len(frame_bytes)-(len(string)*8*8))/8) *'#'
    bits = list(map(int, ''.join([bin(ord(i)).lstrip('0b').rjust(8,'0') for i in string])))

    for i, bit in enumerate(bits):
        frame_bytes[i] = (frame_bytes[i] & 254) | bit
    frame_modified = bytes(frame_bytes)

    with wave.open(fileName, 'wb') as fd:
        fd.setparams(song.getparams())
        fd.writeframes(frame_modified)
    song.close()

    return jsonify({'data': message})
  
  
# driver function
if __name__ == '__main__':
  
    app.run(debug = True)


