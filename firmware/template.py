# Optimized WiFi Sniffer
# Created at 2019-06-11 08:50:00.610727

# The goal here is to optimize Zerynth's basic WiFi Sniffer
# () in order to capture devices connected to the AP
# while also minimizing lost packets.
#
# The algorithm is quite simple: Every X seconds (fixed by the user)
# a WiFi sniffer performs an analysis on the activity of the channels
# and stores that in the form of percentages (between 0.0 and 1.0).
# Then the main sniffer sniffs the channels whose activity percentage is
# above a certain value (also fixed by the user). The analysis function is
# called periodically thanks to a timer.

import streams                                          # For printing to serial out
import timers                                           # For timing the channel analysis
from espressif.esp32net import esp32wifi as wifi_driver # For driving the esp32 WiFi chip
import requests
from wireless import wifi
import mcu
import gc
import json
import math
import rtc
import sfw
from zdm import zdm 

sfw.watchdog(0, 120000)

number_of_channels = 13                             # Total number of channels following the IEEE 802.11 norm in Europe
channel_activity_stats = [0] * number_of_channels   # A list of channel activity
t = timers.timer()                                  # A timer to time the calls to the analysis function


SSID = ' '
PASSWORD = ' '
DEVICEID = ' '
JWT = ' '
TAG='wifiSniffer'

device=None

# Initialize serial out & WiFi chip
def init():
    gc.enable(500)
    try:
        # Initialize serial out
        streams.serial()
        # Initialize WiFi chip
        wifi_driver.auto_init()
        #Connect to ZDM
        device=zdm.Device(DEVICEID)
        device.set_password(JWT)

    except Exception as e:
        print("Initialization error:", e)
        while True:
            sleep(1000)


def init_rtc():
    while True:
        try:
            wifi.link(SSID, wifi.WIFI_WPA2, PASSWORD)

            timestamp = int(json.loads(requests.get("http://now.zerynth.com/").content)['now']['epoch'])
            rtc.set_utc(timestamp)

            wifi.unlink()
            break
        except Exception as e:
            mcu.reset()


# Scan wifi channels in order to analyze their activity over time
def scan_for_active_channels(sleep_time, iterations_per_channel):
    global channel_activity_stats

    # Initialize stat counters
    channel_activity_stats = [0] * number_of_channels
    total_packets_for_stats = 0
    done_counter = 0

    # Transform captured packets per channel percentages into scalars
    channel_activity_stats = [x * total_packets_for_stats for x in channel_activity_stats]

    print("Analyzing channel traffic... (%d)" % int(done_counter * 100), end = '\r')

    try:
        for channel in range(1, number_of_channels + 1):
            # Initialize WiFi sniffer for channel scanning
            # We're only looking for management packages
            # in this case (for example to check how many
            # devices are connected)
            # Also we're not looking to store any payloads
            # (max_payloads = 0)
            wifi_driver.start_sniffer(
                packet_types = [wifi_driver.WIFI_PKT_MGMT],
                channels = [channel],
                mgmt_subtypes = [wifi_driver.WIFI_PKT_MGMT_PROBE_REQ],
                direction = wifi_driver.WIFI_DIR_TO_NULL_FROM_NULL,
                pkt_buffer = 128,
                max_payloads = 0
            )

            for count in range(iterations_per_channel):
                # Show a progress percentage
                done_counter += (1.0 / (iterations_per_channel * number_of_channels))
                print("Analyzing channel traffic... (" + str(int(done_counter * 100) + 1) + "%)", end = '\r')
                # Sleep for a given amount of time
                sleep(sleep_time)
                # Sniff packets on channel
                pkts = wifi_driver.sniff()
                # Update stats
                channel_activity_stats[channel - 1] += (wifi_driver.get_sniffer_stats())[0]
                total_packets_for_stats += (wifi_driver.get_sniffer_stats())[0]

            # Stop the sniffer
            wifi_driver.stop_sniffer()
    except Exception as e:
        print("Error while sniffing:", e)

    # Transform captured packets per channel into percentages
    if total_packets_for_stats == 0:
        channel_activity_stats = [0] * number_of_channels
    else:
        channel_activity_stats = [1.0 * x / total_packets_for_stats for x in channel_activity_stats]

    # Print channel activity percentages
    print("\nChannel activity (normalized):", end = '')
    for channel_stat in channel_activity_stats:
        print(" %.2f " % channel_stat, end = '')
    print()


