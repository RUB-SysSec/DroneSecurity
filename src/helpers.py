import numpy as np
import scipy.signal as signal
from fractions import Fraction
import matplotlib.pyplot as plt

NCARRIERS = 601  # LTE SPEC
NCARRIERS_c2 = 73
MAXNCARRIERS = NCARRIERS
MAXNCARRIERS_c2 = NCARRIERS_c2
NFFT = 1024  # LTE SPEC

# CP Len LTE SPEC: Short, first OFDM Sym: 80 Samples * 1, remaining 6 * 72 Samples
CP_LENGTHS = [
    72 + 8,  # 0
    72,  # 1
    72,  # 2
    72,  # 3
    72,  # 4
    72,  # 5
    72,  # 6
    72,  # 7
    72 + 8,  # 8
]

CP_LENGTHS_legacy = [
    72 + 8,  # 0
    72,  # 1
    72,  # 2
    72,  # 3
    72,  # 4
    72,  # 5
    72,  # 6
    72 + 8,  # 7
]

CP_LENGTHS_C2 = [
    72 + 8,  # 0
    72,  # 1
    72,  # 2
    72,  # 3
    72,  # 4
    72,  # 5
    72 + 8,  # 6
]

# ZC sequence in these symbols
ZC_SYMBOL_IDX = [3, 5]
ZC_SYMBOL_IDX_legacy = [2, 4]
ZC_SYMBOL_IDX_c2 = [0, 6]

def corr(x, y=None):
    if y is None:
        y = x
    result = np.correlate(x, y, mode='full')
    return result[result.size//2:]

def fshift(y, offset, Fs):
    print(f"{len(y)}, offset={offset}, Fs={Fs}")
    x = np.linspace(0.0, len(y)/Fs, len(y))
    return y * np.exp(x * 2j * np.pi * offset)

def fshift_rad(y, offset, Fs):
    x = np.linspace(0.0, len(y)/Fs, len(y))
    return y * np.exp(x * 1j * np.pi * offset)

def with_sample_offset(data, offset):
        return np.interp(np.arange(offset, offset+len(data), 1), np.arange(0, len(data)), data)

def resample(pkt_fullrate, Fs: float, Fsnew: float ):
    # decimate / resample
    #fr = Fraction(int(Fsnew), int(Fs)).limit_denominator(1000)
    #return signal.resample_poly(pkt_fullrate, fr.numerator, fr.denominator)
    #return signal.resample(pkt_fullrate, int(len(pkt_fullrate)/Fs*Fsnew))

    return np.interp(np.arange(0, len(pkt_fullrate), Fs/Fsnew),
            np.arange(0, len(pkt_fullrate)), pkt_fullrate)

def consecutive(data, stepsize=1):
    return np.split(data, np.where(np.diff(data) != stepsize)[0]+1)

def tfft(sy):
    fft = np.fft.fft(sy, n=NFFT)
    half_carriers = NCARRIERS//2
    new_fft = np.concatenate((fft[-half_carriers:], fft[:half_carriers+1]))
    return new_fft

def itfft(c):
    half_carriers = NCARRIERS//2
    c_full = np.zeros((NFFT), dtype=np.complex64)
    c_full[-half_carriers:] = c[:half_carriers]
    c_full[:half_carriers+1] = c[half_carriers:]

    return np.fft.ifft(c_full)

def estimate_offset(y, Fs, debug=False, packet_type="droneid"):
    nfft_welch = 2048

    if len(y) < nfft_welch:
        return None, False

    # calculate power density
    f, Pxx_den = signal.welch(
        y, Fs, nfft=nfft_welch, return_onesided=False)

    Pxx_den = np.fft.fftshift(Pxx_den)
    f = np.fft.fftshift(f)

    if debug:
        # plot power density over frequency
        plt.semilogy(f, Pxx_den)
        plt.xlabel('frequency [Hz]')
        plt.ylabel('PSD [V**2/Hz]')
        plt.plot(f, [Pxx_den.mean(), ]*len(f))
        plt.show()
        #plt.plot(Pxx_den > Pxx_den.mean())

    # add a fake DC carrier
    Pxx_den[nfft_welch//2-10:nfft_welch//2+10] = 1.1*Pxx_den.mean()

    # resulting data is FFT bins with power density higher than avg
    candidate_bands = consecutive(np.where(Pxx_den > Pxx_den.mean())[0])

    band_found = False
    offset = 0.0

    for band in candidate_bands:
        start = band[0]-nfft_welch/2
        end = band[-1]-nfft_welch/2

        bw = (end - start) * (Fs/nfft_welch)

        fend = start * Fs/nfft_welch
        fstart = end * Fs/nfft_welch

        if debug:
            print("candidate band fstart: %3.2f, fend: %3.2f, bw: %3.2f MHz" % (fstart, fend, bw/1e6))
        print("candidate band fstart: %3.2f, fend: %3.2f, bw: %3.2f MHz" % (fstart, fend, bw/1e6))

        # droneid / beacons | c2 | video feed
        if packet_type == "droneid" and (bw > 8e6 and bw < 11e6):
            offset = fstart - 0.5*bw
            band_found = True
            break
        elif packet_type == "c2" and (bw > 1.2e6 and bw < 1.95e6):
            offset = fstart - 0.5*bw
            band_found = True
            break
        elif packet_type == "video" and (bw > 18e6 and bw < 22e6):  # drone ID is 9 MHz wide so 8 MHz should work :)
            # TODO this stops working if there are more than one simultaneous drone ID broadcasts
            # (offset frequencies, not absolute)
            offset = fstart - 0.5*bw
            band_found = True
            break

    if debug:
        print("Offset found: %.2fkHz" % (offset/1000))
    return offset, band_found
