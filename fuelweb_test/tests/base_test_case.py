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

from fuelweb_test.models.environment import EnvironmentModel
from fuelweb_test.helpers.decorators import debug
from fuelweb_test.settings import *

logging.basicConfig(
    format='%(asctime)s - %(levelname)s %(filename)s:'
           '%(lineno)d -- %(message)s',
    level=logging.DEBUG
)

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
        self.env.make_snapshot("empty")

    @test(groups=["thread_1"], depends_on=[setup_master])
    def prepare_release(self):
        self.env.revert_snapshot("empty")

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

    @test(groups=["thread_3", "thread_4"], depends_on=[prepare_release])
    def prepare_5_slaves(self):
        self.env.bootstrap_nodes(self.env.nodes().slaves[:5])
        self.env.make_snapshot("ready_with_5_slaves")