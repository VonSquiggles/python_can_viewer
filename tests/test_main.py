#!/usr/bin/python
#
# Copyright (C) 2018 Kristian Sloth Lauszus. All rights reserved.
#
# Contact information
# -------------------
# Kristian Sloth Lauszus
# Web      :  http://www.lauszus.com
# e-mail   :  lauszus@gmail.com

import curses
import datetime
import operator
import struct
import sys
import time

import can
import pytest

from python_can_viewer import *


@pytest.fixture(scope='module')
def can_bus():  # type: (None) -> can.Bus
    _can_bus = can.interface.Bus(channel='can0', bustype='virtual', receive_own_messages=True)
    yield _can_bus


# noinspection PyShadowingNames
def test_canopen(can_bus):
    # NMT
    data = [2, 1]  # cmd = stop node, node ID = 1
    msg = can.Message(arbitration_id=CANOPEN_NMT, data=data, extended_id=False)
    can_bus.send(msg)
    assert operator.eq(parse_canopen_message(msg), ('NMT', '0x01'))

    msg = can.Message(arbitration_id=CANOPEN_NMT, data=data, extended_id=True)  # CANopen do not use an extended id
    can_bus.send(msg)
    assert operator.eq(parse_canopen_message(msg), (None, None))

    # The ID is not added to the NMT function code
    msg = can.Message(arbitration_id=CANOPEN_NMT + 1, data=data, extended_id=False)
    can_bus.send(msg)
    assert operator.eq(parse_canopen_message(msg), (None, None))

    data = [2, 128]  # cmd = stop node, node ID = invalid id
    msg = can.Message(arbitration_id=CANOPEN_NMT, data=data, extended_id=False)
    can_bus.send(msg)
    assert operator.eq(parse_canopen_message(msg), (None, None))

    data = [1, 0]  # cmd = start node, node ID = all
    msg = can.Message(arbitration_id=CANOPEN_NMT, data=data, extended_id=False)
    can_bus.send(msg)
    assert operator.eq(parse_canopen_message(msg), ('NMT', 'ALL'))

    # SYNC
    # The ID is not added to the SYNC function code
    msg = can.Message(arbitration_id=CANOPEN_SYNC_EMCY + 1, data=None, extended_id=False)
    can_bus.send(msg)
    assert operator.eq(parse_canopen_message(msg), (None, None))

    data = [1, 2, 3, 4, 5, 6, 7, 8]  # Wrong length
    msg = can.Message(arbitration_id=CANOPEN_SYNC_EMCY, data=data, extended_id=False)
    can_bus.send(msg)
    assert operator.eq(parse_canopen_message(msg), (None, None))

    msg = can.Message(arbitration_id=CANOPEN_SYNC_EMCY, data=None, extended_id=False)
    can_bus.send(msg)
    assert operator.eq(parse_canopen_message(msg), ('SYNC', None))

    # EMCY
    data = [1, 2, 3, 4, 5, 6, 7]  # Wrong length
    msg = can.Message(arbitration_id=CANOPEN_SYNC_EMCY + 1, data=data, extended_id=False)
    can_bus.send(msg)
    tmp = parse_canopen_message(msg)
    assert operator.eq(tmp, (None, None))

    data = [1, 2, 3, 4, 5, 6, 7, 8]
    msg = can.Message(arbitration_id=CANOPEN_SYNC_EMCY + 128, data=data, extended_id=False)  # Invalid ID
    can_bus.send(msg)
    assert operator.eq(parse_canopen_message(msg), (None, None))

    msg = can.Message(arbitration_id=CANOPEN_SYNC_EMCY + 1, data=data, extended_id=False)
    can_bus.send(msg)
    assert operator.eq(parse_canopen_message(msg), ('EMCY', '0x01'))

    # TIME
    one_day_seconds = 24 * 60 * 60
    offset = datetime.datetime(year=1984, month=1, day=1)
    now = datetime.datetime.now()
    delta = (now - offset).total_seconds()
    days, seconds = divmod(delta, one_day_seconds)
    time_struct = struct.Struct('<LH')
    data = time_struct.pack(round(seconds * 1000), int(days))
    msg = can.Message(arbitration_id=CANOPEN_TIME, data=data, extended_id=False)
    can_bus.send(msg)
    assert operator.eq(parse_canopen_message(msg), ('TIME', None))

    # The ID is not added to the TIME function code
    msg = can.Message(arbitration_id=CANOPEN_TIME + 1, data=data, extended_id=False)
    can_bus.send(msg)
    assert operator.eq(parse_canopen_message(msg), (None, None))

    # milliseconds, days = time_struct.unpack(data)
    # seconds = days * one_day_seconds + milliseconds / 1000.
    # now_unpacked = datetime.datetime.utcfromtimestamp(
    #     seconds + (offset - datetime.datetime.utcfromtimestamp(0)).total_seconds())

    # TPDO1, RPDO1, TPDO2, RPDO2, TPDO3, RPDO3, TPDO4, RPDO4
    data = [1, 2, 3, 4, 5, 6, 7, 8]
    for i, func_code in enumerate([CANOPEN_TPDO1, CANOPEN_RPDO1, CANOPEN_TPDO2, CANOPEN_RPDO2,
                                   CANOPEN_TPDO3, CANOPEN_RPDO3, CANOPEN_TPDO4, CANOPEN_RPDO4]):
        node_id = i + 1
        msg = can.Message(arbitration_id=func_code + node_id, data=data, extended_id=False)
        can_bus.send(msg)
        assert operator.eq(parse_canopen_message(msg), (canopen_function_codes[func_code], '0x{0:02X}'.format(node_id)))

    # SDO_TX
    data = [1, 2, 3, 4, 5, 6, 7, 8]
    msg = can.Message(arbitration_id=CANOPEN_SDO_TX + 0x10, data=data, extended_id=False)
    can_bus.send(msg)
    assert operator.eq(parse_canopen_message(msg), ('SDO_TX', '0x10'))

    # SDO_RX
    msg = can.Message(arbitration_id=CANOPEN_SDO_RX + 0x20, data=data, extended_id=False)
    can_bus.send(msg)
    assert operator.eq(parse_canopen_message(msg), ('SDO_RX', '0x20'))

    # HEARTBEAT
    data = [0x05]  # Operational
    msg = can.Message(arbitration_id=CANOPEN_HEARTBEAT + 0x7F, data=data, extended_id=False)
    can_bus.send(msg)
    assert operator.eq(parse_canopen_message(msg), ('HEARTBEAT', '0x7F'))

    # LSS_TX
    data = [1, 2, 3, 4, 5, 6, 7, 8]
    msg = can.Message(arbitration_id=CANOPEN_LSS_TX, data=data, extended_id=False)
    can_bus.send(msg)
    assert operator.eq(parse_canopen_message(msg), ('LSS_TX', None))

    # LSS_RX
    msg = can.Message(arbitration_id=CANOPEN_LSS_RX, data=data, extended_id=False)
    can_bus.send(msg)
    assert operator.eq(parse_canopen_message(msg), ('LSS_RX', None))

    # Send non-CANopen message
    msg = can.Message(arbitration_id=0x101, data=data, extended_id=False)
    can_bus.send(msg)
    assert operator.eq(parse_canopen_message(msg), (None, None))

    # Send the same command, but with another data length
    data = [1, 2, 3, 4, 5, 6]
    msg = can.Message(arbitration_id=0x101, data=data, extended_id=False)
    can_bus.send(msg)
    assert operator.eq(parse_canopen_message(msg), (None, None))

    # Message with extended id
    data = [1, 2, 3, 4, 5, 6, 7, 8]
    msg = can.Message(arbitration_id=0x123456, data=data, extended_id=True)
    can_bus.send(msg)
    assert operator.eq(parse_canopen_message(msg), (None, None))

    # Send the same message again to make sure that resending works
    time.sleep(.1)
    can_bus.send(msg)


