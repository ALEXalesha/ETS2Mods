"""No personal disk path of the author in the repository files.

The repository goes to GitHub as an open project. A path to the author's folder on his
disk (in examples, docs and scripts) carries his name. tools/publish_github.sh replaces
such a path in the whole history too (git config publish.privatePath), but this check
catches it earlier: on the very commit that brings it, and in CI as well.

The path is searched in any spelling: forward or back slash, a doubled back slash (as in
JSON and Python strings), any case. It is not written here in one piece - otherwise the
check would find itself.
"""
import os
import re
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERSONAL = re.compile(r"drive[\\/]+" + "alexey", re.IGNORECASE)
SKIP = {".git", "build", "release", "workshop", "extracted", "__pycache__", ".venv", ".ci-venv"}


def tracked_files():
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        # No git (a source archive): every file but the service folders.
        found = []
        for d, dirs, files in os.walk(ROOT):
            dirs[:] = [x for x in dirs if x not in SKIP]
            found += [os.path.join(d, f) for f in files]
        return found
    return [os.path.join(ROOT, name) for name in out.decode("utf-8").split("\0") if name]


class NoPersonalPathTest(unittest.TestCase):
    def test_no_personal_path_in_files(self):
        found = []
        for path in tracked_files():
            try:
                with open(path, "rb") as fh:
                    data = fh.read()
            except OSError:
                continue
            if b"\0" in data[:8192]:
                continue  # a binary file
            for n, line in enumerate(data.decode("utf-8", errors="replace").splitlines(), 1):
                if PERSONAL.search(line):
                    found.append("%s:%d" % (os.path.relpath(path, ROOT).replace("\\", "/"), n))
        self.assertFalse(found, "the author's personal path in files: " + ", ".join(found))

    def test_the_pattern_catches_every_spelling(self):
        head, tail = "Drive", "Alexey"
        for s in ("C:\\%s\\%s\\x" % (head, tail), "c:/%s/%s" % (head.lower(), tail.lower()),
                  "C:\\\\%s\\\\%s" % (head, tail), "/c/%s/%s/" % (head, tail)):
            self.assertTrue(PERSONAL.search(s), s)
        self.assertFalse(PERSONAL.search("C:\\Projects\\EuroTrackMyMods"))


if __name__ == "__main__":
    unittest.main()
