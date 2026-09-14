import unittest

from ml.src.data_schema import (
    MODEL_FORBIDDEN_COLUMNS,
    SCHEMA_V2_COLUMNS,
    build_v2_record,
    classify_transaction,
    extract_amenities,
    make_listing_id,
    parse_location,
    parse_price,
    parse_surfaces,
)


class PriceParserTests(unittest.TestCase):
    def test_normal_mad_price(self):
        parsed = parse_price("1\u00a0200\u00a0000 DH", "SALE")
        self.assertEqual(parsed["price"], 1_200_000)
        self.assertEqual(parsed["currency"], "MAD")
        self.assertEqual(parsed["price_parse_status"], "PARSED")

    def test_formatted_million_price(self):
        parsed = parse_price("1,2 million DH", "SALE")
        self.assertEqual(parsed["price"], 1_200_000)

    def test_price_on_request_is_not_invented(self):
        parsed = parse_price("Prix à consulter", "SALE")
        self.assertIsNone(parsed["price"])
        self.assertEqual(parsed["price_parse_reason"], "price_on_request")

    def test_malformed_price_is_invalid(self):
        parsed = parse_price("prix ??? DH", "SALE")
        self.assertIsNone(parsed["price"])
        self.assertEqual(parsed["price_parse_status"], "INVALID")

    def test_price_per_m2_is_not_total(self):
        parsed = parse_price("12 500 DH/m²", "SALE")
        self.assertIsNone(parsed["price"])
        self.assertEqual(parsed["price_parse_reason"], "price_per_m2_not_total")


class StructuredParserTests(unittest.TestCase):
    def test_sale_rent_and_unknown(self):
        self.assertEqual(classify_transaction(title="Appartement à vendre")["transaction_type"], "SALE")
        self.assertEqual(classify_transaction(title="Studio à louer par mois")["transaction_type"], "RENT")
        self.assertEqual(classify_transaction(title="Bel appartement")["transaction_type"], "UNKNOWN")

    def test_surface_types_remain_separate(self):
        parsed = parse_surfaces("Terrain 500 m², surface habitable 250 m2")
        self.assertEqual(parsed["surface_land_m2"], 500)
        self.assertEqual(parsed["surface_built_m2"], 250)
        self.assertIsNone(parsed["surface_total_m2"])

    def test_generic_surface_becomes_total(self):
        self.assertEqual(parse_surfaces("Appartement de 92 m²")["surface_total_m2"], 92)

    def test_location_normalization_and_ambiguity(self):
        parsed = parse_location("Maârif, Casa")
        self.assertEqual((parsed["quartier"], parsed["city"]), ("Maârif", "Casablanca"))
        self.assertEqual(parse_location("Tangier")["city"], "Tanger")
        self.assertEqual(parse_location("Quartier inconnu")["location_parse_status"], "AMBIGUOUS")

    def test_amenities_are_tri_state(self):
        parsed = extract_amenities("Avec piscine, terrasse et sans ascenseur")
        self.assertTrue(parsed["pool"])
        self.assertTrue(parsed["terrace"])
        self.assertFalse(parsed["elevator"])
        self.assertIsNone(parsed["parking"])

    def test_stable_id_priority(self):
        native = make_listing_id("mubawab.ma", native_id="ABC123")
        by_url = make_listing_id("mubawab.ma", url="https://example.com/a?utm_source=x")
        fallback_a = make_listing_id("mubawab.ma", title="Appartement", location="Agdal", surface_m2=90)
        fallback_b = make_listing_id("mubawab.ma", title="Appartement", location="Agdal", surface_m2=90)
        self.assertEqual(native[1], "native_id")
        self.assertEqual(by_url[1], "canonical_url")
        self.assertEqual(fallback_a, fallback_b)

    def test_complete_record_preserves_raw_and_column_order(self):
        record = build_v2_record({
            "native_id": "42", "source_category": "appartements à vendre",
            "title_raw": "Appartement neuf à vendre avec piscine",
            "raw_price_text": "2 000 000 DH", "location_raw": "Agdal, Rabat",
            "details_raw": "100 m² 4 Pièces 3 Chambres 2 Salles de bains",
        })
        self.assertEqual(list(record), SCHEMA_V2_COLUMNS)
        self.assertEqual(record["price"], 2_000_000)
        self.assertEqual(record["surface_total_m2"], 100)
        self.assertTrue(record["pool"])
        self.assertEqual(record["title_raw"], "Appartement neuf à vendre avec piscine")

    def test_missing_values_remain_null_and_auditable(self):
        record = build_v2_record({"title_raw": "Annonce sans informations"})
        self.assertIsNone(record["price"])
        self.assertIsNone(record["city"])
        self.assertEqual(record["transaction_type"], "UNKNOWN")
        self.assertIn(record["validation_status"], {"WARNING", "INVALID"})

    def test_suspicious_sale_price_per_m2_is_audit_only_and_excluded(self):
        record = build_v2_record({
            "native_id": "outlier-1",
            "transaction_type": "SALE",
            "price_value": 100_000_000,
            "currency": "MAD",
            "city": "Casablanca",
            "property_type": "appartement",
            "surface_total_m2": 50,
        })
        self.assertFalse(record["model_eligible"])
        self.assertIn("price_per_m2_outlier", record["model_exclusion_reasons"])
        self.assertEqual(record["price_per_m2_audit"], 2_000_000)
        self.assertIn("price_per_m2_audit", MODEL_FORBIDDEN_COLUMNS)


if __name__ == "__main__":
    unittest.main()
