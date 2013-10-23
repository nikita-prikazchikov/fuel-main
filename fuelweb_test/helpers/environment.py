#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import os
import time
import logging
from ipaddr import IPNetwork

from devops.helpers.helpers import _get_file_size
from devops.manager import Manager
from devops.helpers.helpers import wait

from fuelweb_test.node_roles import Nodes
from fuelweb_test.settings import EMPTY_SNAPSHOT, ISO_PATH, USE_ALL_DISKS
from fuelweb_test.settings import INTERFACE_ORDER, POOLS, FORWARDING, DHCP


logger = logging.getLogger('integration')


class EnvironmentModel(object):
    hostname = 'nailgun'
    domain = 'test.domain.local'
    installation_timeout = 1800
    deployment_timeout = 1800
    puppet_timeout = 1000

    def __init__(self):
        self.manager = Manager()
        self._environment = None
        self.saved_environment_states = {}

    def remote(self):
        """
        :rtype : SSHClient
        """
        return self.nodes().admin.remote(
            'internal',
            login='root',
            password='r00tme')

    def get_admin_node_ip(self):
        return str(
            self.nodes().admin.get_ip_address_by_network_name('internal'))

    def _get_or_create(self):
        try:
            return self.manager.environment_get(self.env_name())
        except:
            self._environment = self.describe_environment()
            self._environment.define()
            return self._environment

    def get_state(self, name):
        if self.environment().has_snapshot(name):
            self.environment().revert(name)
            return True
        return False

    def get_active_state(self, name):
        if self.environment().has_snapshot(name):
            self.environment().revert(name)
            self.environment().resume()
            return True
        return False

    def make_snapshot(self, snapshot_name):
        self.environment().suspend(verbose=False)
        self.environment().snapshot(snapshot_name)

    def environment(self):
        """
        :rtype : devops.models.Environment
        """
        self._environment = self._environment or self._get_or_create()
        return self._environment

    def nodes(self):
        return Nodes(self.environment(), self.node_roles())

    # noinspection PyShadowingBuiltins
    def add_empty_volume(self, node, name, capacity=20 * 1024 * 1024 * 1024,
                         device='disk', bus='virtio', format='qcow2'):
        self.manager.node_attach_volume(
            node=node,
            volume=self.manager.volume_create(
                name=name, capacity=capacity,
                environment=self.environment(),
                format=format),
            device=device, bus=bus)

    def add_node(self, memory, name, boot=None):
        return self.manager.node_create(
            name=name,
            memory=memory,
            environment=self.environment(),
            boot=boot)

    def create_interfaces(self, networks, node):
        for network in networks:
            if network.name == 'internal':
                self.manager.interface_create(network, node=node)
                self.manager.interface_create(network, node=node)
            self.manager.interface_create(network, node=node)

    def describe_admin_node(self, name, networks, memory=1024):
        node = self.add_node(memory=memory, name=name, boot=['hd', 'cdrom'])
        self.create_interfaces(networks, node)
        self.add_empty_volume(node, name + '-system')
        self.add_empty_volume(
            node, name + '-iso', capacity=_get_file_size(ISO_PATH),
            format='raw', device='cdrom', bus='ide')
        return node

    def describe_empty_node(self, name, networks, memory=1024):
        node = self.add_node(memory, name)
        self.create_interfaces(networks, node)
        self.add_empty_volume(node, name + '-system')

        if USE_ALL_DISKS:
            self.add_empty_volume(node, name + '-cinder')
            self.add_empty_volume(node, name + '-swift')

        return node

    def get_empty_environment(self):
        if not(self.get_state(EMPTY_SNAPSHOT)):
            self.setup_environment()
            self.environment().snapshot(EMPTY_SNAPSHOT)

    def generate_state_hash(self, settings):
        return hashlib.md5(str(settings)).hexdigest()

    def revert_to_state(self, settings={}):
        state_hash = self.generate_state_hash(settings)

        if state_hash in self.saved_environment_states:
            # revert to matching state
            state = self.saved_environment_states[state_hash]
            if not(self.get_state(state['snapshot_name'])):
                return False
            self.environment().resume()
            return True

        return False

    def snapshot_state(self, name, settings={}):
        state_hash = self.generate_state_hash(settings)

        snapshot_name = '{0}_{1}'.format(
            name.replace(' ', '_')[:17], state_hash)

        self.environment().suspend(verbose=False)
        self.environment().snapshot(
            name=snapshot_name,
            description=name,
            force=True,
        )
        self.environment().resume(verbose=False)
        self.saved_environment_states[state_hash] = {
            'snapshot_name': snapshot_name,
            'cluster_name': name,
            'settings': settings
        }

    def internal_virtual_ip(self):
        return str(IPNetwork(
            self.environment().network_by_name('internal').ip_network)[-2])

    def public_router(self):
        return str(
            IPNetwork(
                self.environment().network_by_name('public').ip_network)[1])

    def internal_router(self):
        return self._router('internal')

    def nat_router(self):
        return self._router('nat')

    def _router(self, router_name):
        return str(
            IPNetwork(
                self.environment().network_by_name(router_name).ip_network)[1])

    def get_host_node_ip(self):
        return self.internal_router()

    def internal_network(self):
        return str(
            IPNetwork(
                self.environment().network_by_name('internal').ip_network))

    def internal_net_mask(self):
        return str(IPNetwork(
            self.environment().network_by_name('internal').ip_network).netmask)

    def public_net_mask(self):
        return str(IPNetwork(
            self.environment().network_by_name('public').ip_network).netmask)

    def public_network(self):
        return str(
            IPNetwork(self.environment().network_by_name('public').ip_network))

    @property
    def node_roles(self):
        return NodeRoles(
            admin_names=['admin'],
            other_names=['slave-%02d' % x for x in range(1, 10)]
        )

    @property
    def env_name(self):
        return os.environ.get('ENV_NAME', 'fuelweb')

    def describe_environment(self):
        """
        :rtype : Environment
        """
        environment = self.manager.environment_create(self.env_name())
        networks = []
        for name in INTERFACE_ORDER:
            ip_networks = [IPNetwork(x) for x in POOLS.get(name)[0].split(',')]
            new_prefix = int(POOLS.get(name)[1])
            pool = self.manager.create_network_pool(
                networks=ip_networks, prefix=int(new_prefix))
            networks.append(self.manager.network_create(
                name=name, environment=environment, pool=pool,
                forward=FORWARDING.get(name), has_dhcp_server=DHCP.get(name)))

        for name in self.node_roles().admin_names:
            self.describe_admin_node(name, networks)
        for name in self.node_roles().other_names:
            self.describe_empty_node(name, networks, memory=1024)
        return environment

    def wait_bootstrap(self):
        logging.info("Waiting while bootstrapping is in progress")
        log_path = "/var/log/puppet/bootstrap_admin_node.log"
        wait(
            lambda: not
            self.nodes().admin.remote('internal', 'root', 'r00tme').execute(
                "grep 'Finished catalog run' '%s'" % log_path
            )['exit_code'],
            timeout=self.puppet_timeout
        )

    def get_keys(self, node):
        params = {
            'ip': node.get_ip_address_by_network_name('internal'),
            'mask': self.internal_net_mask(),
            'gw': self.nat_router(),
            'hostname': '.'.join((self.hostname, self.domain))
        }
        keys = (
            "<Esc><Enter>\n"
            "<Wait>\n"
            "vmlinuz initrd=initrd.img ks=cdrom:/ks.cfg\n"
            " ip=%(ip)s\n"
            " netmask=%(mask)s\n"
            " gw=%(gw)s\n"
            " dns1=%(gw)s\n"
            " hostname=%(hostname)s\n"
            " <Enter>\n"
        ) % params
        return keys

    def enable_nat_for_admin_node(self):
        remote = self.nodes().admin.remote('internal', 'root', 'r00tme')

        nat_interface_id = 5
        file_name = \
            '/etc/sysconfig/network-scripts/ifcfg-eth%s' % nat_interface_id
        hwaddr = \
            ''.join(remote.execute('grep HWADDR %s' % file_name)['stdout'])
        uuid = ''.join(remote.execute('grep UUID %s' % file_name)['stdout'])
        nameserver = os.popen(
            "grep '^nameserver' /etc/resolv.conf | "
            "grep -v 'nameserver\s\s*127.' | head -3").read()

        remote.execute('echo -e "%s'
                       '%s'
                       'DEVICE=eth%s\\n'
                       'TYPE=Ethernet\\n'
                       'ONBOOT=yes\\n'
                       'NM_CONTROLLED=no\\n'
                       'BOOTPROTO=dhcp\\n'
                       'PEERDNS=no" > %s'
                       % (hwaddr, uuid, nat_interface_id, file_name))
        remote.execute(
            'sed "s/GATEWAY=.*/GATEWAY="%s"/g" -i /etc/sysconfig/network'
            % self.nat_router())
        remote.execute('echo -e "%s" > /etc/dnsmasq.upstream' % nameserver)
        remote.execute('service network restart >/dev/null 2>&1')
        remote.execute('service dnsmasq restart >/dev/null 2>&1')

    def setup_environment(self):
        # start admin node
        admin = self.nodes().admin
        admin.disk_devices.get(device='cdrom').volume.upload(ISO_PATH)
        self.environment().start(self.nodes().admins)
        # update network parameters at boot screen
        time.sleep(30)
        admin.send_keys(self.get_keys(admin))
        # wait while installation complete
        admin.await('internal', timeout=10 * 60)
        self.wait_bootstrap()
        time.sleep(10)
        self.enable_nat_for_admin_node()


class NodeRoles(object):
    def __init__(self,
                 admin_names=None,
                 other_names=None):
        self.admin_names = admin_names or []
        self.other_names = other_names or []


class Nodes(object):
    def __init__(self, environment, node_roles):
        self.admins = []
        self.others = []
        for node_name in node_roles.admin_names:
            self.admins.append(environment.node_by_name(node_name))
        for node_name in node_roles.other_names:
            self.others.append(environment.node_by_name(node_name))
        self.slaves = self.others
        self.all = self.slaves + self.admins
        self.admin = self.admins[0]

    def __iter__(self):
        return self.all.__iter__()