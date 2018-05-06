#!/usr/bin/python

#Key Libraries
from sshtunnel import SSHTunnelForwarder
import psycopg2
import pandas as pd
import json

def direct_query(querystring, settings_json='../settings.json'):
    with open(settings_json) as f:
        settings = json.load(f, strict=False)

    with SSHTunnelForwarder(
        (settings['torneo']['remote_host'], settings['torneo']['remote_ssh_port']),
        ssh_pkey = settings['torneo']['ssh_pkey'],
        remote_bind_address=('localhost', settings['torneo']['port']),
        local_bind_address=('localhost', settings['torneo']['port'])):

        conn = psycopg2.connect(
            "host=localhost" + " dbname=" + settings['torneo']['dbname'] +
            " user=" + settings['torneo']['dbuser'] + " password=" +
            settings['torneo']['dbpassword']
        )

        results = pd.read_sql(querystring, conn)
        conn.close()
    return results

def events(settings_json = '../settings.json', league=8):
    with open(settings_json) as f:
        settings = json.load(f, strict=False)

    querystring = queryevent = settings['queries']['event'].format(league)
    event_data = direct_query(querystring, settings_json = settings_json)
    return event_data

#reading settings file
class queryTorneo(object):

    """docstring for queryTorneo."""

    def __init__(self, settings_json = '../settings.json'):
        with open(settings_json) as f:
            self.settings = json.load(f, strict=False)

    def query(self, querystring):

        with SSHTunnelForwarder(
            (self.settings['torneo']['remote_host'], self.settings['torneo']['remote_ssh_port']),
            ssh_pkey = self.settings['torneo']['ssh_pkey'],
            remote_bind_address=('localhost', self.settings['torneo']['port']),
            local_bind_address=('localhost', self.settings['torneo']['port'])
        ):

            conn = psycopg2.connect(
                "host=localhost" + " dbname=" + self.settings['torneo']['dbname'] +
                " user=" + self.settings['torneo']['dbuser'] + " password=" +
                self.settings['torneo']['dbpassword']
            )

            results = pd.read_sql(querystring, conn)
            conn.close()

        return results


class soccer(object):
    """docstring for events."""
    def __init__(self, settings_json = '../settings.json'):
        self.queryTorneo = queryTorneo(settings_json)

    def get_events(self, league=8):
        self.league=league
        queryevent = self.queryTorneo.settings['queries']['event'].format(self.league)
        self.events = self.queryTorneo.query(queryevent)
