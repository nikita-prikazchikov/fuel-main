def run_tests():
    from proboscis import TestProgram
    from tests import test_simple

    # Run Proboscis and exit.
    TestProgram().run_and_exit()

if __name__ == '__main__':
    run_tests()
