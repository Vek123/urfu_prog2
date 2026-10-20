from math import inf, nan
from unittest import TestCase
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory

from apps.feedback.bonuses import AnnualBonusServiceImpl, QuarterlyBonusServiceImpl
from apps.feedback.enums import Positions
from apps.feedback.application import FeedbackApplicationService
from apps.feedback.exceptions import DownstreamServiceException
from apps.feedback.views import FeedbackView


class AnnualBonusTests(TestCase):
    def setUp(self):
        self.service = AnnualBonusServiceImpl()

    def test_example_hr(self):
        result = self.service.calculate(Positions.HR, 100000, 2, 243, 2023)
        self.assertAlmostEqual(result, 360493.8271604938, places=7)

    def test_leap_year_and_century_rules(self):
        for year, expected in ((2023, 240000), (2024, 240657.53424657535),
                               (2000, 240657.53424657535), (2100, 240000)):
            with self.subTest(year=year):
                self.assertAlmostEqual(self.service.calculate(
                    Positions.HR, 100000, 2, 365, year), expected, places=7)

    def test_all_position_coefficients(self):
        expected = {Positions.DEV: 440000, Positions.HR: 240000,
                    Positions.TL: 520000, Positions.PO: 600000,
                    Positions.TPM: 700000, Positions.CTO: 800000}
        for position, amount in expected.items():
            with self.subTest(position=position):
                self.assertAlmostEqual(self.service.calculate(
                    position, 100000, 2, 365, 2023), amount, places=7)

    def test_zero_salary_or_multiplier(self):
        self.assertEqual(self.service.calculate(Positions.DEV, 0, 2, 243, 2023), 0)
        self.assertEqual(self.service.calculate(Positions.DEV, 100000, 0, 243, 2023), 0)

    def test_invalid_work_days(self):
        for days in (0, -1, 366, True, 1.5):
            with self.subTest(days=days), self.assertRaises(ValueError):
                self.service.calculate(Positions.HR, 100000, 2, days, 2023)

    def test_366_work_days_allowed_in_leap_year(self):
        self.assertEqual(self.service.calculate(
            Positions.HR, 100000, 2, 366, 2024), 240000)

    def test_invalid_money_values(self):
        for value in (-1, inf, nan, True, '100000'):
            with self.subTest(salary=value), self.assertRaises(ValueError):
                self.service.calculate(Positions.HR, value, 2, 243, 2023)
            with self.subTest(bonus=value), self.assertRaises(ValueError):
                self.service.calculate(Positions.HR, 100000, value, 243, 2023)

    def test_invalid_position_or_year(self):
        with self.assertRaises(ValueError):
            self.service.calculate('HR', 100000, 2, 243, 2023)
        for year in (0, 10000, 2024.5, True):
            with self.subTest(year=year), self.assertRaises(ValueError):
                self.service.calculate(Positions.HR, 100000, 2, 243, year)

    def test_overflow_is_rejected(self):
        with self.assertRaises(ValueError):
            self.service.calculate(Positions.CTO, 1e308, 10, 1, 2023)

    def test_large_integer_overflow_is_rejected(self):
        with self.assertRaises(ValueError):
            self.service.calculate(Positions.CTO, 10**308, 10, 1, 2023)

    @patch('apps.feedback.bonuses.DateTimeUtil.current_year', return_value=2024)
    def test_current_year_used_when_omitted(self, clock):
        self.assertAlmostEqual(self.service.calculate(
            Positions.HR, 100000, 2, 365), 240657.53424657535, places=7)


