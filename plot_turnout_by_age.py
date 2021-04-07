#!/usr/bin/env python3

VOTE_FILE = './data/ncvhis_Statewide.txt'
VOTER_FILE = './data/ncvoter_Statewide.txt'

import csv
from typing import Dict, List

ELECTION_YEAR = 2020 # choose presidential election years from 2000 - 2020
ELECTION_DAY = {
    2020: '03',
    2016: '08',
    2012: '06',
    2008: '04',
    2004: '02',
    2000: '07'
}
ELECTION_DATE = f'11/{ELECTION_DAY[ELECTION_YEAR]}/{ELECTION_YEAR}'
TOTAL_COUNTIES = 100

KEY_FILE = './key.json'

def get_votes() -> Dict[str, List[str]]:
    with open(VOTE_FILE, 'r', encoding='latin-1') as f:
        rows = csv.reader(f, delimiter = '\t')
        for row in rows:
            header = row
            break
        county_index = header.index('county_id')
        election_index = header.index('election_lbl')
        ncid_index = header.index('ncid')
        total_votes = 0
        votes = {}
        for row in rows:
            e = row[election_index]
            if e != ELECTION_DATE:
                continue
            c = row[county_index]
            if c not in votes:
                votes[c] = set()
            votes[c].add(row[ncid_index])
            total_votes += 1
        print(f'got {total_votes} votes in {len(votes)} counties.')
        return votes, total_votes

def get_voters():
    voters = {}
    with open(VOTER_FILE, 'r', encoding='latin-1') as f:
        rows = csv.reader(f, delimiter = '\t')
        for row in rows:
            header = row
            break
        county_index = header.index('county_id')
        reg_index = header.index('registr_dt')
        # TODO: filter out reg after election.
        birth_year_index = header.index('birth_year')
        ncid_index = header.index('ncid')
        total_voters = 0
        bad_ages = 0
        for row in rows:
            c = row[county_index]
            if c not in voters:
                voters[c] = []
            birth_year = int(row[birth_year_index])
            age = ELECTION_YEAR - birth_year + 1 # only an estimate.
            # we set 19 minimum because the above calculation will shift ages +1,
            # so as not to filter out people who are actually of age.
            if age < 19 or age > 120:
                bad_ages += 1
                continue
            voters[c].append({
                'reg': row[reg_index],
                'age': age,
                'ncid': row[ncid_index],
            })
            total_voters += 1
        print(f'got {total_voters} voters in {len(voters)} counties.')
        print(f'skipped {bad_ages} voters for out-of-range ages.')
    return voters, total_voters

from matplotlib import pyplot as plt

def plot_turnout(turnout: Dict[int, float], style: str = '-'):
    tt = list(turnout.items())
    tt.sort()
    plt.plot([x[0] for x in tt], [x[1] for x in tt], style)

MINIMUM_REGISTERED_VOTERS = 50

import json

if __name__ == '__main__':
    voters, total_voters = get_voters()
    votes, total_votes = get_votes()
    print(f'overall turnout for {ELECTION_DATE} election: {total_votes / total_voters}')
    plotted = 0

    key = {}

    for c in votes:
        print(f'plotting {c}')
        assert(c in voters)
        for v in voters[c]:
            v['voted'] = v['ncid'] in votes[c]

        by_age = {}
        for v in voters[c]:
            a = v['age']
            if a not in by_age:
                by_age[a] = []
            by_age[a].append(v)

        turnout = {}
        overall_turnout = len(votes[c]) / len(voters[c])
        for a in by_age:
            voter_count = len(by_age[a])
            if voter_count < MINIMUM_REGISTERED_VOTERS:
                continue
            turnout[a] = len([x for x in by_age[a] if x['voted']]) / voter_count / overall_turnout
                 
        plot_turnout(turnout)

        for a in turnout:
            if a not in key:
                key[a] = []
            key[a].append(turnout[a])

        plotted += 1

    for a in key:
        key[a] = sum(key[a]) / len(key[a]) 

    json.dump(key, open(KEY_FILE, 'w'))
    plot_turnout(key, ':k')

    print(f'plotted {plotted} counties.')
    plt.xlabel(f'Age (ages with less than {MINIMUM_REGISTERED_VOTERS} registered voters are hidden)')
    plt.ylabel('Normalized voter turnout (votes / registered voters / overall turnout fraction)')
    plt.title(f'{ELECTION_YEAR} North Carolina Voter Turnout vs. Age ({plotted} of {TOTAL_COUNTIES} counties; each line = 1 county)')
    plt.show()
