#!/usr/bin/env python

import boto3
import sys
import argparse



from awsiamreport import AccountReport, OrgAccountsReport, ReportEntry
from awsiamreport.output import ReportEmail
# import awsiamreport

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--blacklisted', '-b', nargs='+', default=[],
                        help='blacklisted accounts are getting ignored')
    parser.add_argument('--roleName', '-r', nargs='+',
                        default="OrganizationAccountAccessRole",
                        help='role name to use for assume')

    parser.add_argument('--smtp-server', nargs='?', default="localhost",
                        help='the smtp server to use')
    parser.add_argument('--smtp-port', nargs='?', default=25, type=int, help='smtp port')
    parser.add_argument('--smtp-ssl', default=False, action='store_true', help='use ssl')
    parser.add_argument('--smtp-user', nargs='?', default="", help='smtp user')
    parser.add_argument('--smtp-password', nargs='?', default="",
                        help='smtp users password')
    parser.add_argument('--smtp-to', nargs='+', default="aws@example.com",
                        help='email address(es) receiving the report')
    parser.add_argument('--smtp-from', nargs='?', default="cron@example.com",
                        help='email address used as from')

    args = parser.parse_args(sys.argv[1:])

    sess = boto3.session.Session()

    orgacc = OrgAccountsReport(sess, BlackListedAccountID=args.blacklisted)
    reports = orgacc.getAllAccountReports()

    for r in reports:
        sys.stderr.write("found account %s (%s) report entries %d\n" % (r.name,
                                                                        r.id,
                                                                        len(r.report)))

    output = ReportEmail(reports, 'templates/report.html', server=args.smtp_server,
                         port=args.smtp_port, ssl=args.smtp_ssl, user=args.smtp_user,
                         password=args.smtp_password, to=args.smtp_to,
                         sender=args.smtp_from)
    output.generate()


if __name__ == "__main__":
    main()
