from flask import Flask, jsonify
from wsdiscovery.discovery import ThreadedWSDiscovery as WSDiscovery
from wsdiscovery import Scope
import re

app = Flask(__name__)


def display(any_list):
    for item in any_list:
        print(item)


def fetch_devices():
    # Initialize WS-Discovery
    wsd = WSDiscovery()

    # Define an ONVIF scope for filtering
    scope1 = Scope("onvif://www.onvif.org/Profile")
    wsd.start()

    # Search for ONVIF services with the defined scope
    services = wsd.searchServices(scopes=[scope1])

    # Extract device IP addresses
    ipaddresses = []
    for service in services:
        # Extract IP address from XAddrs
        xaddrs = service.getXAddrs()
        if xaddrs:
            ipaddress = re.search(r'(\d+\.\d+\.\d+\.\d+)', xaddrs[0])
            if ipaddress:
                ipaddresses.append(ipaddress.group(0))
                print("START----------")
                print(f"IP: {ipaddress.group(0)}")

        # Display device scopes for debugging
        print("Scopes:")
        display(service.getScopes())
        print('------------END')

    print(f'\nNumber of devices detected: {len(services)}')

    # Stop WS-Discovery
    wsd.stop()
    return ipaddresses


if __name__ == '__main__':
    app.run(debug=True)
