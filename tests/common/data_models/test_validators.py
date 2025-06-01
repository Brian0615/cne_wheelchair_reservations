import unittest
from unittest.mock import patch, MagicMock

from pydantic import BaseModel

from common.data_models.validators import check_country_code, check_province_state


# pylint: disable=too-few-public-methods
class MockModel(BaseModel):
    """Mock model for testing validators."""
    country: str
    province: str


class TestValidators(unittest.TestCase):
    """Test the validators module."""

    def test_check_country_code_valid(self):
        """Test check_country_code with valid country names."""
        # Test with common country names
        self.assertEqual(check_country_code("Canada"), "CAN")
        self.assertEqual(check_country_code("United States"), "USA")
        self.assertEqual(check_country_code("United Kingdom"), "GBR")
        self.assertEqual(check_country_code("Mexico"), "MEX")

        # Test with case insensitivity
        self.assertEqual(check_country_code("canada"), "CAN")
        self.assertEqual(check_country_code("CANADA"), "CAN")

        # Test with alternative names
        self.assertEqual(check_country_code("United States of America"), "USA")

        # Test with acronyms
        self.assertEqual(check_country_code("US"), "USA")
        self.assertEqual(check_country_code("USA"), "USA")
        self.assertEqual(check_country_code("UK"), "GBR")
        self.assertEqual(check_country_code("HK"), "HKG")

    def test_check_country_code_invalid(self):
        """Test check_country_code with invalid country names."""
        # Test with non-existent country
        with self.assertRaises(ValueError):
            check_country_code("NonExistentCountry")

        # Test with empty string
        with self.assertRaises(ValueError):
            check_country_code("")

        # Test with None
        with self.assertRaises(ValueError):
            check_country_code(None)

    @patch('pycountry.countries.lookup')
    def test_check_country_code_with_mock(self, mock_lookup):
        """Test check_country_code with mocked pycountry lookup."""
        # Setup mock
        mock_country = MagicMock()
        mock_country.alpha_3 = "XYZ"
        mock_lookup.return_value = mock_country

        # Test with mock
        self.assertEqual(check_country_code("TestCountry"), "XYZ")
        mock_lookup.assert_called_once_with("TestCountry")

        # Test with lookup error
        mock_lookup.side_effect = LookupError("Country not found")
        with self.assertRaises(ValueError):
            check_country_code("ErrorCountry")

    def test_check_province_state_non_ca_us(self):
        """Test check_province_state with non-Canada/US countries."""
        # Test with non-Canada/US country
        model = MockModel(country="GBR", province="London")
        result = check_province_state(model)
        # Function should return un-changed model for non-Canada/US countries
        self.assertEqual(result, model)

    @patch('pycountry.subdivisions.get')
    def test_check_province_state_valid_canada(self, mock_get):
        """Test check_province_state with valid Canadian provinces."""
        # Setup mock subdivisions for Canada
        mock_on = MagicMock()
        mock_on.code = "CA-ON"
        mock_on.name = "Ontario"

        mock_bc = MagicMock()
        mock_bc.code = "CA-BC"
        mock_bc.name = "British Columbia"

        mock_get.return_value = [mock_on, mock_bc]

        # Test with province code
        model = MockModel(country="CAN", province="ON")
        result = check_province_state(model)
        self.assertEqual(result.province, "ON")
        mock_get.assert_called_with(country_code="CA")

        # Test with province code
        model = MockModel(country="CAN", province="BC")
        result = check_province_state(model)
        self.assertEqual(result.province, "BC")
        mock_get.assert_called_with(country_code="CA")

        # Test with province name
        model = MockModel(country="CAN", province="Ontario")
        result = check_province_state(model)
        self.assertEqual(result.province, "ON")

        # Test with case insensitivity
        model = MockModel(country="CAN", province="ontario")
        result = check_province_state(model)
        self.assertEqual(result.province, "ON")

    @patch('pycountry.subdivisions.get')
    def test_check_province_state_valid_us(self, mock_get):
        """Test check_province_state with valid US states."""
        # Setup mock subdivisions for US
        mock_ca = MagicMock()
        mock_ca.code = "US-CA"
        mock_ca.name = "California"

        mock_ny = MagicMock()
        mock_ny.code = "US-NY"
        mock_ny.name = "New York"

        mock_get.return_value = [mock_ca, mock_ny]

        # Test with state code
        model = MockModel(country="USA", province="CA")
        result = check_province_state(model)
        self.assertEqual(result.province, "CA")
        mock_get.assert_called_with(country_code="US")

        # Test with state name
        model = MockModel(country="USA", province="California")
        result = check_province_state(model)
        self.assertEqual(result.province, "CA")

        # Test with case insensitivity
        model = MockModel(country="USA", province="california")
        result = check_province_state(model)
        self.assertEqual(result.province, "CA")

    @patch('pycountry.subdivisions.get')
    def test_check_province_state_invalid(self, mock_get):
        """Test check_province_state with invalid provinces/states."""
        # Setup mock subdivisions
        mock_on = MagicMock()
        mock_on.code = "CA-ON"
        mock_on.name = "Ontario"

        mock_get.return_value = [mock_on]

        # Test with invalid province
        model = MockModel(country="CAN", province="InvalidProvince")
        with self.assertRaises(ValueError):
            check_province_state(model)

        # Test with empty province
        model = MockModel(country="CAN", province="")
        with self.assertRaises(ValueError):
            check_province_state(model)

    @patch('pycountry.subdivisions.get')
    def test_check_province_state_no_subdivisions(self, mock_get):
        """Test check_province_state when no subdivisions are found."""
        # Setup mock to return empty list
        mock_get.return_value = []

        # Test with country that has no subdivisions
        model = MockModel(country="CAN", province="ON")
        with self.assertRaises(ValueError):
            check_province_state(model)
