#!/usr/bin/env python
"""
    Make a release of HPCombi from the current directory.
"""
# pylint: disable=invalid-name, missing-function-docstring

import os
import re
import sys
import subprocess

from release import main as _main
from release import (
    new_version,
    old_version,
    rc_branch,
    stable_branch,
    today,
    exec_string,
    add_checks,
    exit_abort,
    get_file_contents,
)

###############################################################################
# Prerelease checks
###############################################################################


def _check_readme():
    """
    Check if the README.md is up to date.
    """
    readme = get_file_contents("README.md")
    if readme.find("v" + old_version()) != -1:
        line_num = readme.count("\n", 0, readme.find(old_version()))
        exit_abort(f"Found old version number {old_version()} in README.md:{line_num}")
    return "ok!"


def _check_cmakelists_txt_version_number():
    version_number = new_version().split(".")
    with open("CMakeLists.txt", "r", encoding="utf-8") as f:
        f = f.read()
        for i, part in enumerate(("MAJOR", "MINOR", "PATCH")):
            p = fr"set\(VERSION_{part}\s*(\d+)"
            m = re.search(p, f)
            if m is None:
                exit_abort(f"Cannot find {part} version number in CMakeLists.txt")
            elif m.group(1) != version_number[i]:
                exit_abort(
                    f"{part} version number in CMakeLists.txt is {m.group(1)}"
                    + f", should be {version_number[i]}"
                )
    return "ok!"

def _check_cpplint():
   try:
       exec_string("cpplint --repository=include include/hpcombi/*.hpp")
   except subprocess.CalledProcessError as e:
       sys.stderr.write("\n" + "\n".join(x for x in e.output.decode("utf-8").split("\n") if not x.startswith("Done processing")))
       sys.stderr.flush()
       exit_abort("cpplint failed")
   return "ok!"

add_checks(
    ("version number in README.md", _check_readme),
    ("version number in CMakeLists.txt", _check_cmakelists_txt_version_number),
    ("running cpplint", _check_cpplint),
)

def release_steps():
    """
    The steps required to finalize the release.
    """
    url = "https://github.com/libsemigroups/hpcombi/pull/new/"
    return (
        f"git push origin {rc_branch()}",
        "open a PR from {0} to {1} (create {1} if necessary): {2}{0}".format(
            rc_branch(), stable_branch(), url
        ),
        "wait for the CI to complete successfully",
        f"git checkout {stable_branch()} && git merge {rc_branch()} && git tag v{new_version()}",
        f"git push origin {stable_branch()} --tags",
        "create a new release at https://github.com/libsemigroups/hpcombi/releases/new",
        f"git checkout main && git merge {stable_branch()} && git push origin main"
    )


def main():
    _main(release_steps, "release_hpcombi")


if __name__ == "__main__":
    main()
