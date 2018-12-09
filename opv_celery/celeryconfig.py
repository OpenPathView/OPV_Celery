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

broker_url = 'redis://OPV_Master:6379/0'
result_backend = 'redis://OPV_Master:6379/1'

task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']

opv_log_dir = '/home/opv/logs/celery'
opv_log_use_ip = True
opv_log_port = 80
opv_log_path = '/celery'
