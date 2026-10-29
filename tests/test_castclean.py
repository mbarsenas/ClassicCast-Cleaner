import unittest
from castclean import safe_info


class SafeInfoTests(unittest.TestCase):
    def test_keeps_useful_fields(self):
        info = {
            "name": "Test Chromecast",
            "cast_build_revision": "3.72.446070",
            "opt_in": {"stats": True, "crash": True},
        }
        result = safe_info(info)
        self.assertEqual(result["name"], "Test Chromecast")
        self.assertEqual(result["opt_in"]["stats"], True)

    def test_omits_sensitive_identifiers(self):
        info = {
            "name": "Test Chromecast",
            "public_key": "not-for-logs",
            "uma_client_id": "private-id",
            "ssdp_udn": "private-udn",
            "ip_address": "192.0.2.10",
            "mac_address": "00:11:22:33:44:55",
        }
        result = safe_info(info)
        for key in ("public_key", "uma_client_id", "ssdp_udn", "ip_address", "mac_address"):
            self.assertNotIn(key, result)


if __name__ == "__main__":
    unittest.main()
