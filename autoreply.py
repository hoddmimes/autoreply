import re
import os
import imaplib
import email
import json
import time

from email.header import decode_header
from datetime import datetime
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

mail_regex = re.compile(r"([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\"([]!#-[^-~ \t]|(\\[\t -~]))+\")@([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\[[\t -Z^-~]*])")

credentials = None
config = None
state = None


def main():
    load_configuration()
    load_credentials()
    load_state()

    for server in credentials:
        host,port = get_host_port("IN", server)
        imap_server = connect_to_server( host, port, server["username"], server["password"], "INBOX")
        msgs = get_unread_mails( imap_server)
        check_unread_mails( server, msgs )



def get_host_port( direction: str, server : dict) -> tuple[str, int]:
    if direction == 'IN':
        if server["in_port"]:
            port = server["in_port"]
        else:
            port = server["port"]

        if server["in_host"]:
            host = server["in_host"]
        else:
            host = server["host"]

    if direction == 'OUT':
        if server["out_port"]:
            port = server["out_port"]
        else:
            port = server["port"]

        if server["out_host"]:
            host = server["out_host"]
        else:
            host = server["host"]
    return host, port

    if 'in_port' in server:
        return server["in_port"]
    return server["port"]


def get_out_port( server : dict) -> int:
    if 'out_port' in server:
        return server["out_port"]
    return server["port"]




def load_credentials():
    try:
        f = open('credentials.json')
        global credentials
        credentials = json.load(f)
        f.close()
    except Exception as e:
        print( "Failed to load credentials.json, reason: " + str(e))
        exit(0)

def load_configuration():
    try:
        f = open('autoreply.conf')
        global config
        config = json.load(f)
        f.close()
    except Exception as e:
        print( "Failed to load autoreply.conf, reason: " + str(e))
        exit(0)

def load_state():
    if os.path.isfile("autoreply_state.json"):
        try:
            f = open('autoreply_state.json')
            global state
            state = json.load(f)
            f.close()
        except Exception as e:
            print("Failed to load sautoreply_state.json, reason: " + str(e))
            exit(0)
    else:
        state = []





def byteStrEncode( item : tuple) -> str:
    if isinstance(item[0], str):
        return item[0]
    if isinstance(item[0], bytes) and item[1]:
            return item[0].decode( item[1])

    return item[0].decode("utf-8")


def decompile_address( address_object : object) -> []:
    adrList = []

    if address_object == None:
        return adrList

    address_list =  decode_header( address_object )

    for adrtuple in address_list:
        list =  byteStrEncode(adrtuple);

        list = list.split(",")
        for adr in list:
            m = re.search(mail_regex, adr)
            if m:
                adrList.append( m.group(0) );
    return adrList

def decompile_subject( subject_header ) -> str:
    if subject_header == None:
        return ""

    subject = decode_header( subject_header )

    subject = byteStrEncode( subject[0] )
    return subject;





def check_unread_mails( server: dict, msgs: [] ):
    for msg_data in msgs:
        for msg_parts in msg_data:
            if isinstance(msg_parts, tuple):
                msg = email.message_from_bytes(msg_parts[1])
                # decode subject sender
                msg_subject = decompile_subject(msg["Subject"])
                msg_from = decompile_address( msg.get("From"))
                msg_to = decompile_address( msg.get("To"))
                print("From: " + str(msg_from))
                check_mail( server, msg_from, msg_to )


def check_mail(server, msg_from: [], msg_to: []):
    to_addr = mail_to_me( msg_to )
    if to_addr:
        if within_out_of_office_time():
            from_addr = msg_from[0]
            if not from_notified( to_addr, from_addr ):
                if not exclude_address( from_addr ):
                    send_autoreply( server, from_addr, to_addr)
                    add_notification(to_addr, from_addr)


def load_message_file( filename: str ) -> str:
    try:
        f = open(filename)
        message = f.read()
        f.close()
        return message
    except Exception as e:
        print( "Failed to read " + filename + ", reason: " + str(e))
        exit(0)

