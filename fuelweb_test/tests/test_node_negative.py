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


import logging
import unittest
from nose.plugins.attrib import attr
from nose.plugins.skip import SkipTest
from fuelweb_test.helpers import Ebtables
from fuelweb_test.models.fuel_web_client import Environment_Model
from fuelweb_test.helpers.decorators import debug, fetch_logs

logging.basicConfig(
    format=':%(lineno)d: %(asctime)s %(message)s',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)
logwrap = debug(logger)


class TestNodeNegative(Environment_Model):

    @logwrap
    @fetch_logs
    @attr(releases=['centos', 'redhat', "ubuntu"], test_thread='thread_1')
    def test_untagged_networks_negative(self):
        raise SkipTest()
        cluster_name = 'simple_untagged'

        vlan_turn_off = {'vlan_start': None}
        nodes = {
            'slave-01': ['controller'],
            'slave-02': ['compute']
        }
        interfaces = {
            'eth0': ["fixed"],
            'eth1': ["public", "floating"],
            'eth2': ["management", "storage"],
            'eth3': []
        }

        self.prepare_environment()

        # create a new empty cluster and add nodes to it:
        cluster_id = self.create_cluster(name=cluster_name)
        self.bootstrap_nodes(self.nodes().slaves[:2])
        self.update_nodes(cluster_id, nodes)

        # assign all networks to second network interface:
        nets = self.client.get_networks(cluster_id)['networks']
        nailgun_nodes = self.client.list_cluster_nodes(cluster_id)
        for node in nailgun_nodes:
            self.update_node_networks(node['id'], interfaces)

        # select networks that will be untagged:
        [net.update(vlan_turn_off) for net in nets]

        # stop using VLANs:
        self.client.update_network(cluster_id,
                                   networks=nets)

        # run network check:
        task = self.run_network_verify(cluster_id)
        self.assert_task_failed(task, 60 * 5)

        # deploy cluster:
        task = self.deploy_cluster(cluster_id)
        self.assert_task_failed(task)


if __name__ == '__main__':
    unittest.main()
