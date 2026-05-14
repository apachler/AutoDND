import importlib.util
import io
import os
import pathlib
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta
from importlib.machinery import SourceFileLoader
from unittest.mock import patch

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


class NextWeekday(unittest.TestCase):
    def test_returns_two_occurrences_for_active_cross_midnight(self):
        # Tue 02:00 with Monday cross-midnight event: should return previous
        # (Mon→Tue, active) and next (next Mon→Tue) occurrences.
        at(datetime(2026, 5, 12, 2, 0))
        start = datetime(2026, 5, 12, 22, 0)  # placeholder, replaced by func
        end = datetime(2026, 5, 13, 10, 0)
        occ = autodnd.next_weekday(0, start, end)
        self.assertEqual(len(occ), 2)

    def test_returns_one_occurrence_when_no_active_previous(self):
        at(datetime(2026, 5, 13, 12, 0))  # Wed 12:00
        start = datetime(2026, 5, 13, 22, 0)
        end = datetime(2026, 5, 14, 10, 0)
        occ = autodnd.next_weekday(2, start, end)  # Wed
        self.assertEqual(len(occ), 1)


class ToDay(unittest.TestCase):
    def test_rejects_unknown_name(self):
        with self.assertRaises(ValueError) as cm:
            autodnd._to_day('xyz')
        self.assertIn('xyz', str(cm.exception))

    def test_accepts_known_name(self):
        self.assertEqual(autodnd._to_day('mon'), 0)

    def test_accepts_int_string(self):
        self.assertEqual(autodnd._to_day('3'), 3)


class CreateDatetimeIntFailure(unittest.TestCase):
    def setUp(self):
        at(datetime(2026, 5, 13, 12, 0))

    def test_non_numeric_components(self):
        with self.assertRaises(ValueError) as cm:
            autodnd.create_datetime('ab:cd')
        self.assertIn('ab:cd', str(cm.exception))


class SighupHandler(unittest.TestCase):
    def test_sets_reload_event(self):
        autodnd._reload_event.clear()
        autodnd._handle_sighup(1, None)
        self.assertTrue(autodnd._reload_event.is_set())
        autodnd._reload_event.clear()


class SetDnd(unittest.TestCase):
    @patch('autodnd.run')
    def test_enabled_passes_show_banners_false(self, mock_run):
        autodnd.set_dnd(True)
        mock_run.assert_called_once_with(
            ['gsettings','set','org.gnome.desktop.notifications','show-banners','false'],
            check=True,
        )

    @patch('autodnd.run')
    def test_disabled_passes_show_banners_true(self, mock_run):
        autodnd.set_dnd(False)
        mock_run.assert_called_once_with(
            ['gsettings','set','org.gnome.desktop.notifications','show-banners','true'],
            check=True,
        )


class GetNow(unittest.TestCase):
    def test_truncates_to_minute(self):
        # Load a fresh copy so monkeypatches to autodnd.get_now from other tests
        # don't shadow the implementation under test.
        fresh_loader = SourceFileLoader('autodnd_fresh', str(_path))
        fresh_spec = importlib.util.spec_from_loader('autodnd_fresh', fresh_loader)
        fresh = importlib.util.module_from_spec(fresh_spec)
        fresh_loader.exec_module(fresh)
        now = fresh.get_now()
        self.assertEqual(now.second, 0)
        self.assertEqual(now.microsecond, 0)


