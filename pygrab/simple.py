from pygrab import yuv
import serial

ser = serial.Serial('/dev/cu.usbmodem14101', baudrate=9600)

while True:
    x = ser.read(1)
    if x != b'R':
        continue
    x = ser.read(1)
    if x != b'D':
        continue
    x = ser.read(1)
    if x != b'Y':
        continue
    break

print('image found')

result = bytearray()

for row in range(320):
    for col in range(240):
        result += ser.read(1)
        result += ser.read(1)
        print(result[-2:])



# convert to YUV image data
rgb = bytearray()
for pixel_index in range(0, len(result), 4):
    window = result[pixel_index:pixel_index+4]
    rgb += bytes((
        yuv.YUV2R(window[1], window[0], window[2]),
        yuv.YUV2G(window[1], window[0], window[2]),
        yuv.YUV2B(window[1], window[0], window[2]),
        yuv.YUV2R(window[3], window[0], window[2]),
        yuv.YUV2G(window[3], window[0], window[2]),
        yuv.YUV2B(window[3], window[0], window[2])))


with open('simple.rgb', mode='wb') as handle:
    handle.write(rgb)

with open('simple.yuv', mode='wb') as handle:
    handle.write(result)
