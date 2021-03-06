"""
MIT License

Copyright (c) 2016 Radio Revolt

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import yaml
import requests
from liquidsoap_boolean import LiquidSoapBoolean


def parse_config(configfile, slackbotfile):
    with open(configfile) as f:
        doc = yaml.load(f)
    socketfile = doc["socketfile"]
    ls_var_name = doc["liquidsoap_var_name"]
    channel = doc["slack_channel"]

    with open(slackbotfile) as f:
        doc2 = yaml.load(f)
    token = doc2["SLACK_TOKEN"]

    return socketfile, ls_var_name, channel, token


def send_to_slack(message):
    options = SLACK_OPTIONS
    options['text'] = message
    r = requests.get("https://slack.com/api/chat.postMessage", params=options,
                     timeout=10.0)
    r.raise_for_status()
    r.close()


SOCKETFILE, LS_VAR_NAME, CHANNEL, TOKEN = parse_config("settings.yaml",
                                                       "settings_slackbot.yaml")

SLACK_OPTIONS = {
    "as_user": True,
    "channel": CHANNEL,
    "token": TOKEN,
}

interactive_bool = LiquidSoapBoolean(SOCKETFILE, LS_VAR_NAME)

outputs = []


def process_message(data):
    global outputs
    to_output = []
    if data['text'].startswith('.nattmusikk'):
        if data['text'].strip() in ('.nattmusikk', '.nattmusikk hjelp',
                                    '.nattmusikk help'):
            to_output.append("\n".join([
                "`.nattmusikk [hjelp|status|på|av]`",
                ".nattmusikk kan brukes for å slå av eller på nattmusikk-hele-"
                "døgnet. Når påslått, vil stille-på-lufta ignoreres, og "
                "nattmusikk vil brukes i stedet for tekniske problemer-jingelen"
                ".",
                "Bruk `.nattmusikk status` for å se om nattmusikk-hele-døgnet "
                "er aktivert eller ikke.",
                "Bruk `.nattmusikk på` for å skru på nattmusikk-hele-døgnet.",
                "Bruk `.nattmusikk av` for å skru av nattmusikk-hele-døgnet.",
            ]))
        else:
            command = data['text'].strip().split(' ')[1]
            with interactive_bool:
                if command in ('på', 'on', 'true'):
                    interactive_bool.value = True
                    to_output.append("Nattmusikk-hele-døgnet er skrudd *PÅ*. \nDere vil *_ikke_*"
                              " lenger få advarsel når det er stille på lufta "
                              "(annet enn når nattmusikken er stille).\n"
                              "Skriv `.nattmusikk av` når det er vanlig drift igjen.")
                elif command in ('av', 'off', 'false'):
                    interactive_bool.value = False
                    to_output.append("Nattmusikk-hele-døgnet er skrudd *AV*.\n"
                              "Normal drift gjenopptatt.")
                elif command in ('status', 'verdi'):
                    interactive_bool.force_update()
                    if interactive_bool.value:
                        to_output.append("Nattmusikk-hele-døgnet er *PÅSLÅTT*.\nDere "
                                       "vil *IKKE* få beskjed hvis det blir stille på lufta.")
                    else:
                        to_output.append("Nattmusikk-hele-døgnet er slått *av*.")
                else:
                    to_output.append("Kjente ikke igjen '%s', skriv `.nattmusikk "
                                   "hjelp` for bruksanvisning." % command)
    for text in to_output:
        send_to_slack(text)
