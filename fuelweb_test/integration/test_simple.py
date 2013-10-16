import logging
from proboscis import test
from fuelweb_test.integration.base_node_test_case import BaseNodeTestCase
from fuelweb_test.integration.decorators import debug
from fuelweb_test.settings import EMPTY_SNAPSHOT, OPENSTACK_RELEASE, OPENSTACK_RELEASE_REDHAT


logger = logging.getLogger(__name__)
logwrap = debug(logger)

DEPLOYMENT_MODE_SIMPLE = "multinode"


class TestBasic(BaseNodeTestCase):

    @test(groups=["thread_1"])
    def setup_master(self):
        self.ci().get_empty_environment()

    @test(groups=["thread_1"], depends_on=[setup_master])
    def prepare_release(self):
        self.ci().get_active_state(EMPTY_SNAPSHOT)

        if OPENSTACK_RELEASE == OPENSTACK_RELEASE_REDHAT:
            self.update_redhat_credentials()
            self.assert_release_state(OPENSTACK_RELEASE_REDHAT,
                                      state='available')

        self.ci().make_snapshot("ready")

    @test(groups=["thread_1"], depends_on=[prepare_release])
    def prepare_slaves(self):
        self.ci().get_active_state("ready")
        self.bootstrap_nodes(self.nodes().slaves[:3])
        self.ci().make_snapshot("ready_with_3_slaves")


class TestSimpleFlat(BaseNodeTestCase):

    @test(groups=["thread_1"], depends_on=[TestBasic.prepare_slaves])
    def simple_flat_deploy(self):
        self.ci().get_active_state("ready_with_3_slaves")

        cluster_id = self.create_cluster(name=self.__class__.__name__, mode=DEPLOYMENT_MODE_SIMPLE)
        self.basic_cluster_setup(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            })
        self.deploy_cluster_wait(cluster_id)
        self.assertClusterReady(
            'slave-01', smiles_count=6, networks_count=1, timeout=300)
        self.get_ebtables(cluster_id, self.nodes().slaves[:2]).restore_vlans()
        self.ci().make_snapshot("deploy_simple_flat")

    @test(groups=["thread_1"], depends_on=[simple_flat_deploy])
    def simple_flat_verify_networks(self):
        self.ci().get_active_state("deploy_simple_flat")

        task = self._run_network_verify(self.get_last_created_cluster())
        self.assertTaskSuccess(task, 60 * 2)

    @test(groups=["thread_1"], depends_on=[simple_flat_deploy])
    def simple_flat_ostf(self):
        self.ci().get_active_state("deploy_simple_flat")

        self.run_OSTF(cluster_id=self.get_last_created_cluster(), should_fail=5, should_pass=19)
