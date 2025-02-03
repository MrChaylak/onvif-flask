from wsdiscovery.discovery import ThreadedWSDiscovery as WSDiscovery
from wsdiscovery import Scope
import re
from app.utils.helpers import display

def fetch_devices():
    try:
        # Initialize WS-Discovery
        wsd = WSDiscovery()
        scope1 = Scope("onvif://www.onvif.org/Profile")
        wsd.start()

        # Search for ONVIF services
        services = wsd.searchServices(scopes=[scope1])

        # Extract device IP addresses
        # # ipaddresses = []

        devices = []

        for service in services:
            xaddrs = service.getXAddrs()
            scopes = service.getScopes()
            if xaddrs:
                ipaddress = re.search(r'(\d+\.\d+\.\d+\.\d+)', xaddrs[0])
                if ipaddress:
                    ip = ipaddress.group(0)

                    # Extract ONVIF profile from scopes
                    # Extract only the profile names (Streaming, T, etc.)
                    profile_list = [
                        scope.split("/")[-1]  # Get last part of URL
                        for scope in map(str, scopes)
                        if "onvif.org/Profile/" in scope
                    ]

                    devices.append({"ip": ip, "profiles": profile_list})

                    # # ipaddresses.append(ipaddress.group(0))
            #         print("START----------")
            #     print(f"IP: {ipaddress.group(0)}")

            # # Display device scopes for debugging
            # print("Scopes:")
            # display(service.getScopes())
            # print('------------END')

        print(f'\nNumber of devices detected: {len(services)}')

        wsd.stop()
        # # return ipaddresses
        return devices

    except Exception as e:
        print(f"Error fetching devices: {e}")
        return None  # Return None to indicate failure
