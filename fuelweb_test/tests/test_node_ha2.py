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
from fuelweb_test.models.fuel_web_model import Environment_Model
from fuelweb_test.helpers.decorators import snapshot_errors, \
    debug, fetch_logs

logging.basicConfig(
    format=':%(lineno)d: %(asctime)s %(message)s',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)
logwrap = debug(logger)


class TestNode(Environment_Model):
    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos', 'redhat', "ubuntu"], test_thread='thread_4')
    def test_ha_cluster_flat(self):
        cluster_id = self.prepare_environment(
            name="ha_flat",
            mode="ha_compact",
            settings={
                'nodes': {
                    'slave-01': ['controller'],
                    'slave-02': ['controller'],
                    'slave-03': ['controller'],
                    'slave-04': ['compute'],
                    'slave-05': ['compute']
                }
            }
        )
        self.assertClusterReady(
            'slave-01', smiles_count=16, networks_count=1, timeout=300)
        self.get_ebtables(cluster_id, self.nodes().slaves[:5]).restore_vlans()
        task = self._run_network_verify(cluster_id)
        self.assertTaskSuccess(task, 60 * 2)
        self.run_OSTF(
            cluster_id=cluster_id,
            test_sets=['ha', 'smoke', 'sanity'],
            should_fail=4, should_pass=24)

    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos', 'redhat', "ubuntu"], test_thread='thread_4')
    def test_ha_add_compute(self):
        cluster_id = self.prepare_environment(
            name="ha_flat",
            mode="ha_compact",
            settings={
                'nodes': {
                    'slave-01': ['controller'],
                    'slave-02': ['controller'],
                    'slave-03': ['controller'],
                    'slave-04': ['compute'],
                    'slave-05': ['compute']
                }
            }
        )

        self.bootstrap_nodes(self.nodes().slaves[5:6])
        self.update_nodes(cluster_id, {'slave-06': ['compute']}, True, False)

        task = self.client.deploy_cluster_changes(cluster_id)
        self.assertTaskSuccess(task)
        self.assertEqual(6, len(self.client.list_cluster_nodes(cluster_id)))

        self.run_OSTF(
            cluster_id=cluster_id,
            test_sets=['ha', 'smoke', 'sanity'],
            should_fail=4, should_pass=24)

if __name__ == '__main__':
    unittest.main()
