#!/usr/bin/env python3
import autograder, canvas
import subprocess
import shutil, os, stat, sys, re
import glob



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

rubricRoot = sys.argv[1]
print(rubricRoot)
questions = [name for name in os.listdir(rubricRoot) if os.path.isdir(os.path.join(rubricRoot, name))]
print(questions)

pointTotal = 0
for q in questions:
    pointTotal += int(open(os.path.join(rubricRoot, q, "points")).readline().split()[0])


                

# For each subdirectory (i.e., student)
for thisDir in dirs:
    # Skip submissions that do not need regrading. All AUTOGRADE.txt files should be deleted whenever the autograder tests are changed to ensure that the new tests are applied to any already-autograded.
    if os.path.exists(os.path.join(thisDir, "AUTOGRADE.txt")):
        print("SKIPPING %s because it has already been autograded." % thisDir);
        continue

    # Set up the autograder
    ag = autograder.autograder("AUTOGRADE.txt", thisDir, totalPoints=pointTotal)
    submissionRoot = os.getcwd() #creating the autograder implicitly changes to a sandbox dir.


    for question in sorted(questions):
        questiondir = os.path.join(rubricRoot, question)
        ag.log_addEntry("=== Marking Question " + question + " ===")
        desiredFiles = open(os.path.join(questiondir,"requiredFiles")).read().splitlines()
        expectedExe = open(os.path.join(questiondir,"buildTargets")).read().splitlines()
        permittedFiles = open(os.path.join(questiondir,"allowedFiles")).read().splitlines()
        pointsForQuestion = int(open(os.path.join(rubricRoot, question, "points")).readline().split()[0])
        testlist = glob.glob(os.path.join(rubricRoot,question,"*.in.*"))
        pointsLeftAtStart = ag.getPointsLeft()

        ag.log_addEntry("=== Verifying Submitted Files ===")
        submissionQuestionDir = os.path.join(submissionRoot, question)
        if os.path.exists(submissionQuestionDir) and os.path.isdir(submissionQuestionDir):
            os.chdir(submissionQuestionDir) 
        else:
            ag.expect_file_all_of([question], pointsForQuestion)
            continue
        # Verify that the files are there that we are expecting and look for unexpected files.
        if not ag.expect_only_files(permittedFiles + ["AUTOGRADE*.txt", "AUTOGRADE.json"], pointsForQuestion):
            ag.log_addEntry("Unexpected file submitted. Submit only files " + " ".join(desiredFiles))
            continue
        if ag.find_unexpected_subdirectories([], pointsForQuestion):
            ag.log_addEntry("Unexpected subdirectoryies in submission.")
            continue
        if not ag.expect_file_all_of(desiredFiles, pointsForQuestion):
            ag.log_addEntry("Please submit all of: " + " ".join(desiredFiles))
            continue
        ag.log_addEntry("=== File Verification Successful ===")
        if len(expectedExe) > 0:
            ag.log_addEntry("=== Compiling Java to VM code ===")
            ag.javaCompile(desiredFiles)
            ag.log_addEntry("=== Compilation Successfull ===")

        for test in testlist:
            basefile = test.split(".")
            outfile = basefile[0]+".expect."+basefile[2]
            commandfile = basefile[0]+".command."+basefile[2]
            ag.log_addEntry("=== Running Test " + test + "===")
            ag.run_JavaStdoutMatch(open(commandfile).read(), stdindata=open(test).read(), stdouttarget = open(outfile).read(), deductTimeout=pointsForQuestion/len(testlist), deductWrongExit=pointsForQuestion/len(testlist), deductOutputMismatch=pointsForQuestion/2/len(testlist), timeout=15)

        pointsLeftAtEnd = ag.getPointsLeft()
        questionScore = pointsForQuestion - (pointsLeftAtStart - pointsLeftAtEnd)
        ag.log_addEntry("=== Score on Question " + question + ": " 
           + str(questionScore) + "/" + str(pointsForQuestion) + " ===")

    # Insert additional tests here!

    ag.cleanup()
