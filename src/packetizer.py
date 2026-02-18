#!/usr/bin/env python3

import argparse
import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt
from helpers import estimate_offset

def find_packet_candidate_time(raw_data, Fs, debug=False, packet_type = "droneid", legacy = False):
    """Find packets with the right length by looking at signal power.
    
    Optimized version with early exit and faster STFT parameters.
    """
    if packet_type == "droneid": 
        if legacy:
            min_packet_len_t = 565e-6
            max_packet_len_t = 600e-6
        else:
            min_packet_len_t = 630e-6
            max_packet_len_t = 665e-6
    elif packet_type == "c2":
        min_packet_len_t = 500e-6
        max_packet_len_t = 520e-6
    elif packet_type == "beacon":
        min_packet_len_t = 490e-6
        max_packet_len_t = 540e-6
    elif packet_type == "pairing":
        min_packet_len_t = 490e-6
        max_packet_len_t = 540e-6
    elif packet_type == "video":
        min_packet_len_t = 630e-6
        max_packet_len_t = 665e-6

    if debug:
        print("Packet Type:",packet_type)

    start_offset = 3*15e-6
    end_offset = 3*15e-6

    # Optimized STFT: smaller nfft for faster computation
    # 64 is enough for timing detection, don't need high frequency resolution
    f, t, Zxx = signal.stft(raw_data, Fs, nfft=64, nperseg=64, noverlap=0)
    
    # Fast power calculation using max across frequency bins
    res_abs = np.max(np.abs(Zxx), axis=0)
    noise_floor = np.mean(res_abs)  # Faster than np.mean(np.abs(Zxx))

    # Get things above the noise floor
    above_level = res_abs > 1.15*noise_floor

    # Search for chunks above noise floor that fit the packet length
    signal_length_min_samples = int(min_packet_len_t/(t[1]-t[0]))
    signal_length_max_samples = int(max_packet_len_t/(t[1]-t[0]))
    
    # Optimized peak finding with reasonable wlen
    wlen = min(100*signal_length_max_samples, len(above_level))
    peaks, properties = signal.find_peaks(
        above_level, 
        width=[signal_length_min_samples, signal_length_max_samples],
        wlen=wlen
    )
        
    packets = []
    center_freq_offset = 0

    for i, _ in enumerate(peaks):
        start = properties["left_bases"][i] * (t[1]-t[0])
        end = properties["right_bases"][i] * (t[1]-t[0])
        length = properties["widths"][i] * (t[1]-t[0])

        packet_data = raw_data[int((start-start_offset)*Fs):int((end+end_offset)*Fs)]

        # Estimate center frequency offset
        center_freq_offset, found = estimate_offset(packet_data, Fs, skip_bw_check=legacy)

        if not found:
            if legacy:
                # For legacy drones, try with zero offset if bandwidth detection fails
                if debug:
                    print("Packet #%i, start %f, end %f, length %f, cfo detection failed - trying with offset=0 (legacy bypass)" % (i, start, end, length))
                center_freq_offset = 0.0
            else:
                if debug:
                    print("Packet #%i, start %f, end %f, length %f, cfo MISMATCH" % (i, start, end, length))
                continue

        if debug:
            print(center_freq_offset)
            print("Packet #%i, start %f, end %f, length %f, cfo %f" % (i, start, end, length, center_freq_offset))
        
        packets.append(packet_data)
        
        # Early exit optimization: if we found packets, don't need to search entire capture
        # This significantly speeds up processing when signals are present
        if len(packets) >= 3:  # Stop after finding 3 packets
            break

    return packets, center_freq_offset

def main(args):
    data = np.fromfile(args.input_file, dtype="<f").astype(np.float32).view(np.complex64)
    find_packet_candidate_time(data, args.sample_rate, args.debug)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file', help="Binary Sample Input")
    parser.add_argument('-s', '--sample-rate', default="50e6", type=float, help="Sample Rate")
    parser.add_argument('-d', '--debug', default=False, action="store_true", help="Enable debug output")
    args = parser.parse_args()

    main(args)