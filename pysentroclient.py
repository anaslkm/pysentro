import os
from pathlib import Path
import socket
import json
from struct import unpack

from sdk.sentro_command import SentroCommand
from sdk.sentro_telegram import Telegram

fpath = Path(os.path.dirname(__file__))
conf_path = Path("conf/config.json")

with open(fpath.parent / conf_path) as f:
    conf = json.load(f)


SERVER_PORT = 60000
SERVER_HOST = ""
BUFFERSIZE = 1028

client = socket.create_connection((SERVER_HOST, SERVER_PORT))

with client:

    commander = SentroCommand("SentroTestClientPy")

    cmd = commander.cmd_constructor("SingleMeasSample", "channel1", ["Sample"])

    client.sendall(cmd)

    msg_header = client.recv(conf['header_size'])
    if msg_header != b"":
        msg_length, msg_type = unpack(conf['header_format'], msg_header)

        telegram = b""
        total_recv_msg_length = 0
        while total_recv_msg_length < msg_length:
            tel_tmp = client.recv(BUFFERSIZE)
            if len(tel_tmp) == 0:
                break
            telegram += tel_tmp
            total_recv_msg_length = len(telegram)

            if msg_type == 0:
                print("recv msg : {}".format(telegram))
            elif msg_type == 11:
                telobj = Telegram(telegram)
                if telobj.contained_type == b"Sentronic.SentroCFBase.MeasurementOutput":
                    print(f"measurement on {telobj.data.channel_name}")
                    print(f"received nbr spectra {telobj.data.nbr_spectra}")
                    if telobj.data.error_msg != b"":
                        print(f"Error msg : {telobj.data.error_msg}")

                    if telobj.data.nbr_spectra > 0:
                        spectra = telobj.data.spectra_data
                    if telobj.data.results:
                        results = telobj.data.results
            else:
                print("received {}".format(conf["msg_types"].get(msg_type)))