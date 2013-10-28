import logging
from proboscis import test, SkipTest
from fuelweb_test.models.environment import EnvironmentModel
from fuelweb_test.helpers.decorators import debug
from fuelweb_test.settings import *

logger = logging.getLogger(__name__)
logwrap = debug(logger)


class TestBasic(object):

    def __init__(self):
        self.env = EnvironmentModel()
        self.fuel_web = self.env.fuel_web
        super(TestBasic, self).__init__()

    @test(groups=["thread_1"])
    def setup_master(self):
        self.env.setup_environment()
        self.env.make_snapshot(EMPTY_SNAPSHOT)

    @test(groups=["thread_1"], depends_on=[setup_master])
    def prepare_release(self):
        self.env.revert_snapshot(EMPTY_SNAPSHOT)

        if OPENSTACK_RELEASE == OPENSTACK_RELEASE_REDHAT:
            self.fuel_web.update_redhat_credentials()
            self.fuel_web.assert_release_state(
                OPENSTACK_RELEASE_REDHAT,
                state='available'
            )
        self.env.make_snapshot("ready")

    @test(groups=["thread_1"], depends_on=[prepare_release])
    def prepare_slaves(self):
        self.env.revert_snapshot("ready")
        self.env.bootstrap_nodes(self.env.nodes().slaves[:3])
        self.env.make_snapshot("ready_with_3_slaves")
