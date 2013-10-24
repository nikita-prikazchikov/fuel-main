import logging
from proboscis import test
from fuelweb_test.helpers.environment import EnvironmentModel
from fuelweb_test.helpers.decorators import debug
from fuelweb_test.settings import *


logger = logging.getLogger(__name__)
logwrap = debug(logger)

DEPLOYMENT_MODE_SIMPLE = "multinode"


class TestBasic(object):

    def __init__(self):
        self.environment = EnvironmentModel()
        super(TestBasic, self).__init__()

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
