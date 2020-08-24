import logging
from itertools import islice
from pathlib import Path
import serial

import click

log = logging.getLogger(__name__)


def _read_ov7670_no_ram_arduino_uno(ser: serial.Serial):
    IMAGE_MARKER = b'\x00'
    IMAGE_HEADER_SIZE = 6
    buffer = b''

    # Wait for first image marker
    while IMAGE_MARKER not in buffer:
        buffer = ser.read(ser.in_waiting)

    # trim off everything before the image marker
    buffer = buffer[buffer.index(IMAGE_MARKER):]

    while True:
        # Wait for the rest of the header
        while len(buffer) < IMAGE_HEADER_SIZE:
            buffer += ser.read(ser.in_waiting)

        assert buffer.startswith(IMAGE_MARKER)

        # Determine the image size based on the header
        num_rows = (buffer[1] << 8) + buffer[2]
        num_cols = (buffer[3] << 8) + buffer[4]
        bytes_per_pixel = buffer[5]
        image_size = num_rows * num_cols * bytes_per_pixel
        log.info(f'image detected: rows={num_rows}, cols={num_cols}, bytes per pixel={bytes_per_pixel}, size={image_size}')

        # Trim off the header from the buffer
        buffer = buffer[IMAGE_HEADER_SIZE:]

        # Read image data
        while len(buffer) < image_size:
            buffer += ser.read(ser.in_waiting)

        assert IMAGE_MARKER not in buffer[:image_size]
        yield buffer[:image_size]

        buffer = buffer[image_size:]

    # # Read until first image marker is seen
    # while IMAGE_MARKER not in buffer:
    #     incoming = ser.read(ser.in_waiting)
    #     buffer += incoming  # read(ser, 1)

    # # Trim off everything up to and including the image marker
    # buffer = buffer[buffer.index(IMAGE_MARKER) + len(IMAGE_MARKER):]
 
    # # Now we know that we're receiving full frames
    # while True:
    #     incoming = ser.read(ser.in_waiting)
    #     buffer += incoming  # read(ser, 1)
    #     # print(buffer.count(IMAGE_MARKER), len(incoming))
    #     while buffer.count(IMAGE_MARKER) > 0:
    #         parts = buffer.split(IMAGE_MARKER)
    #         log.info(f'image detected, {len(parts[0])} bytes')
    #         yield parts[0]
    #         buffer = IMAGE_MARKER.join(parts[1:])


def _read_LiveOV7670(ser: serial.Serial):
    FRAME_START = b'\x00\x01'
    LINE_END = b'\x00\x02'
    buffer = b''
    while True:
        incoming = ser.read()
        buffer += incoming
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


def _read_bayer_rgb_640_480(ser: serial.Serial):
    FRAME_MARKER = b'*RDY*'

    buffer = b''
    while True:
        buffer += ser.read(ser.in_waiting)

        while buffer.count(FRAME_MARKER) > 1:
            log.info('Frame detected')
            parts = buffer.split(FRAME_MARKER)
            frame = parts[1]
            if len(frame) == 640 * 480:
                yield frame
            else:
                log.error(f'Frame size incorrect. Expected: {640 * 480}, Actual: {len(frame)}')
            buffer = FRAME_MARKER + FRAME_MARKER.join(parts[2:])

read_images = _read_bayer_rgb_640_480


@ click.command()
@ click.argument('filename')
# @click.argument('width', type=int)
# @click.argument('height', type=int)
@ click.argument('output')
@ click.option('--baudrate', type=int, default=1000000)
@ click.option('--count', type=int, default=1)
def main(filename, output, baudrate, count):
    logging.basicConfig(level=logging.INFO)

    log.info(f'Baud rate = {baudrate}')

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
