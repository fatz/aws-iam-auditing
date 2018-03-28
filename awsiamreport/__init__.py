import boto3
import sys

from datetime import datetime, timezone
from dateutil.parser import parse


class AccountReport():
    def __init__(self, boto3session):
        self.boto3session = boto3session
        self.client = self.boto3session.client('iam')
        self.account_id = self.boto3session.client('sts').get_caller_identity().get('Account')
        self.account_name = self.client.list_account_aliases()['AccountAliases'][0]

        # request report right ahead
        self.client.generate_credential_report()

    @property
    def id(self):
        """get account's ID"""

        return self.account_id

    @property
    def name(self):
        """get account's alias"""
        return self.account_name

    def _getReportCSV(self):
        # try:
        response = self.client.get_credential_report()
        content = response['Content']
        csv = content.decode("utf-8")
        return csv
        # except:
        #     return None

    def csv2dict(self, csv):
        """ Return a hash made out of a csv. Expecting the first line to be header
        >>> csv2dict("foo,bar,baz\n3,2,1")
        [{"foo":"3","bar":"2","baz":"1"}]
        """
        response = []
        lines = csv.split('\n')
        if len(lines) < 2:
            return response
        headers = lines[0].split(',')

        for c in lines[1:]:
            content = c.split(',')
            if len(content) != len(headers):
                msg = "header and content not equal size %d, %d\n" % (
                    len(content), len(headers))
                sys.stderr.write(msg)
                next
            r = {}
            for i, header in enumerate(headers):
                r[header] = content[i]
            response.append(r)
        return response

    def getReportDict(self):
        """retreive the report CSV and form it into dict"""
        csv = self._getReportCSV()
        if csv is None:
            return []
        return self.csv2dict(csv)

    def getReportReportEntries(self):
        """format the report dict into list of `ReportEntry`"""
        entries = []
        for d in self.getReportDict():
            entries.append(ReportEntry(d))

        return entries

    @property
    def report(self):
        return self.getReportReportEntries()


class OrgAccountsReport():
    def __init__(self, boto3session, RoleArn="arn:aws:iam::{accountID}:role/{roleName}",
                 RoleSessionName="IAMAuditing", RoleName="OrganizationAccountAccessRole",
                 BlackListedAccountID=[]):
        self.boto3session = boto3session
        self.RoleArn = RoleArn
        self.RoleSessionName = RoleSessionName
        self.BlackListedAccountID = BlackListedAccountID
        self.RoleName = RoleName

    def getActiveAccounts(self):
        """List all accounts marked as active."""
        accs = self.boto3session.client('organizations').list_accounts()
        accounts = []
        for acc in accs['Accounts']:
            if acc['Status'] == "ACTIVE" and acc['Id'] not in self.BlackListedAccountID:
                accounts.append(acc)
        return accounts

    def getAssumedAccountSession(self, accountID):
        """Assume into an accountID. Returns an `boto3.session`"""
        role = self.RoleArn.format(accountID=accountID, roleName=self.RoleName)
        session = self.RoleSessionName
        try:
            response = self.boto3session.client('sts').assume_role(RoleArn=role,
                                                                   RoleSessionName=session)
        except:
            raise Exception('Accountid %s can not be assumed' % accountID)

        return boto3.Session(
            aws_access_key_id=response['Credentials']['AccessKeyId'],
            aws_secret_access_key=response['Credentials']['SecretAccessKey'],
            aws_session_token=response['Credentials']['SessionToken'])

    def getAccountReport(self, accountID):
        """return `AccountReport` for `accountID`"""
        session = self.getAssumedAccountSession(accountID)
        return AccountReport(session)

    def getRootAccountReport(self):
        """return `AccountReport` for root account"""
        return AccountReport(self.boto3session)

    def getAllAccountReports(self):
        """iterate over all active accounts and return a list of `AccountReport`s"""
        r = []

        rootAccReport = self.getRootAccountReport()
        r.append(rootAccReport)

        for acc in self.getActiveAccounts():
            if acc['Id'] == rootAccReport.id:
                continue
            r.append(self.getAccountReport(acc['Id']))

        return r


