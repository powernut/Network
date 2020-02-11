import netmiko
import re
import threading
import time

os_ver = '6.5.4.15'  # AP's OS version need to be same as this one
netmiko_exceptions = (netmiko.ssh_exception.NetMikoTimeoutException,
                      netmiko.ssh_exception.NetMikoAuthenticationException)
Qlock = threading.Lock()


# To make print not interrupt by other thread
def print_info(msg):
    Qlock.acquire()
    print(msg)
    Qlock.release()


'''
# This is another way to handle continue process of command.
def handle_continue(net_connect, cmd):
    net_connect.remote_conn.sendall(cmd)
    time.sleep(1)
    output = net_connect.remote_conn.recv(65535).decode('utf-8')
    #print("handle_continue:")
    # print(output)
    if 'y/n' in output:
        net_connect.remote_conn.sendall('y\n')
        output += net_connect.remote_conn.recv(65535).decode('utf-8')
        net_connect.disconnect()
        return output
'''


def handle_continue(net_connect, cmd):
    # send_command_timing as the router prompt is not returned
    output = net_connect.send_command_timing(cmd, strip_command=False, strip_prompt=False)
    if "y/n" in output:
        output += net_connect.send_command_timing("y\n", strip_command=False, strip_prompt=False)
    return output


def need_upgrade(sh_ver, mac):
    ap_ver = re.findall("Version (.*)", sh_ver)[0]
    print_info("AP:{} version:{}".format(mac, ap_ver))
    return False if ap_ver.strip() == os_ver else True


def upgrade_os(net_connect):
    output = net_connect.send_command('upgrade-image tftp://192.168.20.2/AlcatelInstant_Pegasus_6.5.4.15_73677')
    net_connect.disconnect()
    return output


def config_ap(net_connect, mac):
    cmd = "copy tftp 192.168.20.2 backup0129.cfg system config"
    # print("Download AP configuration \n" + cmd)

    output = net_connect.send_command(cmd)
    # print(output)
    if 'please reboot the AP' in output:
        print_info("Will reload the AP:" + mac)
        output = handle_continue(net_connect, 'reload\n')
        net_connect.disconnect()
        output = 'Successfully upload configuration, will reload AP:' + mac + '\nMessage:' + output
        return output
    else:
        output = 'Fail to copy configuration to AP:' + mac + '\nMessage: ' + output
        return output


def connect_ssh(host):
    net_connect = netmiko.ConnectHandler(**host)
    print_info("Connected to AP:{}".format(net_connect.find_prompt()))
    return net_connect


def check_status(net_connect):
    pass


def run_cmd(device, aps):
    mac = device.pop('AP')
    # Q.put(device)
    print_info("----------Start to Set AP:" + mac)

    print_info("Reset to Factory default setting for AP:" + mac)
    try:
        device["password"] = 'switch'
        connection = connect_ssh(device)
        # Factory Reset
        output = handle_continue(connection, "write erase all reboot\n")
        print_info('AP: ' + mac + output)
        if 'y/n' in output:
            print_info('AP: ' + mac + ' passed factory reset step')
            time.sleep(500)
            aps.loc[mac, 'Factory_Reset'] = 'OK'
        else:
            print_info('Failed to reset AP:' + mac)
            aps.loc[mac, 'Factory_Reset'] = 'Failed'
    except netmiko_exceptions as ex:
        print('Failed to factory reset ', mac, ex)
        return

    print_info("upgrade step for AP:" + mac)
    try:
        connection = connect_ssh(device)
        # Upgrade if os version is different
        output = connection.send_command('show version')
        # print(output)
        if need_upgrade(output, mac):
            print_info("Start to upgrade AP: " + mac)
            upgrade_os(connection)
            time.sleep(500)
        else:
            print_info("No need to upgrade AP: " + mac)
        print_info('AP: ' + mac + ' passed upgrade step')
        aps.loc[mac, 'Upgrade'] = 'OK'
    except netmiko_exceptions as ex:
        print('Failed to Upgrade', mac, ex)
        return

    print_info("Upload configuration step for AP: " + mac)
    try:
        connection = connect_ssh(device)
        output = config_ap(connection, mac)
        print_info(output)
        if 'Successfully upload configuration' in output:
            time.sleep(500)
            aps.loc[mac, 'Configuration'] = 'OK'
        else:
            aps.loc[mac, 'Configuration'] = 'Failed'

    except netmiko_exceptions as ex:
        print('Failed to upload configuration ', mac, ex)

    print_info('Check AP:' + mac + 'status')
    try:
        connection = connect_ssh(device)
        check_status(connection)

    except netmiko_exceptions as ex:
        print("Failed to Check AP ", mac, ex)

    # Q.get(host)
    # Q.task_done()