# Get packets from 'active' channels
def get_packets(sleep_time, iterations_per_channel, activity_percentage, scan_time_interval):
    print("Sniffing...")

    count = 0
    while True:
        sfw.kick()
        payloads = []

        if count % 60 == 0:
            print("Initializing RTC")
            init_rtc()
            sfw.kick()

        count = (count + 1) % 60


        # If timer has reached the interval, perform another scan
        if t.get() >= scan_time_interval:
            t.reset()
            print()
            scan_for_active_channels(1000, 2)
        # Else, get packets
        else:
            try:
                for channel in range(1, number_of_channels + 1):
                    print("Checking channel", channel)
                    if channel_activity_stats[channel - 1] >= activity_percentage:
                        print("Starting sniffer on channel", channel)
                        wifi_driver.start_sniffer(
                            packet_types=[wifi_driver.WIFI_PKT_MGMT],
                            channels = [channel],
                            mgmt_subtypes=[wifi_driver.WIFI_PKT_MGMT_PROBE_REQ],
                            direction = wifi_driver.WIFI_DIR_TO_NULL_FROM_NULL,
                            pkt_buffer=32,
                            max_payloads=0,
                            hop_time=2000)
                            
                        print("Start acquisition for", iterations_per_channel, "seconds")

                        for iteration in range(iterations_per_channel):
                            print(gc.info())
                            # Sleep for a given time
                            sleep(sleep_time)
                            # Sniff packets
                            pkts = wifi_driver.sniff()
                            now = rtc.get_utc()
                            for pkt in pkts:
                                payloads.append({
                                    'scanner_id': mac_addr,
                                    'type': pkt[0],
                                    'subtype': pkt[1],
                                    'mac1': pkt[7],
                                    'mac2': pkt[8],
                                    'mac3': pkt[9],
                                    'mac4': pkt[10],
                                    'rssi': pkt[11],
                                    'channel': pkt[12],
                                    'timestamp': now.tv_seconds + (now.tv_microseconds/1000000) #mantenere solo i secondi
                                })
                            print("Sniffed", len(pkts), "in channel", channel)

                # Stop sniffer
                print("STOP")
                wifi_driver.stop_sniffer()
                sfw.kick()
                print("STOPPED")
                sleep(500)
                print("Connecting to Wi-Fi network")
                try:
                    sfw.kick()
                    for j in range(3):
                        try:
                            wifi.link(SSID, wifi.WIFI_WPA2, PASSWORD)
                            break
                        except Exception as e:
                            print("Can't link",e)
                            sleep(100)
                    else:
                        mcu.reset()
                        sleep(100)
                    sleep(100)
                    print(gc.info())
                    print("Storing", len(payloads), "packets in database")
                    sfw.kick()
                    page = 0
                    page_size = 5
                    page_num = math.ceil(len(payloads) / page_size)
                    device.connect()
                    while page < page_num:
                        print(page + 1, "/", page_num)
                        for j in range(3):
                            try:
                                device.publish({"data":payloads[page*page_size:(page+1)*page_size]},TAG)
                                break
                            except Exception as e:
                                print("Can't post data",e)
                                sleep(100)
                        else:
                            mcu.reset()
                        page = page + 1
                        sfw.kick()
                    sleep(1000)
                    #wifi.unlink()
                except Exception as e:
                    print("Error!", e)
                    sleep(100)

            except Exception as e:
                print("Error while sniffing:", e)


# Initialize board
init()
mac_addr = ':'.join([hex(b, prefix='') for b in wifi.link_info()[4]])
print('Current MAC addr', mac_addr)
# Perform initial channel analysis (1000 ms of sleep per iterations, 2 iterations)
scan_for_active_channels(1000, 2)
# Initiate timer
t.start()
# Scan for packets (100 ms of sleep per iteration, 20 iterations,
# channels are considered active if their activity percentage is
# greater than or equal to 1%, scanning channel activity every
# 60000 ms = 60 s)
get_packets(1000, 5, 0.01, 60000)

print("Ended")
