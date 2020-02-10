import netmiko
import re
import time
os_ver = '6.5.4.15'
ap_vc= {'ip':'192.168.20.13',
        'device_type':'aruba_os',
        'username':'admin',
        'password':'switch'}
netmiko_exceptions = (netmiko.ssh_exception.NetMikoTimeoutException,netmiko.ssh_exception.NetMikoAuthenticationException)

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

def need_upgrade(sh_ver):
    ap_ver = re.findall("Version (.*)" ,sh_ver)[0]
    print("AP:{} version:{}".format(ap_vc['ip'],ap_ver))
    if ap_ver.strip() == os_ver:
        print("No need to upgrade OS ")
        return False
    else:
        print("Upgrading AP:{}".format(ap_vc['ip']))
        return True

def upgrade_os(net_connect):
    print("Start to upgrade")
    output = net_connect.send_command('upgrade-image tftp://192.168.20.2/AlcatelInstant_Pegasus_6.5.4.15_73677')
    net_connect.disconnect()
    return output

def config_ap(net_connect):
    cmd = "copy tftp 192.168.20.2 backup0129.cfg system config"
    print("Download AP configuration \n" + cmd)

    output = net_connect.send_command(cmd)
    print(output)
    print("Will reload the AP.....")
    output = handle_continue (net_connect,'reload\n')
    net_connect.disconnect()
    return output

def connect_ssh(host):
    conn = netmiko.ConnectHandler(**host)
    print("Connected to AP:{}".format(conn.find_prompt()))
    return conn

def check_status(net_connect):
    pass

print("----------Start to Set AP----------")


print("Reset to Factory default setting")
try:
    connection = connect_ssh(ap_vc)
    #Factory Reset
    output = handle_continue(connection,"write erase all reboot\n")
    print(output)
    time.sleep(500)
except netmiko_exceptions as ex:
    print('Failed to ', ap_vc['ip'], ex)

print("Upgrade AP if needed")
try:
    ap_vc["password"] = 'admin'
    connection = connect_ssh(ap_vc)
    #Upgrade if os version is different
    output = connection.send_command('show version')
    print(output)
    if need_upgrade(output) :
        output = upgrade_os(connection)
        print(output)
        time.sleep(500)

except netmiko_exceptions as ex:
    print('Failed to ', ap_vc['ip'], ex)

print("Upload configuration")
try:

    ap_vc["password"] = 'admin'
    connection = connect_ssh(ap_vc)
    output = config_ap(connection)
    print(output)
    time.sleep(500)

except netmiko_exceptions as ex:
    print('Failed to ',ap_vc['ip'],ex)

print("Check AP status")
try:
    connection = connect_ssh(ap_vc)
    check_status(connection)

except netmiko_exceptions as ex:
    print("Failed to ",ap_vc['ip'],ex)