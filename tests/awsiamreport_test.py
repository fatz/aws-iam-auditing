from .context import awsiamreport

import unittest


class AWSIAMReportTestSuite(unittest.TestCase):
    """Advanced test cases."""

    def test_thoughts(self):
        report = {
            "user": "test",
            "arn": "arn:aws:iam::123456789123:user/test",
            "user_creation_time": "2017-06-09T04:07:32+00:00",
            "password_enabled": "false",
            "password_last_used": "N/A",
            "password_last_changed": "N/A",
            "password_next_rotation": "N/A",
            "mfa_active": "false",
            "access_key_1_active": "true",
            "access_key_1_last_rotated": "2017-06-09T04:07:33+00:00",
            "access_key_1_last_used_date": "2018-03-27T19:00:00+00:00",
            "access_key_1_last_used_region": "us-west-2",
            "access_key_1_last_used_service": "s3",
            "access_key_2_active": "false",
            "access_key_2_last_rotated": "N/A",
            "access_key_2_last_used_date": "N/A",
            "access_key_2_last_used_region": "N/A",
            "access_key_2_last_used_service": "N/A",
            "cert_1_active": "false",
            "cert_1_last_rotated":  "N/A",
            "cert_2_active": "false",
            "cert_2_last_rotated": "N/A"
        }
        entry = awsiamreport.ReportEntry(report)
        self.assertFalse(entry.hasActiveMFA())
        self.assertTrue(entry.accessKeyExpired(maxAgeDays=1))


if __name__ == '__main__':
    unittest.main()
