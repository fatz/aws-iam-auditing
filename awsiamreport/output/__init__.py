import os
import jinja2
import sys

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib


class ReportOutput():
    def __init__(self, reports, templatefile):
        self.reports = reports
        self.templatefile = templatefile

    def render(self, **context):
        path, filename = os.path.split(self.templatefile)
        return jinja2.Environment(
            extensions=['jinja2.ext.loopcontrols'],
            loader=jinja2.FileSystemLoader(path or './')
        ).get_template(filename).render(context)

    def generate(self):
        print(self.render(accounts=self.reports))


class ReportEmail(ReportOutput):
    def __init__(self, reports, templatefile, server='localhost', port=25,
                 ssl=True, user=None, password=None, sender='cron@example.com',
                 to=['report@example.com'], subject='AWS IAM Users Report'):
        super().__init__(reports, templatefile)
        self.server = server
        self.port = port
        self.ssl = ssl
        self.user = user
        self.password = password
        self.sender = sender
        self.to = to
        self.subject = subject

    def _smtp_client(self):
        if self.ssl:
            client = smtplib.SMTP_SSL('{}:{}'.format(self.server, self.port))
        else:
            client = smtplib.SMTP('{}:{}'.format(self.server, self.port))

        if self.user and self.password:
            client.login(self.user, self.password)

        return client

    def sendMail(self, msg):
        client = self._smtp_client()
        client.sendmail(self.sender, self.to, msg)
        sys.stderr.write("Sending mail to {}".format(self.to))

    def renderPlain(self):
        return "This tool does not support plain text"

    def createMail(self):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = self.subject
        msg['From'] = self.sender
        msg['To'] = ','.join(self.to)

        plain = self.renderPlain()
        html = self.render(accounts=self.reports)

        msg.attach(MIMEText(plain))
        msg.attach(MIMEText(html, 'html'))

        return msg

    def generate(self):
        msg = self.createMail()
        self.sendMail(msg.as_string())
