from datetime import datetime
import time, subprocess
from utils.decorators import routes, LOGS_PATH
from pprint import pprint


def get_logger_output(logname = None):
    today = datetime.now().day
    file_name = f"{routes[logname]}*{today}.log" if logname else f"{LOGS_PATH}/*/*{today}.log"
    f = subprocess.getoutput(f"cat {file_name}").splitlines()

    if f[0].find("No such file or directory") != -1:
        return None

    f_fmt = list(filter(lambda x: x.find("* Detected change")
                 == -1 and x.find("/socket.io/") == -1, f))
    return f_fmt

if __name__ == "__main__":
    while(1):
        pprint(get_logger_output("users"))
        time.sleep(5)
    
