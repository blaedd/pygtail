import gzip
import io
import os
import shutil
import sys
import tempfile
import unittest

import pytest

from pygtail import Pygtail


class PygtailTest(unittest.TestCase):
    # TODO:
    # - test for non-default offset file
    # - test for savelog and datext rotation schemes

    def setUp(self):
        self.test_lines = ["1\n", "2\n", "3\n"]
        self.test_str = ''.join(self.test_lines)
        self.logfile = tempfile.NamedTemporaryFile(mode='w+', delete=False)
        self.logfile.write(self.test_str)
        self.logfile.close()

    def append(self, text):
        # append the give string to the temp logfile
        fh = open(self.logfile.name, "a")
        fh.write(text)
        fh.close()

    def copytruncate(self):
        shutil.copyfile(self.logfile.name, "%s.1" % self.logfile.name)
        fh = open(self.logfile.name, "a")
        fh.truncate(0)
        fh.close()

    def tearDown(self):
        filename = self.logfile.name
        for tmpfile in [filename, filename + ".offset", filename + ".1", filename + ".1.gz"]:
            if os.path.exists(tmpfile):
                os.remove(tmpfile)

    def test_read(self):
        pygtail = Pygtail(self.logfile.name)
        self.assertEqual(pygtail.read(), self.test_str)

    def test_readlines(self):
        pygtail = Pygtail(self.logfile.name)
        self.assertEqual(pygtail.readlines(), self.test_lines)

    def test_subsequent_read_with_no_new_data(self):
        pygtail = Pygtail(self.logfile.name)
        self.assertEqual(pygtail.read(), self.test_str)
        self.assertEqual(pygtail.read(), None)

    def test_subsequent_read_with_new_data(self):
        pygtail = Pygtail(self.logfile.name)
        self.assertEqual(pygtail.read(), self.test_str)
        new_lines = "4\n5\n"
        self.append(new_lines)
        new_pygtail = Pygtail(self.logfile.name)
        self.assertEqual(new_pygtail.read(), new_lines)

    def test_read_from_the_file_end(self):
        pygtail = Pygtail(self.logfile.name, read_from_end=True)
        self.assertEqual(pygtail.read(), None)
        new_lines = "4\n5\n"
        self.append(new_lines)
        new_pygtail = Pygtail(self.logfile.name, read_from_end=True)
        self.assertEqual(new_pygtail.read(), new_lines)

    @pytest.mark.skipif(sys.platform == 'win32', reason="Windows can't rename an open file")
    def test_logrotate_without_delay_compress(self):
        new_lines = ["4\n5\n", "6\n7\n"]
        pygtail = Pygtail(self.logfile.name)
        pygtail.read()
        self.append(new_lines[0])

        # put content to gzip file
        gzip_handle = gzip.open("%s.1.gz" % self.logfile.name, 'wb')
        with open(self.logfile.name, 'rb') as logfile:
            gzip_handle.write(logfile.read())
        gzip_handle.close()

        with open(self.logfile.name, 'w'):
            # truncate file
            pass

        self.append(new_lines[1])
        pygtail = Pygtail(self.logfile.name)
        self.assertEqual(pygtail.read(), ''.join(new_lines))

    @pytest.mark.skipif(sys.platform == 'win32', reason="Windows can't rename an open file")
    def test_logrotate_with_delay_compress(self):
        new_lines = ["4\n5\n", "6\n7\n"]
        pygtail = Pygtail(self.logfile.name)
        pygtail.read()
        self.append(new_lines[0])
        os.rename(self.logfile.name, "%s.1" % self.logfile.name)
        self.append(new_lines[1])
        pygtail = Pygtail(self.logfile.name)
        self.assertEqual(pygtail.read(), ''.join(new_lines))

    @pytest.mark.skipif(sys.platform == 'win32', reason="Windows can't rename an open file")
    def test_logrotate_with_dateext_with_delaycompress(self):
        new_lines = ["4\n5\n", "6\n7\n"]
        pygtail = Pygtail(self.logfile.name)
        pygtail.read()
        self.append(new_lines[0])
        os.rename(self.logfile.name, "%s-20160616" % self.logfile.name)
        self.append(new_lines[1])
        pygtail = Pygtail(self.logfile.name)
        self.assertEqual(pygtail.read(), ''.join(new_lines))

    @pytest.mark.skipif(sys.platform == 'win32', reason="Windows can't rename an open file")
    def test_logrotate_with_dateext_without_delaycompress(self):
        new_lines = ["4\n5\n", "6\n7\n"]
        pygtail = Pygtail(self.logfile.name)
        pygtail.read()
        self.append(new_lines[0])

        # put content to gzip file
        gzip_handle = gzip.open("%s-20160616.gz" % self.logfile.name, 'wb')
        with open(self.logfile.name, 'rb') as logfile:
            gzip_handle.write(logfile.read())
        gzip_handle.close()

        with open(self.logfile.name, 'w'):
            # truncate file
            pass

        self.append(new_lines[1])
        pygtail = Pygtail(self.logfile.name)
        self.assertEqual(pygtail.read(), ''.join(new_lines))

    @pytest.mark.skipif(sys.platform == 'win32', reason="Windows can't rename an open file")
    def test_logrotate_with_dateext2_with_delaycompress(self):
        new_lines = ["4\n5\n", "6\n7\n"]
        pygtail = Pygtail(self.logfile.name)
        pygtail.read()
        self.append(new_lines[0])
        os.rename(self.logfile.name, "%s-20160616-1466093571" % self.logfile.name)
        self.append(new_lines[1])
        pygtail = Pygtail(self.logfile.name)
        self.assertEqual(pygtail.read(), ''.join(new_lines))

    @pytest.mark.skipif(sys.platform == 'win32', reason="Windows can't rename an open file")
    def test_logrotate_with_dateext2_without_delaycompress(self):
        new_lines = ["4\n5\n", "6\n7\n"]
        pygtail = Pygtail(self.logfile.name)
        pygtail.read()
        self.append(new_lines[0])
        # put content to gzip file
        gzip_handle = gzip.open("%s-20160616-1466093571.gz" % self.logfile.name, 'wb')
        with open(self.logfile.name, 'r') as logfile:
            gzip_handle.write(logfile.read().encode(sys.getdefaultencoding()))
        gzip_handle.close()

        with open(self.logfile.name, 'w'):
            # truncate file
            pass

        self.append(new_lines[1])
        pygtail = Pygtail(self.logfile.name)
        self.assertEqual(pygtail.read(), ''.join(new_lines))

    @pytest.mark.skipif(sys.platform == 'win32', reason="Windows can't rename an open file")
    def test_timed_rotating_file_handler(self):
        new_lines = ["4\n5\n", "6\n7\n"]
        pygtail = Pygtail(self.logfile.name)
        pygtail.read()
        self.append(new_lines[0])
        os.rename(self.logfile.name, "%s.2016-06-16" % self.logfile.name)
        self.append(new_lines[1])
        pygtail = Pygtail(self.logfile.name)
        self.assertEqual(pygtail.read(), ''.join(new_lines))

    def test_custom_rotating_file_handler_with_prepend(self):
        new_lines = ["4\n5\n", "6\n7\n"]
        pygtail = Pygtail(self.logfile.name)
        pygtail.read()
        self.append(new_lines[0])
        del pygtail
        file_dir, rel_filename = os.path.split(self.logfile.name)
        os.rename(self.logfile.name, os.path.join(file_dir, "custom_log_pattern.%s" % rel_filename))
        self.append(new_lines[1])
        pygtail = Pygtail(self.logfile.name, log_patterns=["custom_log_pattern.%s"])
        self.assertEqual(pygtail.read(), ''.join(new_lines))

    def test_copytruncate_off_smaller(self):
        self.test_readlines()
        self.copytruncate()
        new_lines = "4\n5\n"
        self.append(new_lines)
        sys.stderr = captured = io.StringIO()
        pygtail = Pygtail(self.logfile.name, copytruncate=False)
        captured_value = captured.getvalue()
        sys.stderr = sys.__stderr__

        self.assertRegex(captured_value, r".*?\bWARN\b.*?\bshrank\b.*")
        self.assertEqual(pygtail.read(), None)

    def test_copytruncate_on_smaller(self):
        self.test_readlines()
        self.copytruncate()
        new_lines = "4\n5\n"
        self.append(new_lines)
        pygtail = Pygtail(self.logfile.name, copytruncate=True)
        self.assertEqual(pygtail.read(), new_lines)

    def _test_copytruncate_larger(self, onoff):
        self.test_readlines()
        self.copytruncate()
        self.append(self.test_str)
        new_lines = "4\n5\n"
        self.append(new_lines)
        pygtail = Pygtail(self.logfile.name, copytruncate=onoff)
        self.assertEqual(pygtail.read(), new_lines)

    def test_copytruncate_larger_off(self):
        self._test_copytruncate_larger(False)

    def test_copytruncate_larger_on(self):
        self._test_copytruncate_larger(True)

    def test_offset_file(self):
        pygtail = Pygtail(self.logfile.name, paranoid=True)

        log_inode = os.stat(self.logfile.name).st_ino
        offset_per_line = 1 +len(os.linesep)
        next(pygtail)
        with open(self.logfile.name + '.offset', 'r') as f:
            inode, offset = int(next(f)), int(next(f))
        self.assertEqual(inode, log_inode)
        self.assertEqual(offset, 1*offset_per_line)

        next(pygtail)
        with open(self.logfile.name + '.offset', 'r') as f:
            inode, offset = int(next(f)), int(next(f))
        self.assertEqual(inode, log_inode)
        self.assertEqual(offset, 2*offset_per_line)

        next(pygtail)
        with open(self.logfile.name + '.offset', 'r') as f:
            inode, offset = int(next(f)), int(next(f))
        self.assertEqual(inode, log_inode)
        self.assertEqual(offset, 3*offset_per_line)

    def test_on_update_with_paranoid(self):
        updates = [0]

        def record_update():
            updates[0] += 1

        pygtail = Pygtail(self.logfile.name, paranoid=True,
                          on_update=record_update)

        self.assertEqual(updates[0], 0)
        next(pygtail)
        self.assertEqual(updates[0], 1)
        next(pygtail)
        self.assertEqual(updates[0], 2)
        next(pygtail)
        self.assertEqual(updates[0], 3)

    def test_on_update_without_paranoid(self):
        updates = [0]

        def record_update():
            updates[0] += 1

        pygtail = Pygtail(self.logfile.name, on_update=record_update)

        self.assertEqual(updates[0], 0)
        for line in pygtail:
            self.assertEqual(updates[0], 0)
        self.assertEqual(updates[0], 1)

    def test_every_n(self):
        updates = [0]
        # We save before returning the second line.
        # We save at the end of the file with all 3 recorded.
        expected = [1, 3]
        previous_lines = 0

        def record_update():
            self.assertEqual(previous_lines, expected[updates[0]])
            updates[0] += 1

        pygtail = Pygtail(self.logfile.name, every_n=2, on_update=record_update)

        self.assertEqual(updates[0], 0)
        for line in pygtail:
            previous_lines += 1

    @pytest.mark.skipif(sys.platform == 'win32', reason="Windows can't rename an open file")
    def test_renamecreate(self):
        """
        Tests "renamecreate" semantics where the currently processed file gets renamed and the
        original file gets recreated. This is the behavior of certain logfile rollers such as
        TimeBasedRollingPolicy in Java's Logback library.
        """
        new_lines = ["4\n5\n", "6\n7\n"]
        pygtail = Pygtail(self.logfile.name)
        pygtail.read()
        os.rename(self.logfile.name, "%s.2018-03-10" % self.logfile.name)
        # append will recreate the original log file
        self.append(new_lines[0])
        self.append(new_lines[1])
        self.assertEqual(pygtail.read(), ''.join(new_lines))

    def test_full_lines(self):
        """
        Tests lines are logged only when they have a new line at the end. This is useful to ensure that log lines
        aren't unintentionally split up.
        """
        pygtail = Pygtail(self.logfile.name, full_lines=True)
        new_lines = "4\n5,"
        last_line = "5.5\n6\n"

        self.append(new_lines)
        pygtail.read()
        self.append(last_line)
        self.assertEqual(pygtail.read(), "5,5.5\n6\n")


def main():
    unittest.main(buffer=True)


if __name__ == "__main__":
    main()
