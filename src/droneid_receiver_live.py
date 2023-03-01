#!/usr/bin/python3

import queue
import uhd
import numpy as np
import signal
import SpectrumCapture as SC
from Packet import Packet
from qpsk import Decoder
from droneid_packet import DroneIDPacket
from datetime import datetime
import argparse
import matplotlib.pyplot as plt
import threading
import multiprocessing as mp
import time
import sys

import warnings

warnings.filterwarnings("ignore")
queue = mp.Queue()
exit_event = threading.Event()
RECV_BUFFER_LEN=1000
streamer = None
usrp = None
db_filename = None
sample_rate = None
args = None
coords = []
lat_list = []
lon_list = []
raw_droneid_bits = []
fixed_runs = 0
c_freq = 0
num_decoded = 0
interesting_freq = 0
crc_err = 0
correct_pkt = 0
total_num_pkt = 0
recv_thread = None
worker = None 

def signal_handler(sig, frame):
    global exit_event
    exit_event.set()

def clean_up():
    global exit_event, recv_thread, workers
    # Stop Stream
    print("\n\n######### Stopping Threads, please wait #########\n\n")
    while recv_thread.is_alive():
        recv_thread.join(timeout=10)

    print("Receiver stopped")
    
    for worker in workers:
        print("Send stop message to thread:",worker.name)
        queue.put((None, None))

def decoded_to_file(raw_bits):
    if len(raw_bits) > 0:     
        with open(db_filename,"ab") as fd:
            fd.write(raw_bits)

def set_sdr(usrp, sample_rate=50e6, duration_s=1.3, gain=None):
    ###### dev config (UHD b200) #####
    # RX2 port for 2.4 GHz antenna
    usrp.set_rx_antenna("RX2",0)
    if gain:
        usrp.set_rx_gain(gain, 0)
    else:
        usrp.set_rx_agc(True, 0)

    num_samps = duration_s*sample_rate

    usrp.set_rx_rate(sample_rate, 0)
    dev_samp_rate = usrp.get_rx_rate()

    # Set up the stream and receive buffer
    st_args = uhd.usrp.StreamArgs("fc32","sc16")
    st_args.channels = [0]
    _metadata = uhd.types.RXMetadata()
    _streamer = usrp.get_rx_stream(st_args)
    _recv_buffer = np.zeros((1, RECV_BUFFER_LEN), dtype=np.complex64)

    return num_samps, _metadata, _streamer, _recv_buffer

def run_demod(samples,Fs, debug=False, legacy = False):
    global correct_pkt, crc_err, total_num_pkt
    chunk_samples = int(500e-3 * Fs) # in seconds
    found = False

    #for packet in packets:
    chunks = len(samples) // chunk_samples

    for i in range(chunks):
        capture = SC.SpectrumCapture(raw_data = samples[i*chunk_samples:(i+1)*chunk_samples],Fs=Fs,debug=debug, p_type = args.packettype, legacy=legacy)
        if debug:
            print("Found %i Drone-ID RF frames in spectrum capture." % len(capture.packets))
        
        total_num_pkt += len(capture.packets)
        for packet_num, _ in enumerate(capture.packets):

            with open("ext_drone_id_" + str(sample_rate),"ab") as f:
                f.write(_)
            # get a Drone ID frame, resampled and with coarse center frequency correction.
            packet_data = capture.get_packet_samples(pktnum=packet_num,debug=debug)

            try:
                packet = Packet(packet_data, debug=debug, legacy=legacy)
            except:
                if debug:
                    print("Could not decode packet.")
                continue
            # perform RF corrections, OFDM and stuff
            symbols = packet.get_symbol_data(skip_zc=True)
            decoder = Decoder(symbols)

            # brute force QPSK alignment
            for phase_corr in range(4):
                decoder.raw_data_to_symbol_bits(phase_corr)
                droneid_duml = decoder.magic()
                if not droneid_duml:
                    # decoding failed
                    continue
                # save bits to file
                decoded_to_file(droneid_duml)

                try:
                    payload = DroneIDPacket(droneid_duml)
                except:
                    print("error decoding packet")
                    continue
                print(payload)
                found = True

                if not payload.check_crc():
                    # CRC check failed
                    crc_err += 1
                    continue
                correct_pkt +=1
                break 

    return found

