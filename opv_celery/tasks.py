# Copyright (C) 2018 NOUCHET Christophe
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

import os
import time
import socket
import logging

from celery import Celery, group, states


from opv_api_client import RestClient
from opv_tasks.utils import find_task
from opv_directorymanagerclient import DirectoryManagerClient, Protocol


#: Set default configuration module name
os.environ.setdefault('CELERY_CONFIG_MODULE', 'opv_celery.celeryconfig')

app = Celery()
app.config_from_envvar('CELERY_CONFIG_MODULE')


class MyException(Exception):
     pass


class MyLittleLogger:

    def __init__(self, name):
        """
        Make a logger
        :param name: The name of the logger
        :return: logger, path to log file, the url to the log file
        """
        self.logger = logging.getLogger(name)
        try:
            self.filename = "%s-%s.txt" % (name, int(time.time() * 1000))
            self.file_path = os.path.join(app.conf["opv_log_dir"], self.filename)
            formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s [%(lineno)d]')
            fh = logging.FileHandler(self.file_path)
            fh.setLevel(logging.INFO)
            self.handler = fh.setFormatter(formatter)
            self.logger.addHandler(fh)
        except Exception:
            logging.exception("Can't create MyLittleLogger")
            pass

    def remove(self):
        """Remove the log file"""
        try:
            self.handler.close()
            self.logger.removeHandler(self.handler)
            os.remove(self.file_path)
        except Exception:
            pass

    @property
    def hostname(self):
        """Get the hostname"""
        host = socket.gethostname()
        return socket.gethostbyname(host) if app.conf["opv_log_use_ip"] else host

    @property
    def url(self):
        try:
            return "http://%s:%s%s/%s" % (
                self.hostname, app.conf["opv_log_port"], app.conf["opv_log_path"], self.filename
            )
        except Exception:
            return "Generic Error"


def run(dm_c, db_c, task_name, inputData, logger=None):
    """
    Run task.
    Return a TaskReturn.
    """
    Task = find_task(task_name)
    if not Task:
        raise Exception('Task %s not found' % task_name)

    task = Task(client_requestor=db_c, opv_directorymanager_client=dm_c)
    if logger:
        task.logger = logger
        task.shell_logger = logger

    return task.run(options=inputData)

@app.task()
def this_is_a_test(ok):
    logger_class = MyLittleLogger("This_is_a_test_%s" % ok)

    if ok:
        logger_class.logger.info("This is ok")
        logger_class.remove()
        return "Is ok"
    else:
        logger_class.logger.error("This is an error")
        raise MyException("Error %s" % logger_class.url)


@app.task()
def make_all(options):

    logger_class = MyLittleLogger("make_all_%s_%s" % (options["id_lot"], options["id_malette"]))

    # Get the address to Directory Manager
    # Variable.setdefault("OPV-DM", "http://OPV_Master:5005")
    # opv_dm = Variable.get("OPV-DM")
    opv_dm = "http://%s:%s" % (
        str(os.getenv("OPV_TASKS_DIRMANAGER_ADDRESS", "opv_master")),
        str(os.getenv("OPV_TASKS_DIRMANAGER_PORT", 5005))
    )

    # Get the address to DB rest API
    # Variable.setdefault("OPV-API", "http://OPV_Master:5000")
    # opv_api = Variable.get("OPV-API")
    opv_api = "http://%s:%s" % (
       str(os.getenv("OPV_TASKS_DBREST_ADDRESS", "opv_master")),
       str(os.getenv("OPV_TASKS_DBREST_PORT", 5000))
    )

    dir_manager_client = DirectoryManagerClient(
        api_base=opv_dm, default_protocol=Protocol.FTP
    )

    db_client = RestClient(opv_api)

    try:
        run(dir_manager_client, db_client, "makeall", options, logger_class.logger)
        logger_class.remove()
        return "Success lot=%s malette=%s" % (options["id_lot"], options["id_malette"])
    except Exception as e:
        msg = "Error lot=%s malette=%s msg='%s'" % (options["id_lot"], options["id_malette"], str(e))
        logger_class.logger.error(msg)
        raise MyException("Error %s" % logger_class.url)


if __name__ == "__main__":
     app.worker_main()
