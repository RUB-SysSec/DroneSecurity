#!/usr/bin/env python3

import numpy as np
from helpers import NCARRIERS, tfft

def zcsequence_t(u: int, seq_length: int, q: int=0) -> np.array:
    """
    Generate a Zadoff-Chu (ZC) sequence.
    Parameters
    ----------
    u : int
        Root index of the the ZC sequence: u>0.
    seq_length : int
        Length of the sequence to be generated. Usually a prime number:
        u<seq_length, greatest-common-denominator(u,seq_length)=1.
    q : int
        Cyclic shift of the sequence (default 0).
    Returns
    -------
    zcseq : 1D ndarray of complex floats
        ZC sequence generated.
    """

    zcseq = np.exp(-1j * np.pi * u * np.arange(seq_length) * (np.arange(seq_length)+1) / seq_length)

    return zcseq

# for compatibility
def zcsequence(u: int, seq_length: int, q: int=0) -> np.array:
    return zcsequence_t(u, seq_length, q)

def zcsequence_f(root: int, seq_length:int):
    zcseq_t = zcsequence_t(root, seq_length)
    zcseq_f = tfft(zcseq_t)
    zcseq_f[NCARRIERS//2] = 0
    return zcseq_f