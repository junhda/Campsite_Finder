import smtplib
import os.path
from os.path import basename
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# code is adapted from examples found here:
# https://realpython.com/python-send-email/


def send_mail(receiver_email, body, files=[]):
    if not isinstance(receiver_email, str):
        raise TypeError("receiver_email parameter expects input of type string")
    if not isinstance(body, str):
        raise TypeError("body parameter expects input of type string")
    if not isinstance(files, list):
        raise TypeError("files parameter expects input of type list")
    # credentials for sender smtp email
    smtp_server = 'smtp.mail.com'
    smtp_username = 'neu_cs5001@technologist.com'
    smtp_password = 'S66bjy$ddwoQOwx7C'
    smtp_port = 587

    # define header of email
    msg = MIMEMultipart()
    msg['Subject'] = 'Camping Done Right!'
    msg['From'] = smtp_username
    msg['To'] = receiver_email

    msgText = MIMEText('<b>%s</b>' % (body), 'html')
    msg.attach(msgText)

    # attach file(s) to the email
    if len(files) > 0:
        for file in files:
            if not isinstance(file, str):
                raise TypeError("files parameter entries expect input of type string")
            if os.path.exists(file):
                with open(file, 'r') as f:
                    part = MIMEApplication(f.read(), Name=basename(file))

                part['Content-Disposition'] = 'attachment; filename="{}"'.format(
                    basename(file))
                msg.attach(part)
                print(file, "attached successfully.")
            else:
                print(file, "does not exist.")

    try:
        # sending the email
        with smtplib.SMTP(smtp_server, smtp_port) as smtpObj:
            # intoduce program to smtp server
            smtpObj.ehlo()
            # enable Transport Layer Security (TLS) to ensure email is sent
            # safely
            smtpObj.starttls()
            smtpObj.login(smtp_username, smtp_password)
            smtpObj.sendmail(smtp_username, receiver_email, msg.as_string())
            print("Email successfully sent to", receiver_email)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    send_mail(
        "danjun95@gmail.com",
        "You've got some camping to do!",
        ["camp_sites.json"])
