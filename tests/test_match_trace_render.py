"""Reconstruction contracts; synthetic fixtures are not observed matches."""
import copy
from pathlib import Path
import runpy
import unittest
import xml.etree.ElementTree as ET

from mid_fast_v1.fixtures import base
from mid_fast_v1.engine import MidEngine
from mid_fast_v2.trace import snapshot

MODULE = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                          'research/v3/cloud-coach/trace/render_snapshot.py'))


class TraceRenderTests(unittest.TestCase):
    def record(self):
        state = base()
        commands, audit = MidEngine().choose(state, 'synthetic-render')
        return snapshot(state, commands, audit, 123)

    def test_svg_marks_limits_and_escapes_text(self):
        record = self.record()
        record['ownIntent'] = ['<script>unsafe</script>']
        svg = MODULE['render'](record)
        ET.fromstring(svg)
        self.assertNotIn('<script>', svg)
        self.assertIn('NOT gameplay footage', svg)
        self.assertIn('Goals not surveyed', svg)
        self.assertIn('unknown team-qualified owner', MODULE['render']({**record, 'ball': {
            **record['ball'], 'possessionTeamCode': None}}))

    def test_ground_plane_is_explicit_and_unknown_frames_rejected(self):
        record = self.record()
        record['frame'] = 'keeper_reference_xz'
        record['ball']['position'] = {'x': 2, 'y': .5, 'z': -3}
        self.assertEqual(MODULE['points'](record)[-1], (2, -3))
        record['frame'] = 'documented_xy_3d'
        self.assertEqual(MODULE['points'](record)[-1], (2, .5))
        record['frame'] = 'unresolved_3d'
        with self.assertRaises(ValueError):
            MODULE['render'](record)

    def test_duplicate_identity_and_missing_positions_rejected(self):
        record = self.record()
        broken = copy.deepcopy(record)
        broken['players'][0] = broken['players'][1]
        with self.assertRaises(ValueError):
            MODULE['render'](broken)
        record['players'][0]['position']['x'] = None
        with self.assertRaises(ValueError):
            MODULE['render'](record)


if __name__ == '__main__':
    unittest.main()
