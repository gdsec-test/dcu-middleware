from unittest.case import TestCase
from dcumiddleware.utilities.branddetectionhelper import BrandDetectionHelper
from mock import patch, Mock


class TestBrandDetector(TestCase):
    def setUp(self):
        self.branddetectionservice = BrandDetectionHelper('', '', '')

    @patch('dcumiddleware.utilities.branddetectionhelper.requests.get')
    @patch.object(BrandDetectionHelper, '_get_jwt')
    def test_get_plid_info_success(self, mock_get_jwt, mock_get):
        mock_get_jwt.return_value = ''
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {
            'abuse_report_email': {
                'email': 'abuse@sample.de'
            },
            'brand': 'EMEA',
            'hosting_abuse_email': [
                'abuse-input@sample.com'
            ]
        }
        mock_get.return_value = mock_response
        brand_info = self.branddetectionservice.get_plid_info(plid='12')
        self.assertEqual(brand_info['brand'], 'EMEA')
        self.assertEqual(brand_info['abuse_report_email']['email'], 'abuse@sample.de')
