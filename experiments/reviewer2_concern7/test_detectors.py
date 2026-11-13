import unittest
from detectors import extra_flags


class DetectorTests(unittest.TestCase):
    def test_expansions_and_known_limit(self):
        text = 'Human immunodeficiency virus (HIV) and COPD (chronic obstructive pulmonary disease) matter.'
        flags = extra_flags(text, text, 'stop')
        self.assertFalse(flags['acronym_without_detected_expansion_candidate'])
        flags = extra_flags('', 'Human immunodeficiency virus, also called HIV, matters.', 'stop')
        self.assertTrue(flags['acronym_without_detected_expansion_candidate'])  # known false-positive form

    def test_format_and_endpoint_are_indicators(self):
        flags = extra_flags('', 'Here is the simplified text:\n- First item\n- Second item', 'stop')
        self.assertTrue(flags['preamble_candidate'])
        self.assertTrue(flags['two_or_more_list_markers'])
        self.assertTrue(flags['stop_no_terminal_punctuation_candidate'])  # complete list can trigger it
        self.assertFalse(extra_flags('', 'Researchers say here is an example.', 'stop')['preamble_candidate'])
        self.assertFalse(extra_flags('', 'unfinished', 'length')['stop_no_terminal_punctuation_candidate'])
        self.assertFalse(extra_flags('', '', 'stop')['stop_no_terminal_punctuation_candidate'])


if __name__ == '__main__':
    unittest.main()
