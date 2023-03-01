import struct
import json
import argparse
import helpers
import crcmod

DRONEID_MAX_LEN = 91

DRONEID_DRONE_TYPES = {
    "1": "Inspire 1",
    "2": "Phantom 3 Series",
    "3": "Phantom 3 Series",
    "4": "Phantom 3 Std",
    "5": "M100",
    "6": "ACEONE",
    "7": "WKM",
    "8": "NAZA",
    "9": "A2",
    "10": "A3",
    "11": "Phantom 4",
    "12": "MG1",
    "14": "M600",
    "15": "Phantom 3 4k",
    "16": "Mavic Pro",
    "17": "Inspire 2",
    "18": "Phantom 4 Pro",
    "20": "N2",
    "21": "Spark",
    "23": "M600 Pro",
    "24": "Mavic Air",
    "25": "M200",
    "26": "Phantom 4 Series",
    "27": "Phantom 4 Adv",
    "28": "M210",
    "30": "M210RTK",
    "31": "A3_AG",
    "32": "MG2",
    "34": "MG1A",
    "35": "Phantom 4 RTK",
    "36": "Phantom 4 Pro V2.0",
    "38": "MG1P",
    "40": "MG1P-RTK",
    "41": "Mavic 2",
    "44": "M200 V2 Series",
    "51": "Mavic 2 Enterprise",
    "53": "Mavic Mini",
    "58": "Mavic Air 2",
    "59": "P4M",
    "60": "M300 RTK",
    "61": "DJI FPV",
    "63": "Mini 2",
    "64": "AGRAS T10",
    "65": "AGRAS T30",
    "66": "Air 2S",
    "67": "M30",
    "68": "DJI Mavic 3",
    "69": "Mavic 2 Enterprise Advanced",
    "70": "Mini SE"
}

CRC_INIT = 0x3692
CRC_POLY = 0x11021

class DroneIDPacket:
    """Decode DUML payload to JSON."""
    droneid = {}

    def __init__(self, raw_bytes):
        self.raw_bytes = raw_bytes

        droneid_pack = struct.unpack("<BBBHH16siihhhhhhQiiiiBB20sH",raw_bytes[0:DRONEID_MAX_LEN])
        self.droneid["pkt_len"]         = droneid_pack[0]
        self.droneid["unk"]             = droneid_pack[1]
        self.droneid["version"]         = droneid_pack[2]
        self.droneid["sequence_number"] = droneid_pack[3]
        self.droneid["state_info"]      = droneid_pack[4]
        self.droneid["serial_number"]   = droneid_pack[5].decode('utf-8').rstrip('\u0000')
        self.droneid["longitude"]       = droneid_pack[6]/174533.0 # i don't know why --> found this in: White Paper: Anatomy of DJI’s Drone ID Implementation
        self.droneid["latitude"]        = droneid_pack[7]/174533.0
        self.droneid["altitude"]        = round(droneid_pack[8]/3.281,2) # ft to m
        self.droneid["height"]          = round(droneid_pack[9]/3.281,2) # ft to m
        self.droneid["v_north"]         = droneid_pack[10]
        self.droneid["v_east"]          = droneid_pack[11]
        self.droneid["v_up"]            = droneid_pack[12]
        self.droneid["d_1_angle"]       = droneid_pack[13]
        self.droneid["gps_time"]        = droneid_pack[14]
        self.droneid["app_lat"]         = droneid_pack[15]/174533.0
        self.droneid["app_lon"]         = droneid_pack[16]/174533.0
        self.droneid["longitude_home"]  = droneid_pack[17]/174533.0
        self.droneid["latitude_home"]   = droneid_pack[18]/174533.0
        self.droneid["device_type"]     = DRONEID_DRONE_TYPES.get(str(droneid_pack[19]))
        self.droneid["uuid_len"]        = droneid_pack[20]
        self.droneid["uuid"]            = droneid_pack[21].decode('utf-8').rstrip('\u0000')
        self.droneid["crc-packet"]      = "%04x" % droneid_pack[22]
        self.droneid["crc-calculated"]  = self.crc()

        state_info = droneid_pack[4]

        # self.droneid["State_Info: alt_val"] = (state_info >> 15) & 1
        # self.droneid["State_Info: gps_val"] = (state_info >> 14) & 1
        # self.droneid["State_Info: in_air"] = (state_info >> 13) & 1
        # self.droneid["State_Info: motor_on"] = (state_info >> 12) & 1
        # self.droneid["State_Info: uuid_set"] = (state_info >> 11) & 1
        # self.droneid["State_Info: home_set"] = (state_info >> 10) & 1
        # self.droneid["State_Info: private_disabled"] = (state_info >> 9) & 1
        # self.droneid["State_Info: serial_valid"] = (state_info >> 8) & 1
        # self.droneid["State_Info: unk"] = (state_info >> 7) & 1
        # self.droneid["State_Info: unk"] = (state_info >> 6) & 1
        # self.droneid["State_Info: unk"] = (state_info >> 5) & 1
        # self.droneid["State_Info: unk"] = (state_info >> 4) & 1
        # self.droneid["State_Info: unk"] = (state_info >> 3) & 1
        # self.droneid["State_Info: veloc_z_val"] = (state_info >> 2) & 1
        # self.droneid["State_Info: veloc_y_val"] = (state_info >> 1) & 1


    def get_coords(self):
        return self.droneid["latitude"], self.droneid["longitude"], self.droneid["app_lat"], self.droneid["app_lon"], self.droneid["height"]

    def crc(self) -> str:
        """Calculate CRC of the packet."""
        crc = crcmod.mkCrcFun(CRC_POLY, initCrc = CRC_INIT, rev=True)
        # CRC is appended to the packet
        crc(self.raw_bytes[:DRONEID_MAX_LEN-2])
        return "%04x" % crc(self.raw_bytes[:DRONEID_MAX_LEN-2])

    def check_crc(self) -> bool:
        """Returns True if the CRC matches, false otherwise."""
        return self.droneid["crc-packet"] == self.droneid["crc-calculated"]

    def __str__(self):
        return json.dumps(self.droneid, indent=4)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', type=str, help="Filename")
    parser.add_argument('-m', '--map', default=False, action="store_true", help="Create Map from coords")
    args = parser.parse_args()
    coords = []
    lat_list = []
    lon_list = []
    a_lat_list = []
    a_lon_list = []

    with open(args.file,"rb") as fd:
        while True:
            d = fd.read(177)
            if len(d) == 0:
                break
            print("\nReceived DroneID packet:")
            packet = DroneIDPacket(d)

            if not packet.check_crc():
                print("Invalid packet (CRC mismatch)")
            else:
                print(packet)
            lat, lon,a_lat, a_lon, height = DroneIDPacket(d).get_coords()
            if lat != 0.0 and lon != 0.0:     
                lat_list.append(lat)
                lon_list.append(lon)

                if a_lat != 0.0 and a_lon != 0.0:
                    a_lat_list.append(a_lat)
                    a_lon_list.append(a_lon)
                coords.append((lat,lon,height))
 
    if args.map:
        helpers.plot_map(lat_list,lon_list,a_lat_list, a_lon_list)

    print("\n\nFlyinfo (LAT, LON, Height):")
    for c in coords:
        print(c)

if __name__ == '__main__':
    main()