class Execute(unittest.TestCase):
    def setUp(self):
        autodnd._last_state = None

    def tearDown(self):
        autodnd._last_state = None

    def test_empty_events_exits(self):
        with self.assertRaises(SystemExit) as cm:
            autodnd.execute([])
        self.assertEqual(cm.exception.code, 0)

    @patch('autodnd.set_dnd')
    def test_transition_to_on_calls_set_dnd_true(self, mock_set_dnd):
        at(datetime(2026, 5, 11, 23, 0))  # Mon 23:00 — inside Mon 22:00→Tue 10:00
        events = autodnd.parse_lines(['mon 22:00 10:00'])
        autodnd._last_state = False  # was off
        autodnd.execute(events)
        mock_set_dnd.assert_called_once_with(True)
        self.assertTrue(autodnd._last_state)

    @patch('autodnd.set_dnd')
    def test_no_call_when_state_unchanged(self, mock_set_dnd):
        at(datetime(2026, 5, 13, 12, 0))  # Wed 12:00, not in any event
        events = autodnd.parse_lines(['weekdays 22:00 10:00'])
        autodnd._last_state = False
        autodnd.execute(events)
        mock_set_dnd.assert_not_called()

    @patch('autodnd.set_dnd')
    def test_first_call_sets_state(self, mock_set_dnd):
        at(datetime(2026, 5, 13, 12, 0))
        events = autodnd.parse_lines(['weekdays 22:00 10:00'])
        autodnd._last_state = None
        delta = autodnd.execute(events)
        mock_set_dnd.assert_called_once_with(False)
        self.assertIsInstance(delta, timedelta)

    @patch('autodnd.set_dnd')
    def test_returns_positive_delta_to_next_transition(self, mock_set_dnd):
        # execute() uses real datetime.now() for its final sleep-delta;
        # pin it alongside get_now() so the test isn't wall-clock-dependent.
        pinned = datetime(2026, 5, 13, 12, 0)
        at(pinned)
        events = autodnd.parse_lines(['weekdays 22:00 10:00'])
        with patch.object(autodnd, 'datetime') as mock_dt:
            mock_dt.now.return_value = pinned
            delta = autodnd.execute(events)
        self.assertGreater(delta.total_seconds(), 0)


class MainCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = pathlib.Path(self.tmp.name)
        (self.home / '.config' / 'autodnd').mkdir(parents=True)
        self.cfg = self.home / '.config' / 'autodnd' / 'config.txt'
        self.cfg.write_text('weekdays 8:00 14:00\n')
        self._old_home = os.environ.get('HOME')
        os.environ['HOME'] = str(self.home)
        autodnd._last_state = None
        autodnd._reload_event.clear()

    def tearDown(self):
        self.tmp.cleanup()
        if self._old_home is not None:
            os.environ['HOME'] = self._old_home

    def _run_main(self, *args):
        old_argv = sys.argv
        sys.argv = ['autodnd', *args]
        out = io.StringIO()
        err = io.StringIO()
        code = None
        try:
            # autodnd imports `stderr` into its namespace, so redirect_stderr
            # alone won't catch its prints — patch the module attribute too.
            with redirect_stdout(out), redirect_stderr(err), \
                 patch.object(autodnd, 'stderr', err):
                autodnd.main()
        except SystemExit as e:
            code = e.code
        finally:
            sys.argv = old_argv
        return code, out.getvalue(), err.getvalue()

    def test_check_succeeds(self):
        code, out, _ = self._run_main('--check')
        self.assertEqual(code, 0)
        self.assertIn('occurrences', out)

    def test_status_prints_state(self):
        code, out, _ = self._run_main('--status')
        self.assertEqual(code, 0)
        self.assertIn('DnD desired state', out)
        self.assertIn('next transition', out)

    @patch('autodnd.set_dnd')
    def test_once_calls_execute_then_exits(self, mock_set_dnd):
        code, _, _ = self._run_main('--once')
        self.assertEqual(code, 0)

    def test_bad_config_exits_with_message(self):
        self.cfg.write_text('garbage\n')
        code, _, err = self._run_main('--check')
        self.assertEqual(code, 2)
        self.assertIn('config error', err)
        self.assertIn('line 1', err)

    def test_creates_missing_config(self):
        self.cfg.unlink()
        code, _, _ = self._run_main('--check')
        self.assertEqual(code, 0)
        self.assertTrue(self.cfg.exists())


if __name__ == '__main__':
    unittest.main()
