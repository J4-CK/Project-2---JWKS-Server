import unittest
import requests
import coverage

# Create a coverage object
cov = coverage.Coverage()

class TestJWKS(unittest.TestCase):
    BASE_URL = 'http://localhost:8080'

    def test_auth_endpoint(self):
        response = requests.post(f'{self.BASE_URL}/auth')
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.json())

    def test_jwks_endpoint(self):
        response = requests.get(f'{self.BASE_URL}/.well-known/jwks.json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('keys', response.json())

if __name__ == '__main__':
    # Start coverage measurement
    cov.start()

    # Run the test suite
    unittest.main()

    # Stop coverage measurement
    cov.stop()

    # Report coverage
    cov.report()
