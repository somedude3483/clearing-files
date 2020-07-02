"""space.py

space.py is a module that manages files.
All it can do at the moment is get the total space in a directory and delete them.

How to use it:
We have multiple functions.
===================================================================================
clear_logs(*, delete=False)
This function clears the file deleted_files.log in the Contents folder.

If the keyword argument delete is set to True, it will try to delete it,
however, if the file is being occupied by another process, an error will be raised.
===================================================================================
get_total_stats()
This function returns the contents in stats.json.

It takes no arguments.
===================================================================================
get_folder_size(*, cwd=None, skip_files=None, display_all_files=True)
This function gets the size of a folder.

The keyword arguments it accepts are:
cwd - To go to a specific directory.
skip_files - to skip certain files.
display_all_files - To print out each file and the space it takes to the console.

This function is ran in the main function.
===================================================================================
remove_all_files(display_removed: bool = False, log_files: bool = True):

This function removes the files that the function get_folder_size logged.
It warns you if you are in deletion mode.

It logs the amount of files that you have deleted called deleted_files.log.
It creates deleted_files.log in the directory you chose.

If display_removed is set to True, it will display all the files in KB and the file
being removed.

If log_files is set to True, it will create a deleted_files.log and log it there,
however if it's set to false, it will not log anything and won't create a file.
===================================================================================
def main(*, cwd: str, skip_list: list, remove_files: bool = False, fast_mode: bool = False):
This is the main function.

It prints each file and the space it takes that the function get_folder_size yielded.
"""

import warnings
import logging
import ctypes
import glob
import json
import time
import sys
import os
from json.decoder import JSONDecodeError

contents_dir = os.path.dirname(os.path.abspath(__file__))
is_idle = "idlelib.run" in sys.modules
start_time = time.time()
total_space = list()
files = list()

main_files = [
    "deleted_files.log",
    "remove.py",
    "space.py",
    "stats.json",
    "json_template.txt",
]
template = {"total_mb": 0, "total_files": 0}


class SpaceError(Exception):
    """SpaceError
    Base space exception"""


class MissingDirectoryError(SpaceError):
    """MissingDirectoryError.
    Directory was not specified on function call."""


class OccupiedError(SpaceError):
    """OccupiedError
    File cannot be removed because it is occupied by another process."""

    def __init__(self, file, second_exc):
        self.file = file
        self.second_exc = second_exc

    def __str__(self):
        if os.path.isfile(self.file):
            return repr(
                "%s could not be removed because another process is occupying it."
                "Close that process and try again. \n %s" % (self.file, self.second_exc)
            )
        return repr("Something went wrong with the program with a second exception of %s"
                    % (self.second_exc))


def _enable_colour(*, enable=True):
    """Enables colour in other terminals that don't support colour"""
    if not is_idle:
        if enable:
            kernel32 = ctypes.WinDLL("kernel32")
            stdout_, mode = kernel32.GetStdHandle(-11), ctypes.c_ulong()

            kernel32.GetConsoleMode(stdout_, ctypes.byref(mode))
            kernel32.SetConsoleMode(stdout_, mode.value | 4)
            return ["\033[01m\033[31m", "\033[01m\033[32m "]
        return "\033[0m"
    return ""


def clear_logs(*, delete=False):
    """Clears deleted_files.log in the Contents folder.
    Takes keyword argument clear_logs(*, delete=False)
    if delete is called with True, it will delete the file if it's not occupied.
    If it is occupied, OccupiedError will be raised."""

    if delete:
        log_file = fr"{contents_dir}\Contents\deleted_files.log"
        try:
            os.remove(log_file)
            return f"{log_file} was successfully removed."
        except PermissionError as error:
            raise OccupiedError(log_file, error) from None
    with open(fr"{contents_dir}\Contents\deleted_files.log", "w+"):
        return "Wiped log file"


def get_total_stats():
    """Get the total stats in the file.
    This function returns the total space deleted in Megabytes
    and the total files deleted."""
    return json.load(open(fr"{contents_dir}\Contents\stats.json", "r+"))


