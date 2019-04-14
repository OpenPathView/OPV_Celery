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

# Author: Christophe NOUCHET
# Email: nouchet.christophe@gmail.com
# Documentation: Scrit to launch OPV_Task with Spark.
# Todo:
#  * Allow to launch make campaign with the id not only the name

import sys
import json
from opv_api_client import RestClient
from opv_api_client.ressources import Campaign
from opv_tasks.__main__ import run
from opv_directorymanagerclient import DirectoryManagerClient, Protocol

from opv_celery.tasks import make_all


def get_campagain_by_id(campaign_id, id_malette):
    # Get all the campaigns
    db_client = RestClient("http://%s:%s" % (
       str(os.getenv("OPV_TASKS_DBREST_ADDRESS", "opv_master")),
       str(os.getenv("OPV_TASKS_DBREST_PORT", 5000))
    ))
    # campaigns = db_client.make_all(Campaign)
    campaigns = db_client.make(Campaign, campaign_id, id_malette)

    return campaigns


def launchAllOPVTask(data):
    options = json.loads(data)

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
    dir_manager_client = DirectoryManagerClient(
        api_base=opv_dm, default_protocol=Protocol.FTP
    )

    db_client = RestClient("http://%s:%s" % (
       str(os.getenv("OPV_TASKS_DBREST_ADDRESS", "opv_master")),
       str(os.getenv("OPV_TASKS_DBREST_PORT", 5000))
    )) 

    try:
        run(dir_manager_client, db_client, "makeall", options)
    except Exception as e:
        print(str(e))

def getStitchableCps(lot):
    """
    get stitchable CP of a lot if it as some, or empty list.
    :param lot: a lot.
    :return: a list of stitchable CPs
    """
    return [cp for cp in lot.cps if cp.stichable]

def found_no_make_lot(lots):
    db_client = RestClient("http://%s:%s" % (
       str(os.getenv("OPV_TASKS_DBREST_ADDRESS", "opv_master")),
       str(os.getenv("OPV_TASKS_DBREST_PORT", 5000))
    ))


    lot_to_make = []

    for lot in lots:
        if is_usable_lot(lot, lot.id_malette, db_client):
            lot_to_make.append({"id_lot": lot.id_lot, "id_malette": lot.id_malette})

    return lot_to_make

def is_usable_lot(lot, malette_id, client_requestor):
    """
    Check if a lot is usable (have a photosphere)
    :param lot:
    :return: Boolean
    """

    if isinstance(lot, int):
        # Get the lot
        try:
            panorama = client_requestor.make(ressources.Lot, lot, malette_id)
            lot_used = panorama.cp.lot
        except Exception:
            print("%s is not a valid panorama id!" % lot)
            return None
    else:
        lot_used = lot

    pano = None
    for cp in lot_used.cps:
        for panorama in cp.panorama:
            if panorama.id_panorama is None:
                continue
            if not panorama.is_photosphere:
                continue
            pano = panorama
            break
    return pano is None

def launch(campaign_id, id_malette):
    campaign = get_campagain_by_id(campaign_id, id_malette)
    
    results = found_no_make_lot(campaign.lots)

    print("%s panorama to make: %s" % (len(results), results))
    for lot in results:
        make_all.delay(lot)

def main():
    campaign_id = 1
    id_malette = 42
    if len(sys.argv) >= 3:
        campaign_id = int(sys.argv[1])
        id_malette = int(sys.argv[2])

    launch(campaign_id, id_malette)
