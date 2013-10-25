import logging
from proboscis import test
from fuelweb_test.models.environment import EnvironmentModel
from fuelweb_test.helpers.decorators import debug
from fuelweb_test.settings import *

logger = logging.getLogger(__name__)
logwrap = debug(logger)

DEPLOYMENT_MODE_SIMPLE = "multinode"


class TestBasic(object):

    def __init__(self):
        self.environment = EnvironmentModel()
        self.fuel_web = self.environment.fuel_web
        super(TestBasic, self).__init__()

    @test(groups=["thread_1"])
    def setup_master(self):
        self.environment.setup_environment()
        self.environment.make_snapshot(EMPTY_SNAPSHOT)

    @test(groups=["thread_1"], depends_on=[setup_master])
    def prepare_release(self):
        self.ci().revert_snapshot(EMPTY_SNAPSHOT)

        if OPENSTACK_RELEASE == OPENSTACK_RELEASE_REDHAT:
            self.fuel_web.update_redhat_credentials()
            self.fuel_web.assert_release_state(
                OPENSTACK_RELEASE_REDHAT,
                state='available'
            )
        self.environment.make_snapshot("ready")

    @test(groups=["thread_1"], depends_on=[prepare_release])
    def prepare_slaves(self):
        self.ci().revert_snapshot("ready")
        self.bootstrap_nodes(self.nodes().slaves[:3])
        self.ci().make_snapshot("ready_with_3_slaves")
