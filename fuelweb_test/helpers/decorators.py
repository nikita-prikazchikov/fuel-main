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

import functools
import json
import logging
import os
import time
import urllib2
from fuelweb_test.settings import LOGS_DIR, ENV_NAME


def save_logs(url, filename):
    logging.info('Saving logs to "{}" file'.format(filename))
    try:
        with open(filename, 'w') as f:
            f.write(
                urllib2.urlopen(url).read()
            )
    except urllib2.HTTPError, e:
        logging.error(e)


def log_snapshot_on_error(func):
    """
    Decorator to snapshot environment when error occurred in test.
    And always fetch diagnostic snapshot from master node
    """
    @functools.wraps(func)
    def wrapper(*args, **kwagrs):
        status = "pass"
        try:
            return func(*args, **kwagrs)
        except:
            status = "fail"
            name = 'error_%s' % func.__name__
            description = "Failed in method '%s'" % func.__name__
            logging.debug("Snapshot {} {}".format(name, description))
            logging.debug(
                "You could revert this snapshot using [{command}]".format(
                    command=
                    "dos.py revert {env} --snapshot-name {name} && "
                    "dos.py resume {env}".format(
                        env=ENV_NAME, name=name
                    )
                )
            )
            if args[0].ci() is not None:
                args[0].ci().get_virtual_environment().suspend(verbose=False)
                args[0].ci().get_virtual_environment().snapshot(
                    name=name[-50:],
                    description=description,
                    force=True,
                )
            raise
        finally:
            if LOGS_DIR:
                if not os.path.exists(LOGS_DIR):
                    os.makedirs(LOGS_DIR)

                environment = args[0]
                task = environment.client.generate_logs()
                task = environment._task_wait(task, 60 * 5)
                url = "http://{}:8000{}".format(
                    environment.get_admin_node_ip(), task['message']
                )
                save_logs(
                    url,
                    os.path.join(
                        LOGS_DIR,
                        '{status}_{name}-{time}.tar.gz'.format(
                            status=status,
                            name=func.__name__,
                            time=time.strftime(
                                "%Y_%m_%d__%H_%M_%S", time.gmtime())
                        )
                    )
                )
    return wrapper


def debug(logger):
    def wrapper(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            logger.debug(
                "Calling: {} with args: {} {}".format(
                    func.__name__, args, kwargs
                )
            )
            result = func(*args, **kwargs)
            logger.debug(
                "Done: {} with result: {}".format(func.__name__, result))
            return result
        return wrapped
    return wrapper


def json_parse(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        response = func(*args, **kwargs)
        return json.loads(response.read())
    return wrapped