# For converting the EMCY and HEARTBEAT messages
data_structs = {
    0x080 + 0x01: struct.Struct('<HBLB'),
    0x700 + 0x7F: struct.Struct('<B'),
}


def test_receive(can_bus):
    ids = {}
    start_time = time.time()

    # Receive the messages we just sent in 'test_canopen'
    while 1:
        msg = can_bus.recv(timeout=0)
        if msg is not None:
            id = draw_can_bus_message(None, ids, start_time, data_structs, msg)
            if id['msg'].arbitration_id == 0x101:
                # Check if the counter is reset when the length has changed
                assert id['count'] == 1
            elif id['msg'].arbitration_id == 0x123456:
                # Check if the counter is incremented
                if id['dt'] == 0:
                    assert id['count'] == 1
                else:
                    assert id['count'] == 2
                    assert pytest.approx(id['dt'], 0.1)  # dt should be ~0.1 s
            else:
                # Make sure dt is 0
                if id['count'] == 1:
                    assert id['dt'] == 0
        else:
            break


def test_pack_unpack():
    data_structs = {
        # CANopen node 1
        CANOPEN_TPDO1 + 1: struct.Struct('<bBh2H'),
        CANOPEN_TPDO2 + 1: (struct.Struct('<HHB'), 100., 10., 1),
        CANOPEN_TPDO3 + 1: struct.Struct('<ff'),
        CANOPEN_TPDO4 + 1: (struct.Struct('<ff'), math.pi / 180., math.pi / 180.),
        CANOPEN_TPDO1 + 2: None,
        CANOPEN_TPDO2 + 2: struct.Struct('>lL'),
    }  # type: Dict[Union[bytes, Tuple[bytes, ...]], Union[struct.Struct, Tuple, None]]

    raw_data = pack_data(CANOPEN_TPDO1 + 1, data_structs, -7, 13, -1024, 2048, 0xFFFF)
    parsed_data = unpack_data(CANOPEN_TPDO1 + 1, data_structs, raw_data)
    assert parsed_data == [-7, 13, -1024, 2048, 0xFFFF]
    assert all(isinstance(d, int) for d in parsed_data)

    raw_data = pack_data(CANOPEN_TPDO2 + 1, data_structs, 12.34, 4.5, 6)
    parsed_data = unpack_data(CANOPEN_TPDO2 + 1, data_structs, raw_data)
    assert pytest.approx(parsed_data, [12.34, 4.5, 6])
    assert isinstance(parsed_data[0], float) and isinstance(parsed_data[1], float) and isinstance(parsed_data[2], int)

    raw_data = pack_data(CANOPEN_TPDO3 + 1, data_structs, 123.45, 67.89)
    parsed_data = unpack_data(CANOPEN_TPDO3 + 1, data_structs, raw_data)
    assert pytest.approx(parsed_data, [123.45, 67.89])
    assert all(isinstance(d, float) for d in parsed_data)

    raw_data = pack_data(CANOPEN_TPDO4 + 1, data_structs, math.pi / 2., math.pi)
    parsed_data = unpack_data(CANOPEN_TPDO4 + 1, data_structs, raw_data)
    assert pytest.approx(parsed_data, [math.pi / 2., math.pi])
    assert all(isinstance(d, float) for d in parsed_data)

    raw_data = pack_data(CANOPEN_TPDO1 + 2, data_structs)
    parsed_data = unpack_data(CANOPEN_TPDO1 + 2, data_structs, raw_data)
    assert parsed_data == b''
    assert isinstance(parsed_data, bytes)

    raw_data = pack_data(CANOPEN_TPDO2 + 2, data_structs, -2147483648, 0xFFFFFFFF)
    parsed_data = unpack_data(CANOPEN_TPDO2 + 2, data_structs, raw_data)
    assert parsed_data == [-2147483648, 0xFFFFFFFF]
    assert all(isinstance(d, int) for d in parsed_data)


def main(stdscr):
    # Used to automatically break out after the messages has been sent
    wait_for_quit = True
    if len(sys.argv) > 1:
        wait_for_quit = sys.argv[1].lower() != 'false' and sys.argv[1] != '0'

    # Create a CAN-Bus interface
    can_bus = can.interface.Bus(channel='can0', bustype='virtual', receive_own_messages=True)

    # Do not wait for key inputs and disable the cursor
    stdscr.nodelay(True)
    curses.curs_set(0)

    # Initialise the ID dictionary and the start timestamp
    ids = {}
    start_time = time.time()

    # Send test messages
    test_canopen(can_bus)

    while 1:
        # Receive the messages we just sent
        msg = can_bus.recv(timeout=0)
        if msg is not None:
            draw_can_bus_message(stdscr, ids, start_time, data_structs, msg)
        elif not wait_for_quit:
            # Automatically exit when we are finished reading
            break
        else:  # pragma: no cover
            # Read the terminal input
            key = stdscr.getch()

            # Stop program if the user presses ESC or 'q'
            if key == KEY_ESC or key == ord('q'):
                break


if __name__ == '__main__':  # pragma: no cover
    # Catch ctrl+c
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
