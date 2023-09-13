import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as mtick
import os
def silentremove(filename):
    try:
        os.remove(filename)
    except OSError:
        pass
silentremove('static/uploads/1654843545/1/rank0_Cmajor.mid')

