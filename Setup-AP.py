import os
import threading
import queue
import time
import netmiko

thread_num = 100

Q = queue.Queue(thread_num)
Qlock = threading.Lock()

def print_info(msg):
    Qlock.acquire()
    print(msg)
    Qlock.release()

def get_devices():
    pass

def run_cmd(device):
    Q.put(device)
    try:
        pass
    except:
        pass
    finally:
        Q.get(host)
        Q.task_done()


if __name__=='__main__':
    if os.path.exists('fail.txt') :
        os.remove('fail.txt')

    devices = get_devices()

    t0 = time.time()
    print_info('----------Setup AP is starting----------')

    for device in devices:
        t = threading.Thread(target=run_cmd,args=(device))
        t.setDaemon(True)
        t.start()

    Q.join()

    t1 = time.time()
    print_info('----------Setup AP is finished----------')
    print('Time:{}s'.format(round(t1-t0,2)))

