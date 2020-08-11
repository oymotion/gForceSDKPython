from gforce import GForceProfile, NotifDataType, DataNotifFlags
import time
import threading
import struct

# An example of the callback function


def set_cmd_cb(resp):
    print('Command result: {}'.format(resp))


def get_firmware_version_cb(resp, firmware_version):
    print('Command result: {}'.format(resp))
    print('Firmware version: {}'.format(firmware_version))

# An example of the ondata


def ondata(data):
    if len(data) > 0:
        print('data.length = {0} \ncontent = {1}'.format(len(data), data))

        if data[0] == NotifDataType['NTF_QUAT_FLOAT_DATA'] and len(data) == 17:
            quat_iter = struct.iter_unpack('f', data[1:])
            quaternion = []
            for i in quat_iter:
                quaternion.append(i[0])
            print('quaternion:', quaternion)

        elif data[0] == NotifDataType['DNF_EMG_RAW'] and len(data) == 129:
            # Data for EMG CH0~CHn repeatly.
            # Resolution set in setEmgRawDataConfig:
            #   8: one byte for one channel
            #   12: two bytes in LSB for one channel.
            # eg. 8bpp mode, data[1] = channel[0], data[2] = channel[1], ... data[8] = channel[7]
            #                data[9] = channel[0] and so on
            # eg. 12bpp mode, {data[2], data[1]} = channel[0], {data[4], data[3]} = channel[1] and so on
            for i in range(1, 129):
                print(data[i])
            # end for


def print2menu():
    print('_'*75)
    print('0: Exit')
    print('1: Get Firmware Version')
    print('2: Toggle LED')
    print('3: Toggle Motor')
    print('4: Get Quaternion(press enter to stop)')
    print('5: Get Raw EMG data(press enter to stop)')
    print('6: Set Emg Raw Data Config')


if __name__ == '__main__':
    while True:
        GF = GForceProfile()
        # Scan all gforces,return [[num,dev_name,dev_addr,dev_Rssi,dev_connectable],...]
        scan_results = GF.scan(5)

        # Display the first menu
        print('_'*75)
        print('0: exit')

        if scan_results == []:
            print('No bracelet was found')
        else:
            for d in scan_results:
                print(
                    '{0:<1}: {1:^16} {2:<18} Rssi={3:<3}, connectable:{4:<6}'.format(*d))

        # Handle user actions
        button = int(
            input('Please select the device you want to connect or exit:'))

        if button == 0:
            break
        else:
            addr = scan_results[button-1][2]
            GF.connect(addr)

            # Display the secord menu
            while True:
                time.sleep(1)
                print2menu()
                button = int(input('Please select a function or exit:'))

                if button == 0:
                    break

                elif button == 1:
                    GF.getControllerFirmwareVersion(
                        get_firmware_version_cb, 1000)

                elif button == 2:
                    GF.setLED(False, set_cmd_cb, 1000)
                    time.sleep(3)
                    GF.setLED(True, set_cmd_cb, 1000)

                elif button == 3:
                    GF.setMotor(True, set_cmd_cb, 1000)
                    time.sleep(3)
                    GF.setMotor(False, set_cmd_cb, 1000)

                elif button == 4:
                    GF.setDataNotifSwitch(
                        DataNotifFlags['DNF_QUATERNION'], set_cmd_cb, 1000)
                    GF.startDataNotification(ondata)

                    while True:
                        button = input()
                        if len(button) != 0:
                            GF.stopDataNotification()
                            GF.setDataNotifSwitch(
                                DataNotifFlags['DNF_OFF'], set_cmd_cb, 1000)
                            break

                elif button == 5:
                    GF.setDataNotifSwitch(
                        DataNotifFlags['DNF_EMG_RAW'], set_cmd_cb, 1000)

                    GF.startDataNotification(ondata)
                    button = input()

                    if len(button) != 0:
                        GF.stopDataNotification()
                        GF.setDataNotifSwitch(
                            DataNotifFlags['DNF_OFF'], set_cmd_cb, 1000)
                        break
                    time.sleep(1000)

                elif button == 6:
                    sampRate = eval(
                        input('Please enter sample value(defaults:650): '))
                    channelMask = eval(
                        input('Please enter channelMask value(defaults:0xFF): '))
                    dataLen = eval(
                        input('Please enter dataLen value(defaults:128): '))
                    resolution = eval(
                        input('Please enter resolution value(defaults:8): '))
                    GF.setEmgRawDataConfig(
                        sampRate, channelMask, dataLen, resolution, cb=set_cmd_cb, timeout=1000)
            break
