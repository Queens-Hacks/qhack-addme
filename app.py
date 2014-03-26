#!/usr/bin/env python
from re import search
from os import environ
from requests import Session
from flask import Flask, request

app = Flask(__name__)
app.config.update(TOKEN=environ['TOKEN'],
                  SLACK_TEAM=environ['SLACK_TEAM'],
                  SLACK_EMAIL=environ['SLACK_EMAIL'],
                  SLACK_PASSWORD=environ['SLACK_PASSWORD'])


slack_url = 'https://{teamname}.slack.com'.format(teamname=app.config['SLACK_TEAM'])
invite_url = '{}/admin/invites'.format(slack_url)
gateway_url = '{}/account/gateways'.format(slack_url)
crumb_re = r'type="hidden" name="crumb" value="(.*)" />'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36',
}

invite_form = """
<h1>join the qhack chat slack</h1>
<form action="" method="post">
  <label for="email">email address</label>
  <input type="email" name="email" id="email" placeholder="email address" />
  <button type="submit">join</button>
</form>
"""

welcome = """
<h1>invited. check your email.</h1>
<p>Once you're in slack, you can either use their UI, or connect via IRC or XMPP.
IRC and XMPP config details will be at <a href="{gateway_url}">/account/gateways</a></p>
""".format(gateway_url=gateway_url)

def login(session):
    login_page_resp = session.get(slack_url, headers=headers)
    assert login_page_resp.ok, 'could not load login page'
    crumb = search(crumb_re, login_page_resp.text).groups()[0]
    auth = {'signin': 1,
            'email': app.config['SLACK_EMAIL'],
            'password': app.config['SLACK_PASSWORD'],
            'crumb': crumb}
    resp = session.post(slack_url, data=auth, headers=headers)
    assert resp.ok, 'could not log in'

def post_invite(session, email):
    invite_page_resp = session.get(invite_url, headers=headers)
    assert invite_page_resp.ok, 'could not load invite page'
    crumb = search(crumb_re, invite_page_resp.text).groups()[0]
    invite = {'invite': 1,
              'crumb': crumb,
              'emails': email}
    resp = session.post(invite_url, data=invite, headers=headers)
    assert resp.ok, 'could not invite {}'.format(email)

def invite(email):
    session = Session()
    login(session)
    post_invite(session, email)

@app.route('/join-slack/<token>', methods=['GET', 'POST'])
def signup(token):
    if token != app.config['TOKEN']:
        return 'nope', 401
    email = request.form.get('email')
    if email is not None:
        invite(email)
        return welcome
    return invite_form

@app.route('/')
def hello():
    return 'nope', 401


if __name__ == '__main__':
    app.run(debug=True)
