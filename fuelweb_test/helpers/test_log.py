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

import hashlib
import json

import logging
import datetime
import os
import uuid
from fuelweb_test.settings import OPENSTACK_RELEASE

logger = logging.getLogger(__name__)


class LogTestCase(object):

    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"

    def __init__(self, name, tags=None):
        super(LogTestCase, self).__init__()
        self.id = str(uuid.uuid4())
        self.name = name
        self.start_time = datetime.datetime.now()
        self.end_time = None
        self.status = self.PASS
        self.tags = tags or []
        self.steps = []
        self.environment = OPENSTACK_RELEASE
        self._depth = 0
        self.caught = False

    def add_test_step(self, test_step):
        depth = self._depth
        steps = self.steps
        while depth > 0:
            if len(steps) > 0:
                steps = steps[-1].steps
                depth -= 1
            else:
                break

        steps.append(test_step)

    def add_depth_level(self):
        self._depth += 1

    def pop_depth_level(self):
        if self._depth > 0:
            self._depth -= 1

    def set_status(self, status):
        self.status = status

    def info(self, text):
        self.add_test_step(TestStep(text))

    def finish(self):
        if self.end_time is None:
            self.end_time = datetime.datetime.now()

    def save(self, directory):

        self.finish()
        logger.debug(self)

        name = hashlib.sha1()
        name.update(self.name)
        name.update(str(self.tags))
        name.update(str(self.start_time))
        name.update(str(self.end_time))

        file_name = os.path.join(directory, name.hexdigest() + ".json")

        with open(file_name, 'w') as f:
            f.write(self.__repr__())

    def __repr__(self):
        return json.dumps({
            "name": self.name,
            "start_time": str(self.start_time),
            "end_time": str(self.end_time),
            "duration": str(self.end_time - self.start_time),
            "environment": self.environment,
            "status": self.status,
            "tags": self.tags,
            "steps": [step.to_object() for step in self.steps]
        }, indent=4)


class TestStep(object):
    def __init__(self, name):
        super(TestStep, self).__init__()
        self.name = name
        self.status = LogTestCase.PASS
        self.steps = []

    def to_object(self):
        return {
            "name": self.name,
            "status": self.status,
            "steps": [step.to_object() for step in self.steps]
        }

    def set_status(self, status):
        self.status = status