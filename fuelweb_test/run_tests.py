def run_tests():
    from proboscis import TestProgram
    from integration import test_simple

    # Run Proboscis and exit.
    TestProgram().run_and_exit()

if __name__ == '__main__':
    run_tests()