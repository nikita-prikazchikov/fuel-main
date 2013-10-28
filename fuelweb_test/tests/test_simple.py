import logging
from proboscis import test, SkipTest

from fuelweb_test.helpers.decorators import debug
from fuelweb_test.models.fuel_web_client import DEPLOYMENT_MODE_SIMPLE
from fuelweb_test.tests.base_test_case import TestBasic


logger = logging.getLogger(__name__)
logwrap = debug(logger)


@test
class TestSimpleFlat(TestBasic):
    @test(groups=["thread_1"], depends_on=[TestBasic.prepare_slaves])
    def simple_flat_deploy(self):
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

    @test(groups=["thread_1"], depends_on=[simple_flat_deploy])
    def simple_flat_verify_networks(self):
        self.env.revert_snapshot("deploy_simple_flat")

        #self.env.get_ebtables(self.fuel_web.get_last_created_cluster(),
        #                      self.env.nodes().slaves[:2]).restore_vlans()
        task = self.fuel_web.run_network_verify(
            self.fuel_web.get_last_created_cluster())
        self.fuel_web.assert_task_success(task, 60 * 2, interval=10)

    @test(groups=["thread_1"], depends_on=[simple_flat_deploy])
    def simple_flat_ostf(self):
        self.env.revert_snapshot("deploy_simple_flat")

        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=5, should_pass=19
        )
