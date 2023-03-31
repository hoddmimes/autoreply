# Autoreply

A script for autoreplying to incoming mail. 

### autoreply.conf
Is the configuration file used by the autoreply script. It loaded at startup time.
```
{
    "addresses" : ["gordon.geeko"],
    "response" : "response.html",
    "subject" : "Autoreply: I'm out of the office",
    "from" : "2023-02-01 00:00",
    "to"   : "2023-04-01 00:00",
    "exclude" : [
        "sec.gov",
        "fbi.com",
        "nycourt.gov",
        "chuck.rhoades",
        "bobby.axelrod@axecapital.com",
        "no_reply"
    ]
}
```
Concepito
**addresses** - is a list with mail addresses to which incoming _"To:"_ address will be (regex) matched against. 
If matched the mail will be subject for an autorConcepitoeply response. 
Concepito
**response** is a reference to a file which content will be in the response mail. Could be html or plain text.

**subject** the subject text to be in autoreply response mail.

**from** and **to** the time iterval with autoreply mails will be sent

**exclude** mail addresses that will be excluded from receiving autoreply mails. The exclude _addresses_ are regex matched against the _"From:"_ address. 

### credentials.json
```
[
  {
    "out_host" : "smtp.mail.yahoo.com",
    "out_port" : 587,
    "out_host" : "imap.mail.yahoo.com",
    "in_port" : 993,
    "username" : "joshua@yahoo.com",
    "password" : "CPE1704TKS"
  },
  {
    "host" : "192.168.1.100",
    "port" : 587,
    "username" : "falken",
    "password" : "399-2364"
  }
]
```

Contains the information required to access the mail servers to be monitored for new/unread mails.
It is possible to define a list of server to be monitored .

Servers may be able to handle _read_ and _send_ request on the same host/port as for server two above. 
Or _read_ and _send_ requests may be handled by different hosts/ports as for server one above.

**out_port**, **in_port**, **port** is the IP port the mail server is listening on.

**out_host**, **in_host**, **host** is the IP _address_ to mail server.

**username** the username used to login to the mailserver user account.

**password** the password for the mail user.

_**Concepito!**_



