import sys
from junitparser import JUnitXml

xml = JUnitXml.fromfile(sys.argv[1])
tests = 0
failures = 0
for suite in xml:
    tests += suite.tests
    failures += suite.failures
if tests == 0:
    print(0)
else:
    print(round(((tests-failures)/tests)*100, 2))