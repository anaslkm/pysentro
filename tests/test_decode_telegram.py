import os
import sys
from pprint import pprint
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sdk.sentro_telegram import Telegram, TelegramData

test_path = Path(os.path.dirname(__file__))

list_meas = [f for f in os.listdir() if f.endswith(".txt")]

for meas in list_meas:
    with open(meas, "rb") as f:
        telegram = f.read()

    tg = Telegram(telegram)

    pprint(tg)

    f, ax = plt.subplots(figsize=(16, 6))
    colors = ['b', 'r', 'm']
    for i, s in enumerate(tg.data.spectra_data):
        if i == 0:
            ax.plot(np.array(s[0], dtype=int), np.array(s[1], dtype=float), c=colors[i])
        else:
            axb = ax.twinx()
            axb.plot(np.array(s[0], dtype=int), np.array(s[1], dtype=float), c=colors[i])
    plt.show()