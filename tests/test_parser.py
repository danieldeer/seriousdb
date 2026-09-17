import unittest

from seriousdb.parser import parse_value


class ParserTests(unittest.TestCase):
    def test_string(self):
        self.assertEqual(parse_value("Alice"), "Alice")

    def test_integer(self):
        self.assertEqual(parse_value("42"), 42)

    def test_float(self):
        self.assertEqual(parse_value("3.14"), 3.14)

    def test_boolean(self):
        self.assertEqual(parse_value("true"), True)
        self.assertEqual(parse_value("false"), False)

    def test_null(self):
        self.assertIsNone(parse_value("null"))

    def test_list(self):
        self.assertEqual(parse_value("[1, 2, 3]"), [1, 2, 3])

    def test_dict(self):
        self.assertEqual(
            parse_value('{"name": "Alice"}'),
            {"name": "Alice"},
        )

    def test_plain_string(self):
        self.assertEqual(parse_value("hello world"), "hello world")
