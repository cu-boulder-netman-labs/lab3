from netmiko import ConnectHandler
from concurrent.futures import ThreadPoolExecutor

from sshInfo import load_ssh_info
from validateIP import validate_ip
from connectivity import check_reachability
from bgp import BgpManager

def check_bgp_connectivity(device):
    # Open a connection
    try:
        conn = ConnectHandler(**device)
    except Exception:
        raise Exception(f'Failed to connect to device {device}')

    hostname = conn.find_prompt()[:-1].lower()
    if hostname == 'r1':
        ping = conn.send_command('ping 20.20.20.1')
        print()
        print("Pinging from R1 to R2's loopback")
        print(ping.splitlines()[1])
        print(ping.splitlines()[-1])
        print()
    elif hostname == 'r2':
        ping = conn.send_command('ping 10.10.10.1')
        print()
        print("Pinging from R2 to R1's loopback")
        print(ping.splitlines()[1])
        print(ping.splitlines()[-1])
        print()
    else:
        raise Exception("Invalid hostname")


def config(device):
    # Check that all devices in ssh_info have a valid ip
    if not validate_ip(device['host']):
        raise Exception(f"Invalid IP {device['host']}")
    else:
        print(f"IP {device['host']} is valid")

    # Check that all devices are reachable
    connectivity = check_reachability([device['host']])
    if not connectivity[device['host']]:
        raise Exception(f"{device['host']} not reachable")
    else:
        print(f"IP {device['host']} is reachable")

    # Configure and monitor BGP
    bgp_manager = BgpManager(device)
    bgp_manager.config_bgp()
    bgp_manager.print_bgp_neighbors()
    bgp_manager.print_bgp_routes()
    bgp_manager.save_running_config()

    # Check ping connectivity between R1 and R2
    check_bgp_connectivity(device)


if __name__ == '__main__':
    ssh_info = load_ssh_info("sshInfo.json")
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(config, ssh_info))