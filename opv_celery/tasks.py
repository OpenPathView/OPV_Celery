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

from celery import Celery

import os
from opv_api_client import RestClient
from opv_tasks.__main__ import run
from opv_directorymanagerclient import DirectoryManagerClient, Protocol

#: Set default configuration module name
os.environ.setdefault('CELERY_CONFIG_MODULE', 'opv_celery.celeryconfig')

app = Celery()
app.config_from_envvar('CELERY_CONFIG_MODULE')

@app.task
def make_all(options):

    # Get the address to Directory Manager
    # Variable.setdefault("OPV-DM", "http://OPV_Master:5005")
    # opv_dm = Variable.get("OPV-DM")
    opv_dm = "http://OPV_Master:5005"

    # Get the address to DB rest API
    # Variable.setdefault("OPV-API", "http://OPV_Master:5000")
    # opv_api = Variable.get("OPV-API")
    opv_api = "http://OPV_Master:5000"

    dir_manager_client = DirectoryManagerClient(
        api_base=opv_dm, default_protocol=Protocol.FTP
    )

    db_client = RestClient(opv_api)

    try:
        run(dir_manager_client, db_client, "makeall", options)
        return "Success for lot %s for malette %s" % (options["id_lot"], options["id_malette"])
    except Exception as e:
        print(str(e))
        return "Error for lot %s for malette %s" % (options["id_lot"], options["id_malette"])


if __name__ == "__main__":
     app.worker_main()
