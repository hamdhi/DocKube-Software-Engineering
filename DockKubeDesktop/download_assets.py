import os
import urllib.request
from pathlib import Path

# Ensure assets directory exists
assets_dir = Path('assets')
assets_dir.mkdir(exist_ok=True)

pairs = [
    ('k8s_network.png', 'https://raw.githubusercontent.com/kubernetes/website/main/content/en/images/docs/concepts/cluster/networking.png'),
    ('dns_flow.png', 'https://www.cloudflare.com/img/learning/dns/dns-overview/dns-overview-diagram.svg'),
    ('cidr_chart.png', 'https://www.ipcalc.net/images/cidr-table.png'),
    ('osi_layers.png', 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/OSI_Model.png/800px-OSI_Model.png'),
    ('subnet_example.png', 'https://i.stack.imgur.com/5xqZb.png'),
    ('firewall_stateful.png', 'https://www.cisco.com/c/en/us/td/docs/security/firepower/630/firepower-system-management/configuration/guide/fpm-630-sys-mgmt-config/figures/fpm_stateful_firewall.png'),
    ('ssh_handshake.png', 'https://i.stack.imgur.com/l3P2N.png'),
    ('tls_handshake.png', 'https://tls13.ulfheim.net/tls13_handshake.png'),
    ('router_vs_switch.png', 'https://www.networkworld.com/wp-content/uploads/2020/05/router-switch-800x450.png'),
    ('vm_vs_container.png', 'https://i.stack.imgur.com/aB9Xy.png'),
]

for filename, url in pairs:
    out_path = assets_dir / filename
    try:
        urllib.request.urlretrieve(url, out_path)
        print(f'Downloaded {filename}')
    except Exception as e:
        print(f'Failed {filename}: {e}')
