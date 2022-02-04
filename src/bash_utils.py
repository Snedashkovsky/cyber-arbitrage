import json
from subprocess import Popen, PIPE


def execute_bash(bash_command: str):
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
    popen_process = Popen(_bash_command_list, stdout=PIPE)
    return popen_process.communicate(timeout=15)


def get_json_from_bash_query(bash_command: str):
    _res = execute_bash(bash_command)
    if _res[0]:
        return json.loads(_res[0].decode('utf8').replace("'", '"'))
    return
