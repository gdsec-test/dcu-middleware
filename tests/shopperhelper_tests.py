from unittest import TestCase
from unittest.mock import Mock, patch

from dcumiddleware.utilities.shopperhelper import ShopperApiHelper


class TestShopperApiHelper(TestCase):

    @patch('dcumiddleware.utilities.shopperhelper.requests.get')
    def test_valid_get_shopper_id(self, mock_get):
        shopperApiHelper = ShopperApiHelper('', '', '')
        mock_response = Mock(status_code=201)
        mock_response.json.return_value = {
            'shopperId': '123'
        }
        mock_get.return_value = mock_response
        shopperId = shopperApiHelper.get_shopper_id('1')
        self.assertEqual(shopperId, '123')

    @patch('dcumiddleware.utilities.shopperhelper.requests.get')
    def test_invalid_get_shopper_id(self, mock_get):
        shopperApiHelper = ShopperApiHelper('', '', '')
        mock_get.return_value = Mock(status_code=400)
        shopperId = shopperApiHelper.get_shopper_id('1')
        self.assertEqual(shopperId, '')
