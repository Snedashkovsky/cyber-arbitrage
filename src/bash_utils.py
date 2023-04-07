from sys import stdout
import json
from time import sleep
from typing import Optional
from subprocess import Popen, PIPE


def display_sleep(delay_time: int) -> None:
    for remaining in range(delay_time, -1, -1):
        stdout.write("\r")
        stdout.write("{:2d} from {:2d} seconds remaining.".format(remaining, delay_time))
        stdout.flush()
        sleep(1)
    stdout.write("\n")


def execute_bash(bash_command: str, shell: bool = False,
                 timeout: Optional[int] = 15) -> tuple[Optional[str], Optional[str]]:
    if len(bash_command.split('"')) == 1:
        _bash_command_list = bash_command.split()
    elif len(bash_command.split('"')) == 2:
        _bash_command_list = \
            bash_command.split('"')[0].split() + \
            [bash_command.split('"')[1]]
    elif len(bash_command.split('"')) > 2:
        _bash_command_list = \
            bash_command.split('"')[0].split() + \
            [bash_command.split('"')[1]] + \
            [item for items in bash_command.split('"')[2:] for item in items.split()]
    else:
        return None, f'Cannot split bash command {bash_command}'
    popen_process = Popen([bash_command], stdout=PIPE, shell=shell, text=True) \
        if shell else Popen(_bash_command_list, stdout=PIPE)
    return popen_process.communicate(timeout=timeout)


def get_json_from_bash_query(bash_command: str, shell: bool = False,
                             timeout: Optional[int] = 15) -> Optional[dict]:
    _res, _ = execute_bash(bash_command, shell=shell, timeout=timeout)
    if _res:
        return json.loads(_res.decode('utf8').replace("'", '"'))
    return
