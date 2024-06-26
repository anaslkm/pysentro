from struct import calcsize, pack
from pathlib import Path
import os
import json
from pprint import pprint


fpath = Path(os.path.dirname(__file__))
conf_path = Path("conf/config.json")

with open(fpath.parent / conf_path) as f:
    conf = json.load(f)


class SentroCommand:
    def __init__(self, client_id: str):
        self.client_id: str = client_id
        self.telegram_cmd: bytearray = None
        self.conf: dict = conf
        self.pointer_cmd: int = 0
        self.cmd_format: str = ""

    def print_params_options(self):
        print("\nParameter options list:")
        pprint(self.conf["params"])
        print()

    def cmd_param_constructor(self, telegram_tmp: bytearray, params: list = []):
        if len(params) == 0:
            telegram_tmp.append(0)
            self.cmd_format += "i"
        else:
            for param in params:
                telegram_tmp.append(param.encode("utf-8"))
                telegram_tmp.append(len(param))
                self.cmd_format += "s" + str(len(param))[::-1]
                self.cmd_format += "i"
        telegram_tmp.append(len(params))
        self.cmd_format += "b"
        return telegram_tmp

    def reset_command(self):
        self.cmd_format = ""
        self.pointer_cmd = 0
        self.telegram_cmd = None

    def cmd_constructor(self, cmd: str, channel: str = None, params: list = []):
        self.reset_command()
        telegram_send = [self.conf["cmds"][cmd]["encoding"]]
        self.cmd_format += "i"
        if channel is not None:
            telegram_send.append(channel.encode("utf-8"))
            self.cmd_format += "s" + str(len(channel))[::-1]
            telegram_send.append(len(channel))
        else:
            telegram_send.append(0)
        self.cmd_format += "i"
        telegram_send.append(int(self.conf["cmds"][cmd]["executed"]))
        self.cmd_format += "b"
        telegram_send.append(int(self.conf["cmds"][cmd]["requires_receipt"]))
        self.cmd_format += "b"
        telegram_send = self.cmd_param_constructor(telegram_send, params)
        
        telegram_send.append(self.conf["cmds"][cmd]["identifier"].encode("utf-8"))
        self.cmd_format += "s" + str(len(self.conf["cmds"][cmd]["identifier"]))[::-1]
        telegram_send.append(len(self.conf["cmds"][cmd]["identifier"]))
        self.cmd_format += "b"

        telegram_send.append(calcsize("<" + self.cmd_format[::-1]))
        self.cmd_format += "i"
        telegram_send.append(self.conf["cmds"][cmd]["contained_type"].encode("utf-8"))
        self.cmd_format += "s" + str(len(self.conf["cmds"][cmd]["contained_type"]))[::-1]
        telegram_send.append(len(self.conf["cmds"][cmd]["contained_type"]))
        self.cmd_format += "b"
        telegram_send.append(self.conf["cmds"][cmd]["recipient"].encode("utf-8"))
        telegram_send.append(len(self.conf["cmds"][cmd]["recipient"]))
        self.cmd_format += "s" + str(len(self.conf["cmds"][cmd]["recipient"]))[::-1]
        self.cmd_format += "b"
        telegram_send.append(self.client_id.encode("utf-8"))
        telegram_send.append(len(self.client_id))
        self.cmd_format += "s" + str(len(self.client_id))[::-1]
        self.cmd_format += "b"
        telegram_send.append(self.conf["cmds"][cmd]["type"])
        telegram_send.append(calcsize("<" + self.cmd_format[::-1]))
        self.cmd_format += "b"
        self.cmd_format += "i"
        self.cmd_format += "<"
        self.cmd_format = self.cmd_format[::-1]
        telegram = list(reversed(telegram_send))
        self.telegram_cmd = pack(self.cmd_format, *telegram)
        return self.telegram_cmd
