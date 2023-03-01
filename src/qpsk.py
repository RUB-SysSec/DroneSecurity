#!/usr/bin/env python3

import argparse
import bitarray

import numpy as np
from goldgen import gold
from droneid_packet import DroneIDPacket

# QPSK quadrant-to-symbol mapping for multiple rotations
qpsk_to_bits = [[2, 3, 1, 0],
                [0, 2, 3, 1], # +90 degree
                [1, 0, 2, 3], # +180 degree
                [3, 1, 0, 2]]  # +270 degree

# symbols within the Drone ID frame
sym = [0, 1, 2, 4, 6, 7, 8] # symbols 3, 5 intentionally left out
                            # they contain the ZC sequence and no information

# straight from 3GPP
RM_PERM_TURBO = [0, 16, 8, 24, 4, 20, 12, 28, 2, 18, 10, 26, 6, 22, 14, 30, 1, 17, 9, 25, 5, 21, 13, 29, 3, 19, 11, 27, 7, 23, 15, 31]

def rm_turbo_rx(bits_in):
    ncols = 32
    nrows = (len(bits_in) + 31) // ncols
    n_dummy = (ncols * nrows) - len(bits_in)

    bits = np.zeros((nrows, ncols), dtype=int)

    p = 0
    for col in range(ncols):
        if RM_PERM_TURBO[col] < n_dummy:
            bits[1:,RM_PERM_TURBO[col]] = bits_in[p:p + nrows - 1]
            bits[0,RM_PERM_TURBO[col]] = -1
            p += nrows - 1
        else:
            bits[:,RM_PERM_TURBO[col]] = bits_in[p:p + nrows]
            p += nrows
    assert p == len(bits_in)

    bits_out = bits.flatten()
    assert (bits_out[:n_dummy] == -1).all()
    return bits_out[n_dummy:]

# Poor man's QPSK mapping quadrants to symbols
def get_symbol_bits(symbol: np.complex, phase_correction: int=0) -> int:
    if phase_correction < 0 or phase_correction >= len(qpsk_to_bits):
        raise ValueError("Invalid phase correction")

    if symbol.real >= 0 and symbol.imag >= 0:
        return qpsk_to_bits[phase_correction][0]
    elif symbol.real >= 0 and symbol.imag < 0:
        return qpsk_to_bits[phase_correction][1]
    elif symbol.real < 0 and  symbol.imag< 0:
        return qpsk_to_bits[phase_correction][2]
    elif symbol.real < 0 and  symbol.imag> 0:
        return qpsk_to_bits[phase_correction][3]

class Decoder:
    def __init__(self, raw_data=None):
        # list of lists; 7 drone id frame symbols, and 601 qpsk symbols for each frame symbol

        self.raw_data = []
        self.sym_bits = []

        if raw_data != None:
            self.raw_data = raw_data

    def raw_data_to_symbol_bits(self, phase_correction):
        demod = []

        for frame_symbol in self.raw_data:
            frame_symbol_demod = []
            for qpsk_symbol in frame_symbol:
                frame_symbol_demod.append(get_symbol_bits(qpsk_symbol, phase_correction))
            demod.append(frame_symbol_demod)

        self.sym_bits = demod

    def read_file(self, path=None):
        raw_data = []

        for i, s in enumerate(sym):
            f = "pkt_sym_" + str(s) + ".txt"
            qbits = open(f).readlines()

            raw_data.append([])
            for qval_ in qbits:
                qval_ = qval_.split(" ")
                qval = np.complex(float(qval_[0]), float(qval_[1]))
                raw_data[i].append(qval)

        self.raw_data = raw_data

    def magic(self):
        sym_bits = self.sym_bits
        bits = np.array(sym_bits)
        bits = np.delete(bits, 300,1)

        bits = np.repeat(bits, 2, axis=1)
        bits &= np.tile([1,2], 600)
        bits = bits > 0
        bits = bits.astype(bool)

        if len(np.concatenate((bits[0:]))) > 7200:

            goldseq = gold(1600, 1200, 0x12345678)
            #print("Gold Seq len: ", len(goldseq))
            #print("Gold for Symbol: 0")
            gold_err = 0
            for i,j in enumerate(bits[0]):
                if j != goldseq[i]:
                    gold_err += 1

            if not np.all(goldseq == bits[0]):
                #print("Unable to satisfy Gold for Symbol 0")
                #print("Gold Error:", gold_err,"\n")
                pass
                #print("Gold seq does not match")
                #return False

            all_bits = np.concatenate((bits[1:]))
        else:
            # for legacy drones (missing symbol 0)
            all_bits = np.concatenate((bits[0:]))

        #print("Descramble",len(all_bits),"bits")
        # descramble
        plo = gold(1600, len(all_bits), 0x12345678) ^ all_bits

        # extract from cyclic buffer
        plo = np.concatenate((plo, plo))
        plo = plo.astype(int)
        offset = 4148

        systematic_stream = plo[offset:offset + 1412]

        # extract payload (ignore parity streams)
        p_decoded = rm_turbo_rx(systematic_stream)

        # convert into bytes
        ba = bitarray.bitarray(list(p_decoded), endian='big')
        return ba.tobytes()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--phase-shift', type=int, default=0, help="Phase Shift (0..3)")
    args = parser.parse_args()
    d = Decoder()
    d.read_file()
    for phase_corr in range(4):
        d.raw_data_to_symbol_bits(phase_corr)
        droneid_pack = d.magic()
        if droneid_pack:
            try:
                payload = DroneIDPacket(droneid_pack)
                print(payload)
                break
            except:
                continue