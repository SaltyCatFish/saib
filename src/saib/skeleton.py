#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following lines in the
[options.entry_points] section in setup.cfg:

    console_scripts =
         fibonacci = tracker.skeleton:run

Then run `python setup.py install` which will install the command `fibonacci`
inside your current environment.
Besides console scripts, the header (i.e. until _logger...) of this file can
also be used as template for Python modules.

Note: This skeleton file can be safely removed if not needed!
"""

import argparse
import logging
import os
import re
import sys

import paramiko
import pymysql
import pymysql.cursors

from saib import __version__

SAIB_ADDRESS_KEY_NAME = "Saib_Address"
SAIB_USER_NAME = 'saib'
SAIB_KEY_NAME = "saib"

CEREBRO_SSH_PORT = 22
CEREBRO_SSH_ADDRESS = "192.168.0.1"
CEREBRO_SSH_USER_NAME = "root"
CEREBRO_SSH_KEY_NAME = "Cerebro_SSH"

__author__ = "Ryan Long"
__copyright__ = "Ryan Long"
__license__ = "mit"

_logger = logging.getLogger(__name__)


def parse_update(update):
    result = []
    for entry in update:
        result.append(parse_update_entry(entry))
    return result


def parse_update_entry(entry):
    map = {
        "name": 0,
        "ip": 1,
        "mac": 3,
    }

    data = re.split(r'\s', entry.strip())
    name = clean_update_item_string(data[map["name"]])
    ip = clean_update_item_string(data[map["ip"]])
    mac_address = clean_update_item_string(data[map["mac"]])
    return {
        "name": name,
        "ip": ip,
        "mac_address": mac_address,
    }


def clean_update_item_string(string):
    return str(string.replace("(", "").replace(")", ""))


def fetch_router_data(): # pragma: no cover
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(CEREBRO_SSH_ADDRESS, CEREBRO_SSH_PORT, CEREBRO_SSH_USER_NAME,
                get_credentials()[CEREBRO_SSH_KEY_NAME])
    (ssh_stdin, ssh_stdout, ssh_stderr) = ssh.exec_command("arp -a")
    return [entry for entry in ssh_stdout]


def get_credentials():
    return {
        CEREBRO_SSH_KEY_NAME: os.getenv(CEREBRO_SSH_KEY_NAME),
        SAIB_KEY_NAME: os.getenv(SAIB_KEY_NAME),
        SAIB_ADDRESS_KEY_NAME: os.getenv(SAIB_ADDRESS_KEY_NAME)
    }


def update():
    write_update(parse_update(fetch_router_data()))


def write_update(parsed_data): # pragma: no cover
    connection = pymysql.connect(host=get_credentials()[SAIB_ADDRESS_KEY_NAME],
                                 user=SAIB_USER_NAME,
                                 password=get_credentials()[SAIB_KEY_NAME],
                                 db=SAIB_USER_NAME,
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    try:
        with connection.cursor() as cursor:
            for item in parsed_data:
                sql = "INSERT INTO `log_in_range` (`ip`, `mac_address`, `name`) VALUES (%s, %s, %s)"
                cursor.execute(sql,
                               (item["ip"], item["mac_address"], item["name"]))
                connection.commit()
    finally:
        connection.close()


def parse_args(args):
    """Parse command line parameters

    Args:
      args ([str]): command line parameters as list of strings

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(
        description="Saib tracker")
    parser.add_argument(
        '--version',
        action='version',
        version='tracker {ver}'.format(ver=__version__))
    parser.add_argument(
        '-u',
        '--update',
        help="Fetches updated info and posts to persistence",
        action='store_true')
    parser.add_argument(
        '-v',
        '--verbose',
        dest="loglevel",
        help="set loglevel to INFO",
        action='store_const',
        const=logging.INFO)
    parser.add_argument(
        '-vv',
        '--very-verbose',
        dest="loglevel",
        help="set loglevel to DEBUG",
        action='store_const',
        const=logging.DEBUG)
    return parser.parse_args(args)


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stdout,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


def main(args):
    """Main entry point allowing external calls

    Args:
      args ([str]): command line parameter list
    """
    args = parse_args(args)
    setup_logging(args.loglevel)
    if args.update:
        _logger.info("Updating persistence...")
        update()
        _logger.info("Updating persistence complete")


def run():
    """Entry point for console_scripts
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    run()
