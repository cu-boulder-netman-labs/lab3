import json
import os
import time
from netmiko import ConnectHandler, ConfigInvalidException

class BgpManager:
    def __init__(self, device):
        self.device = device

        # Open a connection
        try:
            self.conn = ConnectHandler(**device)
        except Exception:
            raise Exception(f'Failed to connect to device {device}')

        # Load config
        try:
            self.hostname = self.conn.find_prompt()[:-1].lower()
            self.bgp_conf = self.load_bgp_conf("bgp.conf")['routers'][self.hostname]
            print(self.bgp_conf)
        except KeyError:
            raise Exception(f"Could not find router in bgp.conf")

    def load_bgp_conf(self, path: str="bgp.conf.json"):
        if not os.path.exists(path):
            raise FileNotFoundError(f"BGP config file not found: {path}")
        with open(path) as f:
            return json.load(f)

    def save_running_config(self, path: str="config.txt"):
        config = self.conn.send_command("show running-config")
        path = f"{self.hostname}_config.txt"
        with open(path, 'w') as f:
            f.write(config)

        print(f"Saved running config to {path}")

    def wait_for_bgp(self, neighbor_ip, timeout=20, interval=2):
        print('Waiting for BGP to establish')
        elapsed = 0
        while elapsed < timeout:
            output = self.conn.send_command(f"show ip bgp neighbors {neighbor_ip} | i BGP state")
            state = output.split(" = ")[1].split()[0].rstrip(",")
            if state.lower() == "established":
                return True
            time.sleep(interval)
            elapsed += interval
        return False

    def print_bgp_neighbors(self):
        output = self.conn.send_command(f"show ip bgp neighbors | i BGP neighbor is")
        neighbor_ip = output.split()[3].rstrip(",")
        neighbor_as = output.split()[6].rstrip(",")

        state = self.conn.send_command(f"show ip bgp neighbors")
        state = state.split(" = ")[1].split()[0].rstrip(',')

        # Header
        print()
        print(self.conn.find_prompt()[:-1])
        print(f"{'Neighbor IP':<15} {'Remote AS':<10} {'State':<20}")
        print("-" * 45)

        # Rows
        print(f"{neighbor_ip:<15} {neighbor_as:<10} {state:<20}")
        print()

    def print_bgp_routes(self):
        routes = self.conn.send_command("sh ip route bgp | include ^B").splitlines()
        print()
        print(f"BGP routes ({self.hostname})")
        print("-" * 70)
        for route in routes:
            print(route)
        print()

    def config_bgp(self):
        # Configure bgp on router
        try:
            error_pattern = r"% Invalid|% Incomplete"
            commands = [
                f"router bgp {self.bgp_conf['local_asn']}",
                f"neighbor {self.bgp_conf['neighbor_ip']} remote-as {self.bgp_conf['neighbor_remote_as']}"
            ]

            for network in self.bgp_conf['network_list_to_advertise']:
                commands.append(f"network {network} mask 255.255.255.255")

            self.conn.send_config_set(
                commands,
                error_pattern=error_pattern
            )
        except ConfigInvalidException:
            print(f"Failed to configure bgp on router {self.hostname}")
            return False

        # Wait for BGP to establish
        if not self.wait_for_bgp(self.bgp_conf['neighbor_ip']):
            print(f"BGP was never established between {self.device['host']} and {self.bgp_conf['neighbor_ip']}")
            return False

        # Update neighbor state
        state = self.conn.send_command(f"show ip bgp neighbors {self.bgp_conf['neighbor_ip']} | i BGP state")
        self.bgp_conf['neighbor_state'] = state.split(" = ")[1].split()[0].rstrip(',')

        return True