def send_autoreply( server: dict, to_addr: str, from_addr: str):
    is_html = str(config["response"]).endswith("html")
    response = load_message_file(config["response"])
    host,port = get_host_port("OUT", server)


    context = context = ssl._create_unverified_context()
    with smtplib.SMTP(host, port) as stmp_server:
        stmp_server.ehlo()  # Can be omitted
        stmp_server.starttls(context=context)
        stmp_server.ehlo()  # Can be omitted
        stmp_server.login(server["username"] , server["password"])

        email_message = MIMEMultipart()
        email_message['From'] = from_addr
        email_message['To'] = to_addr
        email_message['Subject'] = config["subject"]

        if is_html:
            email_message.attach(MIMEText(response, "html"))
        else:
            email_message.attach(MIMEText(response, "plain"))

        email_string = email_message.as_string()

        stmp_server.sendmail( from_addr, to_addr, email_string)

def exclude_address( from_addr : str ) -> bool:
        for exclude_pattern in config["exclude"]:
            if re.search( exclude_pattern, from_addr, re.IGNORECASE ):
                return True
        return False

def add_notification( to_addr: str, from_addr: str ):
    now = datetime.now()
    entry = dict()
    entry["to"] = to_addr
    entry["from"] = from_addr
    entry["time"] = now.strftime('%Y-%m-%d %H:%M:%S')
    global state
    state.append( entry )

    json_state = json.dumps(state)
    with open("autoreply_state.json", "w") as outfile:
        outfile.write(json_state)
        outfile.flush()
        outfile.close()


def from_notified( to_addr: str, from_addr : str ) -> bool:
    for notify_item in state:
        if to_addr == notify_item["to"] and from_addr == notify_item["from"]:
            return within_notify_interval( notify_item["time"])
    return False


def delta_time_to_hours( td ) -> int:
    hh = (td.days * 24) + td.seconds / 3600
    return int(hh)


def within_notify_interval( notify_time_str : str ) -> bool:
    now = datetime.now()
    notify_time = datetime.strptime(notify_time_str, '%Y-%m-%d %H:%M:%S')

    delta_time = now - notify_time
    hh = delta_time_to_hours( delta_time )
    return hh < 24

def within_out_of_office_time() -> bool:
    start =  datetime.strptime(config["from"], '%Y-%m-%d %H:%M')
    stop = datetime.strptime(config["to"], '%Y-%m-%d %H:%M')
    now = datetime.now()

    return  (now >= start and now <= stop)


def mail_to_me( msg_to: [] ) -> str:
    for addr_pattern in config["addresses"]:
        for addr in msg_to:
            if re.search( addr_pattern, addr, re.IGNORECASE  ):
                return addr
    return None


def connect_to_server( host: str, port: int, username: str, password:str, mailbox: str ):
    try:
        imap = imaplib.IMAP4_SSL(host)
        imap.login(username, password)
        status, messages = imap.select( mailbox )
        print("Connected to " + host + " on port " + str(port)  + " as " + username )
        return imap;
    except imaplib.IMAP4.error as e:
        print("Failed to connect to  " + host  + " on port " + str(port) + " as " + username + " reason: " + e.args[0].decode('utf-8') )
        exit(0)


def get_latest_mails( imap, count : int ) -> []:
    msgs = []
    status, messages = imap.select("INBOX")
    msg_count = int(messages[0])
    for id in range( count ):
        status, msg = imap.fetch(str( msg_count - id ), "(RFC822)")
        msgs.append( msg )
    return msgs

def get_unread_mails( imap ) -> []:
    # Search for all unread messages
    status, data = imap.search(None, 'UnSeen')
    id_list = data[0].decode()
    mail_ids = id_list.split()
    msgs = []
    for id in mail_ids:
        status, msg = imap.fetch(id, "(BODY.PEEK[HEADER])")
        msgs.append( msg )
    return msgs;



if __name__ == '__main__':
    main()