class ReportEntry(dict):
    # self.user_creation_time = reportDict['user_creation_time']
    # self.password_enabled = reportDict['password_enabled']
    # self.password_last_used = reportDict['password_last_used']
    # self.password_last_changed = reportDict['password_last_changed']
    # self.password_next_rotation = reportDict['password_next_rotation']
    # self.mfa_active = reportDict['mfa_active']
    # self.access_key_1_active = reportDict['access_key_1_active']
    # self.access_key_1_last_rotated = reportDict['access_key_1_last_rotated']
    # self.access_key_1_last_used_date = reportDict['access_key_1_last_used_date']
    # self.access_key_1_last_used_region = reportDict['access_key_1_last_used_region']
    # self.access_key_1_last_used_service = reportDict['access_key_1_last_used_service']
    # self.access_key_2_active = reportDict['access_key_2_active']
    # self.access_key_2_last_rotated = reportDict['access_key_2_last_rotated']
    # self.access_key_2_last_used_date = reportDict['access_key_2_last_used_date']
    # self.access_key_2_last_used_region = reportDict['access_key_2_last_used_region']
    # self.access_key_2_last_used_service = reportDict['access_key_2_last_used_service']
    # self.cert_1_active = reportDict['cert_1_active']
    # self.cert_1_last_rotated = reportDict['cert_1_last_rotated']
    # self.cert_2_active = reportDict['cert_2_active']
    # self.cert_2_last_rotated = reportDict['cert_2_last_rotated']

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def _age(self, timeEntry):
        if timeEntry not in self:
            return None
        try:
            rotated = parse(self[timeEntry])
            duration = datetime.now(timezone.utc) - rotated

            return duration
        except:
            return None

    def _checkPrefixExpire(self, prefix, maxAgeDays):
        if self['%s_active' % prefix] == "false":
            return False

        timeEntry = '%s_last_rotated' % prefix
        duration = self._age(timeEntry)

        if duration.days >= maxAgeDays:
            return True
        return False

    def _checkPrefixUnused(self, prefix, maxAgeDays):
        timeEntry = '%s_last_used' % prefix
        duration = self._age(timeEntry)

        if duration is None or duration.days >= maxAgeDays:
            return True
        return False

    def getAccessKeyAge(self, num):
        """Returns `timedelta` for access key `num`"""
        prefix = 'access_key_%d' % int(num)
        if self['%s_active' % prefix] == "false":
            return None
        timeEntry = '%s_last_rotated' % prefix

        if self[timeEntry] == "N/A":
            return None
        return self._age(timeEntry)

    def accessKeyInactiveNum(self, num):
        """Returns `True` if the access key `num` is inactive"""
        prefix = 'access_key_%d' % int(num)
        if self['%s_active' % prefix] == "false":
            return True

        return False

    def getAccessKeyLastUsageNum(self, num):
        """Returns `timedelta` from the access key `num`'s last usage'"""
        prefix = 'access_key_%d' % int(num)
        if self.accessKeyInactiveNum(num):
            return None

        timeEntry = '%s_last_used_date' % prefix

        if self[timeEntry] == "N/A":
            return None
        return self._age(timeEntry)

    def checkAccessKeyExpireNum(self, num, maxAgeDays):
        """
        checks if the access key with `num` is older than `maxAgeDays` days
        """
        prefix = "access_key_%d" % int(num)

        return self._checkPrefixExpire(prefix, maxAgeDays)

    def accessKeyExpired(self, maxAgeDays):
        """checks if one of the access keys is older than `maxAgeDays` days"""
        return (self.checkAccessKeyExpireNum(1, maxAgeDays) or
                self.checkAccessKeyExpireNum(2, maxAgeDays))

    def checkCertKeyExpireNum(self, num, maxAgeDays):
        """
        checks if the certificate keys with `num` is older than
        `maxAgeDays` days
        """
        prefix = "cert_%d_" % int(num)

        return self._checkPrefixExpire(prefix, maxAgeDays)

    def certKeyExpired(self, maxAgeDays):
        """
        checks if one of the certificate keys is older than `maxAgeDays` days
        """
        return (self.checkCertKeyExpireNum(1, maxAgeDays) or
                self.checkCertKeyExpireNum(2, maxAgeDays))

    def hasActiveMFA(self):
        """returns `True` if mfa is active"""
        if self['mfa_active'] == 'true':
            return True
        return False

    def hasPasswordEnabled(self):
        """returns `True` if password is enabled"""
        if self['password_enabled'] == 'true':
            return True
        return False

    def getPasswordLastUsage(self):
        """returns `timedelta` for the last password usage"""
        if self['password_enabled'] == "false":
            return None

        if self['password_last_used'] == "no_information":
            return None
        return self._age('password_last_used')

    def getapiLastUsed(self):
        """returns `timedelta` for the last access key usage"""
        api1 = self.getAccessKeyLastUsageNum(1)
        api2 = self.getAccessKeyLastUsageNum(2)

        if api1 is None:
            return api2

        return api1 if api2 is None or api1 < api2 else api2

    def apiUnusedNum(self, num, days):
        """checks if the api access key `num` is unused for `days` days"""
        prefix = "access_key_%d_" % int(num)

        return self._checkPrefixUnused(prefix, days)

    def apiUnused(self, maxAgeDays):
        """checks if both of the api access keys is unused for `days` days"""
        return self.apiUnusedNum(1, maxAgeDays) and self.apiUnusedNum(2, maxAgeDays)

    def passwordUnused(self, days):
        """checks if the password access is unused for `days` days"""
        return self._checkPrefixUnused("password", days)

    def isUnused(self, maxAgeDays):
        """checks if the user is unused for `days` days"""
        return self.apiUnused(maxAgeDays) and self.passwordUnused(maxAgeDays)

    def lastUsed(self):
        """returns the `timedelta` to last usage of this user"""
        api = self.getapiLastUsed()
        pw = self.getPasswordLastUsage()

        if api is None:
            return pw

        return api if pw is None or api < pw else pw
