#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb as mdb
import sys

from pprint import pprint
import smtplib


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def py_mail(SUBJECT, BODY, TO, FROM):
    """With this function we send out our html email"""
 
    # Create message container - the correct MIME type is multipart/alternative here!
    MESSAGE = MIMEMultipart('alternative')
    MESSAGE['subject'] = SUBJECT
    MESSAGE['To'] = TO
    MESSAGE['From'] = FROM
#    MESSAGE.preamble = """
#Your mail reader does not support the report format.
#Please visit us <a href="http://www.mysite.com">online</a>!"""
 
    # Record the MIME type text/html.
    HTML_BODY = MIMEText(BODY, 'html')
 
    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    MESSAGE.attach(HTML_BODY)
 
    # The actual sending of the e-mail
    server = smtplib.SMTP('smtp.gmail.com:587')
 
    # Print debugging output when testing
    if __name__ == "__main__":
        server.set_debuglevel(1)
 
    # Credentials (if needed) for sending the mail
    username = "peeyush.raj@vvdntech.com"
    password = "J.Street@123"
 
    server.starttls()
    server.login(username,password)
    server.sendmail(FROM, [TO], MESSAGE.as_string())
    server.quit()


try:
    con = mdb.connect('localhost', 'root', 'zaqwsxCDE', 'meru_cnms');

    cur = con.cursor()
    query = """
    SELECT alarm_cmac, alarm_type, alarm_severity, alarm_ts, alarm_content, 
    user_name, user_email, 
    controller_hostname, controller_name, controller_ip
    FROM meru_alarm 
    JOIN (meru_user, meru_controller_controllergroup, meru_controller)
    ON (
        (meru_alarm.alarm_cmac = meru_controller.controller_mac)
        AND
        (meru_controller.controller_id = meru_controller_controllergroup.ccg_cid_fk)
        AND
        (meru_controller.controller_createdby_fk = meru_user.user_id)
        )
    WHERE (
        (meru_alarm.alarm_status = 0)
        AND
        (meru_alarm.is_read = 0)
        ) ORDER BY `meru_user`.`user_email` ASC
    """
    cur.execute(query)

    ver = cur.fetchall()

    alarms_mails = {}


    for v in ver:
        if v[6] in alarms_mails:
            alarms_mails[v[6]].append([v[0], v[1], v[2], v[4], v[3], v[7], v[8], v[9], v[5]])
        else:
            alarms_mails[v[6]] = []
            alarms_mails[v[6]].append([v[0], v[1], v[2], v[4], v[3], v[7], v[8], v[9], v[5]])

#    pprint(alarms_mails)

    for to_user in alarms_mails:
        TO = to_user
        email_content = """
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <title>html title</title>
  <style type="text/css" media="screen">
    table{
        background-color: #fff;
        empty-cells:hide;
    }
    td {
	border: #111 solid 1px;
	}
    td.cell{
        background-color: white;
    }
  </style>
</head>
<body>
  <table style="border: blue 1px solid;">
    <tr>
	<td class="cell">Alarm</td>
	<td>Severity</td>
	<td>Content</td>
	<td>Controller Mac</td>
	<td>Site Name</td>
	<td class="cell">TimeStamp</td>
    </tr>
    <tr>
	<td>&nbsp;</td>
	<td>&nbsp;</td>
	<td>&nbsp;</td>
	<td>&nbsp;</td>
	<td>&nbsp;</td>
        <td>&nbsp;</td>
    </tr>
"""
	
        alarms_are = alarms_mails[TO]
        update_this = ""
        for alarm in alarms_are :
            email_content += "<tr>"
            email_content += "<td>"
            email_content += alarm[1]
            email_content += "</td>"
            email_content += "<td>"
            email_content += alarm[2]
            email_content += "</td>"
            email_content += "<td>"
            email_content += alarm[3]
            email_content += "</td>"
            email_content += "<td>"
            email_content += alarm[0]
            email_content += "</td>"
            email_content += "<td>"
            email_content += alarm[5]
            email_content += "</td>"
            email_content += "<td>"
            email_content += alarm[4]
            email_content += "</td>"
            email_content += "</tr>"
            update_this = alarm[4]

        try:
            email_content += """
                </table>
            </body>
            """
            sql = ""
            sql = """
	        UPDATE meru_alarm SET alarm_status = 1 WHERE alarm_ts = %s
            """ % update_this
            #print sql
            cur = con.cursor()
            cur.execute(sql)
            con.commit()
            #TO = 'receiver@email.com'
            FROM ='admin@mcloud.com'
 
            py_mail("Alarm Notificaiton Meru Cloud", email_content, TO, FROM)

        except Exception as e:
            print str(e)
            pass

    
except mdb.Error, e:
  
    print "Error %d: %s" % (e.args[0],e.args[1])
    sys.exit(1)
    
finally:    
        
    if con:    
        con.close()
