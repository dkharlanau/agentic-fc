"""Offline stream fixtures; no boto3 import, network, or live session."""
import unittest
import lab

probe = lab.load_module('d02_probe', lab.HERE / 'candidate/harness-route-timing.py')


class StreamTimingTests(unittest.TestCase):
    def collect(self, events):
        ticks = iter(range(1, 30))
        return probe.collect_stream(events, 0, now=lambda: next(ticks) / 1000)

    def test_metadata_and_message_start_are_not_first_text(self):
        row = self.collect(iter([
            {'messageStart': {}}, {'contentBlockDelta': {'delta': {'text': ''}}},
            {'contentBlockDelta': {'delta': {'text': '['}}},
            {'contentBlockDelta': {'delta': {'text': ']'}}},
            {'messageStop': {}}, {'metadata': {'usage': {'outputTokens': 2}}}]))
        self.assertEqual((row['firstEventMs'], row['firstTextMs'], row['lastTextMs']), (1, 3, 4))
        self.assertEqual(row['messageStopMs'], [5])
        self.assertEqual(row['completeMs'], 7)
        self.assertEqual(row['text'], '[]')
        self.assertIsNone(row['serverApplyMs'])

    def test_valid_prefix_does_not_hide_trailing_explanation(self):
        text = '[{"commandType":"CLEAR_OVERRIDE","playerId":0,"parameters":{},"duration":0}]'
        row = self.collect(iter([
            {'contentBlockDelta': {'delta': {'text': text}}}, {'messageStop': {}},
            {'contentBlockDelta': {'delta': {'text': '\nExplanation'}}}, {'messageStop': {}}]))
        self.assertTrue(row['streamComplete'])
        self.assertEqual(row['messageStopMs'], [2, 4])
        self.assertEqual(lab.command_errors(row['text'], 'gk'), ['not_exact_json_command_array'])
        self.assertEqual(row['completeMs'], 5)

    def test_transport_exception_preserves_partial_and_censored_time(self):
        def stream():
            yield {'contentBlockDelta': {'delta': {'text': '['}}}
            raise TimeoutError('private detail must not be serialized')
        row = self.collect(stream())
        self.assertFalse(row['streamComplete'])
        self.assertIsNone(row['completeMs'])
        self.assertEqual(row['observedElapsedMs'], 2)
        self.assertEqual(row['streamFailureType'], 'TimeoutError')
        self.assertEqual(row['text'], '[')

    def test_service_error_is_not_a_complete_success(self):
        row = self.collect(iter([{'throttlingException': {'message': 'synthetic'}}]))
        self.assertFalse(row['streamComplete'])
        self.assertIsNone(row['firstTextMs'])
        self.assertIsNone(row['completeMs'])
        self.assertEqual(row['errors'][0]['type'], 'throttlingException')

    def test_empty_stream_is_transport_complete_but_has_no_valid_command(self):
        row = self.collect(iter([]))
        self.assertTrue(row['streamComplete'])
        self.assertIsNone(row['firstEventMs'])
        self.assertIsNone(row['firstTextMs'])
        self.assertTrue(lab.command_errors(row['text'], 'gk'))


if __name__ == '__main__':
    unittest.main()
