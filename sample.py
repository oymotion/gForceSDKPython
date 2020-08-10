from gforce import GForceProfile, NotifDataType, DataNotifFlags
import time
import threading
import struct

# An example of the callback function

def cmd_cb(resp,respdata):
    print('Command result: {}'.format(resp))
    print('raspdata:{}'.format(respdata))

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


def print2menu():
    print('_'*75)
    print('0: exit')
    print('1: Toggle LED')
    print('2: Toggle Motor')
    print('3: Get quaternion(press enter to stop)')
    print('4: Get raw EMG data(press enter to stop)')
    print('5:Set Emg Raw Data Config')


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
                    GF.setLED(False, cmd_cb, 1000)
                    time.sleep(3)
                    GF.getControllerFirmwareVersion(cmd_cb, 1000)

                elif button == 2:
                    GF.setMotor(True, cmd_cb, 1000)
                    time.sleep(3)
                    GF.setMotor(False, cmd_cb, 1000)

                elif button == 3:
                    GF.setDataNotifSwitch(
                        DataNotifFlags['DNF_QUATERNION'], cmd_cb, 1000)
                    GF.startDataNotification(ondata)
                    while True:
                        button = input()
                        if len(button) != 0:
                            GF.stopDataNotification()
                            break

                elif button == 4:
                    GF.setDataNotifSwitch(
                        DataNotifFlags['DNF_EMG_RAW'], cmd_cb, 1000)
                    GF.startDataNotification(ondata)
                    button = input()
                    if len(button) != 0:
                        GF.stopDataNotification()
                        break
                    time.sleep(1000)

                elif button == 5:
                    sampRate = eval(
                        input('Please enter sample value(defaults:650): '))
                    channelMask = eval(
                        input('Please enter channelMask value(defaults:0xFF): '))
                    dataLen = eval(
                        input('Please enter dataLen value(defaults:128): '))
                    resolution = eval(
                        input('Please enter resolution value(defaults:8): '))
                    GF.setEmgRawDataConfig(
                        sampRate, channelMask, dataLen, resolution, cb=cmd_cb, timeout=1000)
            break
