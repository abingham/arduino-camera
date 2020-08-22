import logging
from itertools import islice
from pathlib import Path
import serial

import click

log = logging.getLogger(__name__)


def _read_images(ser: serial.Serial):
    IMAGE_MARKER = b'RDY'
    buffer = b''
    while True:
        incoming = ser.read(ser.in_waiting)
        buffer += incoming  # read(ser, 1)
        # print(buffer.count(IMAGE_MARKER), len(incoming))
        while buffer.count(IMAGE_MARKER) > 1:
            parts = buffer.split(IMAGE_MARKER)
            print(list(map(len, parts)))
            yield parts[1]
            buffer = IMAGE_MARKER + IMAGE_MARKER.join(parts[2:])


def read_images(ser: serial.Serial):
    FRAME_START = b'\x00\x01'
    LINE_END = b'\x00\x02'
    buffer = b''
    while True:
        incoming = ser.read(2)
        if incoming:
            print(len(incoming), incoming, (incoming[1] << 8) + incoming[0])
            # buffer += incoming

        continue

        print('Frame starts:', buffer.count(FRAME_START))

        while buffer.count(FRAME_START) > 1:
            print('Image detected')
            parts = buffer.split(FRAME_START)

            buffer = FRAME_START + FRAME_START.join(parts[2:])

            image = parts[1]
            if len(image) < 5:
                log.error(f'Header too short. Expected >= 5, received {len(image)}.')
                continue

            # 2-byte width, 2-bytes height, 1-byte format 
            width = (image[0] << 8) + image[1]
            height = (image[2] << 8) + image[3]
            image_format = image[4]

            print(f'width: {width} heigh: {height} format: {image_format}')

            expected_size = 5 + width * height * 2 + height * len(LINE_END)
            print(f'size: {len(image)}, expected size: {expected_size}')
            if len(image) != expected_size:
                log.error(f'Image too short. Expected {expected_size}, received {len(image)}.')
                continue

            yield image[5:].replace(LINE_END, b'')

            ser.send_break()


@ click.command()
@ click.argument('filename')
# @click.argument('width', type=int)
# @click.argument('height', type=int)
@ click.argument('output')
@ click.option('--baudrate', type=int, default=1000000)
@ click.option('--count', type=int, default=1)
def main(filename, output, baudrate, count):
    logging.basicConfig(level=logging.INFO)

    ser = serial.Serial(filename, baudrate=baudrate)  # open serial port
    ser = serial.Serial(
        filename,
        baudrate=baudrate,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=None,
        xonxoff=False,
        rtscts=False,
        write_timeout=None,
        dsrdtr=False,
        inter_byte_timeout=None,
        exclusive=None)
    log.info('Port opened')
    # serial_data = wait_for_image(ser)

    # We (assume) we read row-major YUV422 data now
    # YUV422 is 4 bytes per 2 pixels.
    # total_image_size = width * height * 2

    # extend the image buffer to hold the rest of the image
    # remaining_data_size = total_image_size - len(serial_data)

    # read the rest of the image data
    # serial_data += bytearray(read(ser, remaining_data_size))

    output = Path(output)
    for idx, image in enumerate(islice(read_images(ser), count)):
        # image = bytes(yuv422_to_rgb(image))
        outname = f'{output.stem}_{idx}{output.suffix}'
        print(f'saving image {outname}, size {len(image)}')
        with open(outname, mode='wb') as handle:
            handle.write(image)
