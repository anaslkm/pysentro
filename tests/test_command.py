import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sdk.sentro_command import SentroCommand

commander = SentroCommand("SentroTestClientPy")

expected_test1 = b'}\x00\x00\x00\x0b\x12SentroTestClientPy\x0cSentroDriver%Sentronic.SentroCommunication.Command3\x00\x00\x00\x11SingleMeasurement\x01\n\x00\x00\x00Correction\x01\x01\x08\x00\x00\x00channel2\x9fN\x00\x00'
expected_test2 = b'y\x00\x00\x00\x0b\x12SentroTestClientPy\x0cSentroDriver%Sentronic.SentroCommunication.Command/\x00\x00\x00\x11SingleMeasurement\x01\x06\x00\x00\x00Sample\x01\x01\x08\x00\x00\x00channel1\x9fN\x00\x00'

cmd_msg = commander.cmd_constructor("SingleMeasCorrection", "channel2")
print("test01 passed :", cmd_msg == expected_test1)
if cmd_msg != expected_test1:
    raise ValueError("test 01 failed")

cmd_msg = commander.cmd_constructor("SingleMeasSample", "channel1")
print("test02 passed :", cmd_msg == expected_test2)
if cmd_msg != expected_test2:
    raise ValueError("test 01 failed")
