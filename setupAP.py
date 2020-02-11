import os
import threading
import queue
import re
import time
import pandas as pd
import aruba



thread_num = 100

APs = pd.read_excel('data/devices.xlsx',index_col=0)

#Q = queue.Queue(thread_num)




if __name__=='__main__':
    #if os.path.exists('fail.txt') :
    #   os.remove('fail.txt')
    APs = pd.read_excel('data/devices.xlsx')
    devices = APs.drop(['Old_Version', 'Factory_Reset', 'Upgrade', 'Configuration'], axis=1).to_dict(orient='records')
    APs.set_index('AP',inplace=True)

    t0 = time.time()

    print('----------Setup AP is starting----------')


    threads = []
    for device in devices:
        t = threading.Thread(target=aruba.run_cmd,args=(device,APs))
        t.setDaemon(True)
        t.start()
        threads.append(t)

    for thread in threads:
        print(thread)
        thread.join()
 #   Q.join()

    t1 = time.time()

    filename = 'data/result_' + time.strftime("%Y%m%d%H%M%S",time.localtime(t1)) +'.xlsx'
    APs.to_excel(filename)

    print('----------Setup AP is finished----------')
    print('Time:{} minutes'.format(round(t1-t0)/60))