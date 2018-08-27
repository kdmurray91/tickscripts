#!/usr/bin/env python3
import sys
import json
import requests
import datetime
import yaml
from github import Github, GithubObject
config = json.load(open('/home/stormaes/tickscripts/config.json'))
g = Github(config['token'])

user = g.get_organization(config['org'])
repo = user.get_repo(config['repo'])
data = json.load(sys.stdin)

slack_hook = config.get("slack_webhook")

full_title = "[{}] {}".format(data['level'], data['id'])

day_of_week = datetime.datetime.today().weekday()
r = requests.get("https://raw.githubusercontent.com/appf-anu/tickets/master/schedule.yaml")

schedule_data = yaml.load(r.content)

always = None

if type(schedule_data['notify_always']) is list:
    always = ",".join(schedule_data['notify_always'])
elif type(schedule_data['notify_always']) is str:
    always = schedule_data['notify_always'].strip()

all_assignees = schedule_data['notify_on_days'][day_of_week]

if always is not None and always not in ["", ",", " "]:
    all_assignees = ",".join([always, schedule_data['notify_on_days'][day_of_week]])

def notify_slack(issue, updated=False):

    color = "#36a64f"
    if "CRITICAL" in data['level']:
        color = "#FF0000"
    request_data = {
        "attachments": [
            {
                "fallback": data['message'],
                "color": color,
                "pretext": data['id'],
                "title": issue.title,
                "title_link": issue.html_url,
                "text": "This git issue was just {}".format("created" if not updated else "updated"),
                "footer": "Kapacitor"
            }
        ]
    }

    r = requests.post(
        slack_hook,
        data = json.dumps(request_data),
        headers = {'Content-Type': 'application/json'}
    )
    print(r)

def make_issue():
    kwargs = {
        "body": data['message'],
        "labels": [data['level']]
    }

    if "," in all_assignees:
        kwargs["assignees"] = [x.strip() for x in all_assignees.split(',')]
    else:
        kwargs["assignee"] = all_assignees.strip()

    return repo.create_issue(full_title, **kwargs)

for iss in repo.get_issues():
    if data['id'] in iss.title:
        iss.create_comment(data['message'])
        notify_slack(iss, updated=True)
        sys.exit(0)

iss = make_issue()
notify_slack(iss)
