import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button

import numpy as np
import scipy.signal as signal
from zcsequence import zcsequence_t, zcsequence_f

from helpers import CP_LENGTHS, NCARRIERS, ZC_SYMBOL_IDX

def interactive(packet):
    fig, ax = plt.subplots(3, 3)
    symbol_data_export = []

    linrot  = Slider(plt.axes([0.25, .1, 0.50, 0.02]),  'linear rotation', - .03, .03, valinit=0)
    off     = Slider(plt.axes([0.25, .08, 0.50, 0.02]), 'sampling offset', -100, 100, valinit=0)
    tune    = Slider(plt.axes([0.25, .06, 0.50, 0.02]), 'tune frequency', -30000, 30000, valinit=0)
    sr      = Slider(plt.axes([0.25, .04, 0.50, 0.02]), 'sr', -.001, .001, valinit=0)
    #seqcor  = Slider(plt.axes([0.25, .02, 0.30, 0.02]), 'zc_cyc', 0, 601, valinit=zc_cyc)
    write   = Button(plt.axes([0.60, .02, 0.20, 0.02]), 'write')

    def save(_):
        print("saving data...")
        for i, symbol in enumerate(symbol_data_export):
            if symbol is None:
                continue
            with open("pkt_sym_%d.txt" % (i), "w") as fo:
                for val in symbol:
                    fo.write("%f %f\n" % (np.real(val), np.imag(val)))

    def update(_):

        symbol_data_export.clear()

        for axis in ax:
            for plot in axis:
                plot.clear()

        # iterate over all symbol indices
        for s, _ in enumerate(CP_LENGTHS):
            a = ax[s//3][s % 3] # current axis

            # current symbol data
            #data = packet.update_params(s, linrot.val, off.val, tune.val, sr.val)
            data = packet.get_symbol_data(linear_rotation=linrot.val, _sampling_offset=off.val, tune=tune.val)[s]

            data_fft = [np.real(data), np.imag(data)]

            if s in ZC_SYMBOL_IDX:
                # Plotting for ZC Sequences
                # 600 is wrong, this should variable
                seq = zcsequence_t(600, NCARRIERS)
                # poor man's channel estimation
                est = seq / data
                est[NCARRIERS//2] = (est[NCARRIERS//2-1] +
                                        est[NCARRIERS//2+1]) * .5  # fake
                #magest = np.abs(est)
                a.plot(np.angle(est))
                symbol_data_export.append(None)
            else:
                markers = ['+', 'x', 'o', '.', '*', 'v']
                for i in range(NCARRIERS//100):
                    a.scatter(data_fft[0][i*100:100*(i+1)], data_fft[1]
                                [i*100:100*(i+1)], marker=markers[i])
                symbol_data_export.append(data)
        fig.canvas.draw_idle()

    write.on_clicked(save)
    linrot.on_changed(update)
    off.on_changed(update)
    tune.on_changed(update)
    sr.on_changed(update)
    #seqcor.on_changed(update)
    update(0)

    plt.show()