def receive_samples(num_samps, metadata, streamer, recv_buffer):
    # Receive Samples
    samples = np.zeros(int(num_samps), dtype=np.complex64)

    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
    stream_cmd.num_samps = int(num_samps)
    stream_cmd.stream_now = True
    streamer.issue_stream_cmd(stream_cmd)

    for i in range(int(num_samps//RECV_BUFFER_LEN)):
        streamer.recv(recv_buffer, metadata,timeout=1.4)
       
        if "ERROR_CODE_TIMEOUT" in str(metadata.strerror()):
            return None
            

        samples[i*RECV_BUFFER_LEN:(i+1)*RECV_BUFFER_LEN] = recv_buffer[0]
    return samples

def receive_thread(usrp, sample_rate, duration, gain, queue):
    global interesting_freq
    frequencies = [2414.5, 2429.502441, 2434.5, 2444.5, 2459.5, 2474.5, 5721.5, 5731.5, 5741.5, 5756.5, 5761.5, 5771.5, 5786.5, 5801.5, 5816.5, 5831.5]
    num_samps, metadata, streamer, recv_buffer = set_sdr(usrp, sample_rate, duration, gain)

    while True:
        samples = []
        for c_freq in frequencies:
            c_freq = c_freq * 1e6

            if interesting_freq == 0:
                cnt_freq = c_freq
                interesting_freq = 0
                r = usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(cnt_freq), 0)
            else:
                r = usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(interesting_freq), 0)
                cnt_freq = interesting_freq

            if not r:
                print("Unable to set center freq")
            else:
                print("Center Freq: ",cnt_freq,"@",sample_rate/1e6)


            samples = receive_samples(num_samps, metadata, streamer, recv_buffer)
            if samples is None:
                continue
            else:
                samples = samples#.view(np.complex64)
            queue.put((samples.copy(),c_freq))
            if exit_event.is_set():
                break
        if exit_event.is_set():
            print("Receiver Thread: Stopped")
            break


def process_samples(sample_rate, queue):
    #global droneid_found, new_cnt_freq, fixed_runs
    global interesting_freq
    droneid_found = False
    fixed_runs = 0

    while True:
        samples, cnt_freq = queue.get()

        if samples is None and cnt_freq is None:
            break

        with open("receive_test.raw", 'ab') as f:
           f.write(samples)

        if run_demod(samples,sample_rate,debug=args.debug, legacy = args.legacy):
            interesting_freq = cnt_freq
            print("Locking Frequency to", cnt_freq)
            fixed_runs = 0
        else:
            fixed_runs += 1

        if fixed_runs > 10:
            interesting_freq = 0
            fixed_runs = 0
        
        if exit_event.is_set():
            print("Process Thread: Stopped")
            break


####################################


def main():
    global db_filename, usrp, recv_thread, args, workers
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--gain', default="0", type=int, help="Gain 0 == AGC")
    parser.add_argument('-s', '--sample_rate', default="50e6", type=float, help="Sample Rate")
    parser.add_argument('-w', '--workers', default="2", type=int, help="number of worker threads for processing")
    parser.add_argument('-l', '--legacy', default=False, action="store_true", help="Support of legacy drones (Mavic Pro, Mavic 2)")
    parser.add_argument('-d', '--debug', default=False, action="store_true", help="Enable debug output")
    parser.add_argument('-t', '--duration', default=1.3, type=float, help="Time of receiving samples per band")
    parser.add_argument('-p', '--packettype', default="droneid", type=str, help="Packet type: droneid, c2, beacon, video")

    args = parser.parse_args()


    signal.signal(signal.SIGINT, signal_handler)
    usrp = uhd.usrp.MultiUSRP("type=b200, recv_frame_size=8200,num_recv_frames=512")

    if args.gain > 0:
        gain = args.gain
    else:
        # AGC
        gain = False

    duration = args.duration
    sample_rate = args.sample_rate
    channels = [0]


    dt = datetime.now()
    db_filename = "decoded_bits_" + str(dt.day) + str(dt.month) + "_" + str(dt.hour) + str(dt.minute) + ".bin"


    # Start Stream
    print("Start receiving...")

    recv_thread = threading.Thread(target=receive_thread, args=(usrp, sample_rate, duration, gain, queue))
    recv_thread.start()

    num_workers = args.workers
    workers = []
    for i in range(num_workers):
        proc_thread = mp.Process(target=process_samples, args=(sample_rate, queue))
        proc_thread.start()
        workers.append(proc_thread)

    while True:

        if exit_event.is_set():
            clean_up()
            exit_event.clear()

        workers_alive = 0
        for worker in workers:
            if worker.is_alive():
                workers_alive += 1

        if workers_alive == 0:
            print("No more workers alive!\nExiting...")
            break

    print("\n\nSuccessfully decoded %i / %i packets" % (total_num_pkt, correct_pkt))
    print(crc_err,"Packets with CRC error")


if __name__ == "__main__":
    main()