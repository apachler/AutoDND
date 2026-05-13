import importlib.util
import pathlib
import sys
import unittest
from datetime import datetime, timedelta
from importlib.machinery import SourceFileLoader

_path = pathlib.Path(__file__).resolve().parent.parent / 'files' / 'autodnd'
_loader = SourceFileLoader('autodnd', str(_path))
_spec = importlib.util.spec_from_loader('autodnd', _loader)
autodnd = importlib.util.module_from_spec(_spec)
sys.modules['autodnd'] = autodnd
_loader.exec_module(autodnd)


def at(when: datetime):
    autodnd.get_now = lambda: when.replace(second=0, microsecond=0)


class ExpandDays(unittest.TestCase):
    def test_numeric_list(self):
        self.assertEqual(autodnd.expand_days('0,1,2,3,4'), [0, 1, 2, 3, 4])

    def test_names(self):
        self.assertEqual(autodnd.expand_days('mon,wed,fri'), [0, 2, 4])

    def test_aliases(self):
        self.assertEqual(autodnd.expand_days('weekdays'), [0, 1, 2, 3, 4])
        self.assertEqual(autodnd.expand_days('weekends'), [5, 6])
        self.assertEqual(autodnd.expand_days('all'), [0, 1, 2, 3, 4, 5, 6])

    def test_numeric_range(self):
        self.assertEqual(autodnd.expand_days('0-4'), [0, 1, 2, 3, 4])

    def test_name_range(self):
        self.assertEqual(autodnd.expand_days('mon-fri'), [0, 1, 2, 3, 4])

    def test_mixed(self):
        self.assertEqual(autodnd.expand_days('weekdays,sat'), [0, 1, 2, 3, 4, 5])

    def test_rejects_reversed_range(self):
        with self.assertRaises(ValueError):
            autodnd.expand_days('4-2')

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            autodnd.expand_days(',mon')


class CreateDatetime(unittest.TestCase):
    def setUp(self):
        at(datetime(2026, 5, 13, 12, 0))

    def test_parses_hhmm(self):
        self.assertEqual(autodnd.create_datetime('08:30').hour, 8)
        self.assertEqual(autodnd.create_datetime('08:30').minute, 30)

    def test_rejects_bad_format(self):
        with self.assertRaises(ValueError):
            autodnd.create_datetime('8')

    def test_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            autodnd.create_datetime('25:00')
        with self.assertRaises(ValueError):
            autodnd.create_datetime('08:60')


class ParseLines(unittest.TestCase):
    def setUp(self):
        at(datetime(2026, 5, 13, 12, 0))

    def test_skips_comments_and_blanks(self):
        events = autodnd.parse_lines(['# x\n', '\n', '   \n'])
        self.assertEqual(events, [])

    def test_strips_inline_comments(self):
        events = autodnd.parse_lines(['mon 8:00 14:00  # school\n'])
        self.assertTrue(events)

    def test_reports_line_number(self):
        with self.assertRaises(ValueError) as cm:
            autodnd.parse_lines(['mon 8:00 14:00\n', 'bogus\n'])
        self.assertIn('line 2', str(cm.exception))

    def test_rejects_out_of_range_day(self):
        with self.assertRaises(ValueError) as cm:
            autodnd.parse_lines(['9 8:00 14:00'])
        self.assertIn('day 9', str(cm.exception))


class CrossMidnight(unittest.TestCase):
    def test_morning_half_detected(self):
        # Tue 02:00 — the Mon 22:00 -> Tue 10:00 event must be active.
        at(datetime(2026, 5, 12, 2, 0))
        events = autodnd.parse_lines(['weekdays 22:00 10:00'])
        self.assertTrue(autodnd.desired_state(events, autodnd.get_now()))

    def test_gap_during_day(self):
        # Tue 12:00 — between Mon-end and Tue-start, DnD off.
        at(datetime(2026, 5, 12, 12, 0))
        events = autodnd.parse_lines(['weekdays 22:00 10:00'])
        self.assertFalse(autodnd.desired_state(events, autodnd.get_now()))

    def test_weekend_off(self):
        # Sat 12:00 — no weekday event covers this.
        at(datetime(2026, 5, 16, 12, 0))
        events = autodnd.parse_lines(['weekdays 22:00 10:00'])
        self.assertFalse(autodnd.desired_state(events, autodnd.get_now()))

    def test_evening_active(self):
        # Mon 23:30 — start of the cross-midnight event.
        at(datetime(2026, 5, 11, 23, 30))
        events = autodnd.parse_lines(['weekdays 22:00 10:00'])
        self.assertTrue(autodnd.desired_state(events, autodnd.get_now()))


class MonthBoundary(unittest.TestCase):
    def test_no_crash_on_31st(self):
        at(datetime(2026, 5, 31, 23, 0))
        events = autodnd.parse_lines(['sun 22:00 10:00'])
        self.assertTrue(autodnd.desired_state(events, autodnd.get_now()))


class NextTransition(unittest.TestCase):
    def test_returns_soonest_boundary(self):
        at(datetime(2026, 5, 13, 12, 0))  # Wed 12:00
        events = autodnd.parse_lines(['weekdays 22:00 10:00'])
        transition = autodnd.next_transition(events, autodnd.get_now())
        self.assertEqual(transition, datetime(2026, 5, 13, 22, 0))


if __name__ == '__main__':
    unittest.main()