def get_folder_size(*, cwd=None, skip_files=None, display_all_files=True):
    """Yields the space of each file not including the unwanted file in KB."""
    try:
        if os.path.isdir(cwd):
            os.chdir(cwd)

            for file in glob.glob("*"):
                if file not in skip_files:

                    files.append(file)
                    space = os.stat(file).st_size
                    total_space.append(int(space))
                    if display_all_files:
                        yield f"{file} takes up {space/1000}KB"
                else:
                    yield f"Skipped unwanted file, {file}"
    except TypeError:
        if cwd is None:
            org_error, line = sys.exc_info()[1], sys.exc_info()[-1].tb_lineno

            raise MissingDirectoryError(
                'Invalid directory, "%s". '
                "Please specify a directory when calling the function."
                " Cause: %s at line %s" % (cwd, org_error, line)
            ) from None


def remove_all_files(display_removed: bool = False, log_files: bool = True):
    """Removes files in kwarg cwd mentioned in function get_folder_size."""
    print(_enable_colour(enable=True)[0] if not is_idle else "")
    warnings.warn(
        "\n\nYou are currently in delete files mode. "
        "To confirm deletion, press Y and enter. "
        "Anything else will abort the deletion.\n"
        "Once entered deletion mode, there is no rolling back. "
        "Continue? Y/N",
        Warning,
    )
    print(_enable_colour(enable=False))

    continue_ = input()
    if continue_ in ["Y", "y"]:
        try:
            json_file_contents = get_total_stats()
        except (JSONDecodeError, FileNotFoundError):
            with open(fr"{contents_dir}\Contents\stats.json", "w+") as stats:
                json.dump(template, stats)
        json_file_contents = get_total_stats()

        # print("CHECK")
        stats = {
            "total_mb": sum(total_space) / 1_000_000 + json_file_contents["total_mb"],
            "total_files": len(files) + json_file_contents["total_files"],
        }
        if log_files:
            logging.basicConfig(
                filename=fr"{contents_dir}\Contents\deleted_files.log",
                format="%(asctime)s %(message)s",
                filemode="a",
            )

            logger = logging.getLogger()
            logger.setLevel(logging.DEBUG)
        for file in files:
            try:
                os.remove(file)
                if display_removed:
                    print(
                        f'Deletion Successful: "{file}" was deleted from'
                        f"{os.getcwd()}"
                    )
            except PermissionError as error:
                print(f"Error - {error} Permission Denied for {file}")
        if log_files:
            logger.info(
                "Deletion successful - %i deleted.\n" "%iMB freed up.\n",
                len(files),
                sum(total_space) / 1_000_000,
            )

        with open(fr"{contents_dir}\Contents\stats.json", "w+") as json_file:
            json.dump(stats, json_file)
        json_file_contents = get_total_stats()

        total_files = f"{'{:,} files'.format(json_file_contents['total_files'])}"
        total_space_ = f"{'{:,}MB'.format(int(json_file_contents['total_mb']))}"
        print(
            f"{'Total files deleted'}: {total_files:>{40-len('Total files deleted')}}",
            f"{'Total space cleared'}: {total_space_:>{40-len('Total space cleared')}}",
            sep="\n",
        )
    else:
        print(
            f"{_enable_colour(enable=True)[1]}Deletion aborted.{_enable_colour(enable=False)}"
            if not is_idle
            else "Deletion aborted."
        )


def main(
        *, cwd: str, skip_list: list, remove_files: bool = False, fast_mode: bool = False
):
    """Prints out the space of each file in Kilobytes, as well as the total
    space of the folder in Megabytes.

       Also prompts you if you want to delete all the files.
       Deletes the files and logs them in deleted_files.log as well.
    """

    if main_files not in skip_list:
        skip_list.extend(main_files)
    print(cwd)

    for logged_file in get_folder_size(
                        cwd=cwd,  # Set this to the directory you want to scan.
                        display_all_files=not fast_mode,
                        # ^ if True, display each file and how much they take in KB.
                        skip_files=skip_list
    ):
        print(logged_file)
    print("{:.2f}MB in current folder.".format(sum(total_space) / 1_000_000))

    if remove_files:
        remove_all_files(not fast_mode, True)


if __name__ == "__main__":
    if not os.path.isdir(contents_dir):
        os.mkdir("Contents")
    main(
        cwd=r"PUT DIRECTORY HERE",
        skip_list=[  # List of ignored files
            "data_0",
            "data_1",
            "data_2",
            "data_3",
            "index",
        ],
        remove_files=True,  # Set this to True to enter Deletion mode.
        fast_mode=True,
    )  # Set this to True to make the process faster.
    print("Program finished in [{:.3f}s]".format(time.time() - start_time))
    if not is_idle:
        time.sleep(20)
