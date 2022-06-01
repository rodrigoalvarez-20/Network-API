from multiprocessing import Process

from api.utils.monitor import run_service as run_monitor
from api.utils.notify import notify_daemon as run_notifier
from api.utils.topology_mapper import run_daemon as run_mapper
from api.utils.topology_mapper import run_daemon as run_trappy

process_list = []
proc_monitor = Process(target=run_monitor, name="Monitor_Process", daemon=True)
proc_mapper = Process(target=run_mapper, name="Mapper_Process", daemon=True)
#proc_traps 
proc_notify = Process(target=run_notifier, name="Email_Service", daemon=True)

process_list.append(proc_monitor)
process_list.append(proc_mapper)
process_list.append(proc_notify)

for p in process_list:
    p.start()


try:
    while (True):
        pass
except KeyboardInterrupt:
    print("Finalizando los procesos...")
    for p in process_list:
        p.terminate()

