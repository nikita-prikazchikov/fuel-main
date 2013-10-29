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
from proboscis import test, SkipTest

from fuelweb_test.helpers.decorators import debug, log_snapshot_on_error
from fuelweb_test.models.fuel_web_client import DEPLOYMENT_MODE_SIMPLE
from fuelweb_test.tests.base_test_case import TestBasic

logger = logging.getLogger(__name__)
logwrap = debug(logger)


@test
class OneNodeDeploy(TestBasic):

    @log_snapshot_on_error
    @test(groups=["thread_2"], depends_on=[TestBasic.prepare_release])
    def deploy_one_node(self):
        self.env.revert_snapshot("ready")
        self.fuel_web.client.get_root()
        self.env.bootstrap_nodes(self.env.nodes()[:1])

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller']}
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=4, networks_count=1, timeout=300)


@test
class SimpleFlat(TestBasic):
    @log_snapshot_on_error
    @test(groups=["thread_2"], depends_on=[TestBasic.prepare_slaves])
    def deploy_simple_flat(self):
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=6, networks_count=1, timeout=300)
        self.env.make_snapshot("deploy_simple_flat")

    @log_snapshot_on_error
    @test(groups=["thread_2"], depends_on=[deploy_simple_flat])
    def simple_flat_verify_networks(self):
        self.env.revert_snapshot("deploy_simple_flat")

        #self.env.get_ebtables(self.fuel_web.get_last_created_cluster(),
        #                      self.env.nodes().slaves[:2]).restore_vlans()
        task = self.fuel_web.run_network_verify(
            self.fuel_web.get_last_created_cluster())
        self.fuel_web.assert_task_success(task, 60 * 2, interval=10)

    @log_snapshot_on_error
    @test(groups=["thread_2"], depends_on=[deploy_simple_flat])
    def simple_flat_ostf(self):
        self.env.revert_snapshot("deploy_simple_flat")

        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=5, should_pass=19
        )


@test
class SimpleVlan(TestBasic):
    @log_snapshot_on_error
    @test(groups=["thread_2"], depends_on=[TestBasic.prepare_slaves])
    def deploy_simple_vlan(self):
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        )
        self.fuel_web.update_vlan_network_fixed(
            cluster_id, amount=8, network_size=32)
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=6, networks_count=1, timeout=300)
        self.env.make_snapshot("deploy_simple_vlan")

    @log_snapshot_on_error
    @test(groups=["thread_2"], depends_on=[deploy_simple_vlan])
    def simple_flat_verify_networks(self):
        self.env.revert_snapshot("deploy_simple_vlan")

        task = self.fuel_web.run_network_verify(
            self.fuel_web.get_last_created_cluster())
        self.fuel_web.assert_task_success(task, 60 * 2, interval=10)

    @log_snapshot_on_error
    @test(groups=["thread_2"], depends_on=[deploy_simple_vlan])
    def simple_flat_ostf(self):
        self.env.revert_snapshot("deploy_simple_vlan")

        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=5, should_pass=19
        )


@test
class UntaggedNetworksNegative(TestBasic):
    @log_snapshot_on_error
    @test(groups=["thread_1"], depends_on=[TestBasic.prepare_slaves])
    def untagged_networks_negative(self):
        raise SkipTest()
        self.env.revert_snapshot("ready_with_3_slaves")

        vlan_turn_off = {'vlan_start': None}
        interfaces = {
            'eth0': ["fixed"],
            'eth1': ["public", "floating"],
            'eth2': ["management", "storage"],
            'eth3': []
        }

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        )

        nets = self.fuel_web.client.get_networks(cluster_id)['networks']
        nailgun_nodes = self.fuel_web.client.list_cluster_nodes(cluster_id)
        for node in nailgun_nodes:
            self.fuel_web.update_node_networks(node['id'], interfaces)

        # select networks that will be untagged:
        [net.update(vlan_turn_off) for net in nets]

        # stop using VLANs:
        self.fuel_web.client.update_network(cluster_id, networks=nets)

        # run network check:
        task = self.fuel_web.run_network_verify(cluster_id)
        self.fuel_web.assert_task_failed(task, 60 * 5)

        # deploy cluster:
        task = self.fuel_web.deploy_cluster(cluster_id)
        self.fuel_web.assert_task_failed(task)
