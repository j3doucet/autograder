#!/usr/bin/env python3
import autograder, canvas
import subprocess
import shutil, os, stat, sys, re

if sys.hexversion < 0x030000F0:
    print("This script requires Python 3")
    sys.exit(1)


def compile_warning_errors(ag):
    (didRun, tooSlow, retcode, stdoutdata, stderrdata) = ag.run(['make'])

    for line in stderrdata.split('\n'):
        if " warning: " in line:
            ag.log_addEntry("Compiler warning: " + line, -2)
        if " error: " in line:
            ag.log_addEntry("Compiler error: " + line, -10)

def cppcheck(ag):
    cmd = subprocess.Popen("/usr/bin/cppcheck --std=c99 --quiet *.c",
                           shell=True, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    (stdoutdata, stderrdata)  = cmd.communicate()
    stderrdata = stderrdata.decode('utf-8','replace')
    for line in stderrdata.split('\n'):
        if "(error)" in line:
            ag.log_addEntry("cppcheck error: " + line, -1)

def stringMustContainRegex(ag, haystack, needle, pts):
    if re.search(needle, haystack, re.IGNORECASE):
        ag.log_addEntry("Output correctly contained '" + needle + "' (regex)", 0);
    else:
        ag.log_addEntry("Output did not contain '" + needle + "' (regex)", pts);

def stringMustContain(ag, haystack, needle, pts):
    needlelow = needle.lower()
    haystacklow = haystack.lower()
    if needlelow in haystacklow:
        ag.log_addEntry("Output correctly contained '" + needle + "'", 0);
    else:
        ag.log_addEntry("Output did not contain '" + needle + "'", pts);

def stringMustNotContain(ag, haystack, needle, pts):
    needlelow = needle.lower()
    haystacklow = haystack.lower()
    if needlelow not in haystacklow:
        ag.log_addEntry("Output correctly lacked '" + needle + "'.", 0);
    else:
        ag.log_addEntry("Output incorrectly contained '" + needle + "'.", pts);



config = autograder.config()
settings = config.get()
subdirName = settings['subdirName']


# Get a list of subdirectories (each student submission will be in its own subdirectory)
dirs = [name for name in os.listdir(subdirName) if os.path.isdir(os.path.join(subdirName, name))]
dirs.sort()
os.chdir(subdirName)

if len(sys.argv) > 1:
    dirs = sys.argv[1:]



desiredFiles = ["Hello.java"]
expectedExe =  ["Hello.class"]

# For each subdirectory (i.e., student)
for thisDir in dirs:
    # Skip submissions that do not need regrading. All AUTOGRADE.txt files should be deleted whenever the autograder tests are changed to ensure that the new tests are applied to any already-autograded.
    if os.path.exists(os.path.join(thisDir, "AUTOGRADE.txt")):
        print("SKIPPING %s because it has already been autograded." % thisDir);
        continue

    # Set up the autograder
    ag = autograder.autograder("AUTOGRADE.txt", thisDir)

    ag.log_addEntry("=== Verifying Submitted Files ===")
    # Verify that the files are there that we are expecting and look for unexpected files.
    if not ag.expect_only_files(desiredFiles + ["AUTOGRADE*.txt", "AUTOGRADE.json"], 100):
        ag.log_addEntry("Unexpected file submitted. Submit only files " + " ".join(desiredFiles))
        continue
    if ag.find_unexpected_subdirectories([], 100):
        ag.log_addEntry("Unexpected subdirectoryies in submission.")
        continue
    if not ag.expect_file_all_of(desiredFiles, 100):
        ag.log_addEntry("Please submit all of: " + " ".join(desiredFiles))
        continue
    ag.log_addEntry("=== File Verification Successful ===")
    ag.log_addEntry("=== Compiling Java to VM code ===")
    ag.javaCompile(desiredFiles)
    ag.log_addEntry("=== Compilation Successfull ===")

    ag.log_addEntry("=== Running Hello ===")
    ag.run_JavaStdoutMatch("Hello", stdindata=None, stdouttarget = "Hello World!\n", deductTimeout=100, deductWrongExit=100, deductOutputMismatch=50, timeout=5)

    # Insert additional tests here!

    ag.cleanup()