class QuarterlyBonusTests(TestCase):
    def setUp(self):
        self.service = QuarterlyBonusServiceImpl()

    def test_quarterly_bonus_for_each_manager(self):
        for position, expected in ((Positions.TL, 130000), (Positions.PO, 150000),
                                   (Positions.TPM, 175000), (Positions.CTO, 200000)):
            with self.subTest(position=position):
                self.assertAlmostEqual(self.service.calculate(
                    position, 100000, 2, 365, 2023), expected, places=7)

    def test_non_managers_are_rejected(self):
        for position in (Positions.DEV, Positions.HR):
            with self.subTest(position=position), self.assertRaisesRegex(
                    ValueError, 'руководител'):
                self.service.calculate(position, 100000, 2, 243, 2023)

    def test_quarterly_bonus_uses_leap_year(self):
        self.assertAlmostEqual(self.service.calculate(
            Positions.TL, 100000, 2, 366, 2024), 130000, places=7)

    def test_invalid_values_are_rejected(self):
        with self.assertRaises(ValueError):
            self.service.calculate(Positions.TL, 100000, 2, 0, 2023)
        with self.assertRaises(ValueError):
            self.service.calculate('TL', 100000, 2, 243, 2023)


@override_settings(FEEDBACK_FORWARD_REQUESTS=False)
class FeedbackApiTests(SimpleTestCase):
    def setUp(self):
        self.payload = {
            'uid': 'bonus-unit', 'operationUid': 'operation-001',
            'systemTime': '2023-01-01T00:00:00.000Z', 'communicationId': 1000,
            'position': 'TL', 'salary': 100000, 'bonus': 2,
            'workDays': 365, 'year': 2023,
        }

    def post(self, payload):
        request = APIRequestFactory().post('/feedback', payload, format='json')
        with self.assertLogs('apps.feedback', level='INFO'):
            return FeedbackView.as_view()(request)

    def test_manager_response_has_both_bonuses(self):
        response = self.post(self.payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['annualBonus'], 520000)
        self.assertEqual(response.data['quarterlyBonus'], 130000)

    def test_non_manager_receives_null_quarterly_bonus(self):
        response = self.post({**self.payload, 'position': 'HR'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['annualBonus'], 240000)
        self.assertIsNone(response.data['quarterlyBonus'])

    def test_366_days_rejected_only_in_common_year(self):
        invalid = self.post({**self.payload, 'workDays': 366})
        valid = self.post({**self.payload, 'workDays': 366, 'year': 2024})
        self.assertEqual(invalid.status_code, 400)
        self.assertIn('workDays', invalid.data['errorMessage'])
        self.assertEqual(valid.status_code, 200)
        self.assertEqual(valid.data['annualBonus'], 520000)

    def test_numeric_strings_and_boolean_rejected(self):
        response = self.post({**self.payload, 'salary': '100000',
                              'bonus': True, 'workDays': 0})
        self.assertEqual(response.status_code, 400)
        for field in ('salary', 'bonus', 'workDays'):
            self.assertIn(field, response.data['errorMessage'])
        self.assertIsNone(response.data['annualBonus'])

    def test_missing_bonus_fields_are_reported(self):
        payload = self.payload.copy()
        del payload['position']
        del payload['salary']
        response = self.post(payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn('position', response.data['errorMessage'])
        self.assertIn('salary', response.data['errorMessage'])

    def test_business_error_does_not_return_a_calculated_bonus(self):
        response = self.post({**self.payload, 'uid': '123'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errorCode'], 'UnsupportedCodeException')
        self.assertIsNone(response.data['annualBonus'])
        self.assertIsNone(response.data['quarterlyBonus'])

    def test_validated_bonus_fields_are_forwarded(self):
        forwarder = Mock()
        service = FeedbackApplicationService(forwarder=forwarder)
        with self.assertLogs('apps.feedback', level='INFO'):
            service.handle(self.payload, 12345)
        message, received_at = forwarder.send.call_args.args
        self.assertEqual(message.position, Positions.TL)
        self.assertEqual(message.salary, 100000)
        self.assertEqual(message.year, 2023)
        self.assertEqual(received_at, 12345)
        self.assertEqual(self.payload['position'], 'TL')

    @override_settings(FEEDBACK_FORWARD_REQUESTS=True)
    @patch('apps.feedback.application.ForwardRequestService')
    def test_forwarding_failure_returns_null_bonuses(self, client):
        client.return_value.send.side_effect = DownstreamServiceException()
        response = self.post(self.payload)
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.data['errorCode'], 'DownstreamServiceException')
        self.assertIsNone(response.data['annualBonus'])
        self.assertIsNone(response.data['quarterlyBonus'])
