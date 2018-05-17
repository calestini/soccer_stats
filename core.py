#!/usr/bin/python

#Key Libraries
from sshtunnel import SSHTunnelForwarder
import psycopg2
import pandas as pd
import numpy as np
import json
import scipy
from sklearn.utils.extmath import cartesian
import matplotlib.pyplot as plt
import seaborn as sns

code_toggle = '''
<script>
    code_show=true;

    function code_toggle() {
         if (code_show){
             $('div.input').hide();
            } else {
             $('div.input').show();
            }
         code_show = !code_show
    }

    $( document ).ready(code_toggle);
</script>

The raw code for this IPython notebook is by default hidden for easier reading.
To toggle on/off the raw code, click <a href="javascript:code_toggle()">here</a>.'''


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


def probability_matrix(events, hometeam, awayteam, goals_list, season='2016/2017', save_image=False):
    """
    :events: dataframe with fixture/events data
    :return: probability matrix with all combinations
    """
    events_season = events[events['season'].isin(season)]
    dedup_events = events_season[[
            'fixture_id','localname', 'localteam_score','visitorteam_score',
            'visitorname','season'
        ]].drop_duplicates()

    average_home = np.sum(dedup_events['localteam_score'])/len(dedup_events)
    average_away = np.sum(dedup_events['visitorteam_score'])/len(dedup_events)

    #attack strength
    home_att_home = np.sum(dedup_events[dedup_events['localname']==hometeam]['localteam_score'])/len(dedup_events[dedup_events['localname']==hometeam])/average_home
    #home_att_away = np.sum(dedup_events[dedup_events['visitorname']==hometeam]['visitorteam_score'])/len(dedup_events[dedup_events['visitorname']==hometeam])/average_away
    #away_att_home = np.sum(dedup_events[dedup_events['localname']==awayteam]['localteam_score'])/len(dedup_events[dedup_events['localname']==awayteam])/average_home
    away_att_away = np.sum(dedup_events[dedup_events['visitorname']==awayteam]['visitorteam_score'])/len(dedup_events[dedup_events['visitorname']==awayteam])/average_away

    #defense strength
    home_def_home = np.sum(dedup_events[dedup_events['localname']==hometeam]['visitorteam_score'])/len(dedup_events[dedup_events['localname']==hometeam])/average_away
    #home_def_away = np.sum(dedup_events[dedup_events['visitorname']==hometeam]['localteam_score'])/len(dedup_events[dedup_events['visitorname']==hometeam])/average_home
    #away_def_home = np.sum(dedup_events[dedup_events['localname']==awayteam]['visitorteam_score'])/len(dedup_events[dedup_events['localname']==awayteam])/average_away
    away_def_away = np.sum(dedup_events[dedup_events['visitorname']==awayteam]['localteam_score'])/len(dedup_events[dedup_events['visitorname']==awayteam])/average_home

    #expected goals
    #goals home will score:
    home_goals = home_att_home * away_def_away * average_home

    #goals away will score;
    away_goals = away_att_away * home_def_home * average_away

    #poisson distrib.
    poisson = scipy.stats.distributions.poisson
    goals = goals_list
    home_prob = poisson.pmf(goals, home_goals)
    away_prob = poisson.pmf(goals, away_goals)

    home_df = pd.DataFrame([home_prob,goals], index=['home_prob','home_score']).transpose()
    away_df = pd.DataFrame([away_prob,goals], index=['away_prob','away_score']).transpose()

    #probability matrix with all scores combinations
    all_results = pd.DataFrame(cartesian([home_prob, away_prob]), columns = ['home_prob','away_prob']).merge(
        home_df, on='home_prob', how='inner'
    ).merge(
        away_df, on='away_prob', how='inner'
    )

    home_prob = np.sum(
        all_results[all_results['home_score'] > all_results['away_score']]['home_prob']*
        all_results[all_results['home_score'] > all_results['away_score']]['away_prob']
    )


    tie_prob = np.sum(
        all_results[all_results['home_score'] == all_results['away_score']]['home_prob']*
        all_results[all_results['home_score'] == all_results['away_score']]['away_prob']
    )


    away_prob = np.sum(
        all_results[all_results['home_score'] < all_results['away_score']]['home_prob']*
        all_results[all_results['home_score'] < all_results['away_score']]['away_prob']
    )

    outcome = [home_prob, tie_prob, 1. - (home_prob+tie_prob)] # using 1.- to add to complete 100.00%

    all_results['prob'] = all_results['home_prob']*all_results['away_prob']
    prob_matrix = all_results.pivot('home_score', 'away_score', 'prob')

    #plot
    plt.figure(figsize=(16,8))
    plt.subplot2grid((2, 4), (0, 0), rowspan=2, colspan=2)
    axx = sns.heatmap(prob_matrix, annot=True, fmt = '.2%', square=1, linewidth=1.)
    axx.invert_yaxis()
    plt.title('{0} vs. {1}\n'.format(hometeam, awayteam), fontsize=17)
    plt.xlabel(awayteam)
    plt.ylabel(hometeam)

    ax = plt.subplot2grid((2, 4), (0, 2))
    plt.title('Goal Distribution\n', fontsize=17)
    sns.countplot(dedup_events[dedup_events['localname'] == hometeam]['localteam_score'], color='#f15b24')
    plt.xlabel('Hometeam: {0}'.format(hometeam))
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.yticks([], [])
    plt.ylabel('')

    ax1 = plt.subplot2grid((2, 4), (1, 2))
    sns.countplot(dedup_events[dedup_events['visitorname'] == awayteam]['visitorteam_score'], color='#363e4f')
    plt.xlabel('Awayteam: {0}'.format(awayteam))
    ax1.spines['top'].set_visible(False)
    ax1.spines['left'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    plt.yticks([], [])
    plt.ylabel('')

    ax2 = plt.subplot2grid((2, 4), (0, 3), rowspan=2)
    plt.title('3-way odds\n', fontsize=17)
    plt.bar(range(len(outcome)),outcome, color=['#f15b24','grey','#363e4f'])
    plt.xticks(range(len(outcome)), [hometeam, 'tie',awayteam])
    ax2.spines['top'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    plt.yticks([], [])
    plt.ylabel('')
    plt.text(-0.2, outcome[0]+0.01, '{:.1%}'.format(outcome[0]), fontsize=12)
    plt.text(0.8, outcome[1]+0.01, '{:.1%}'.format(outcome[1]), fontsize=12)
    plt.text(1.8, outcome[2]+0.01, '{:.1%}'.format(outcome[2]), fontsize=12)

    plt.tight_layout()
    if save_image:
        plt.savefig('{0}_{1}.png'.format(hometeam, awayteam))
    plt.show()

    return prob_matrix

################################################################################
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
