import analyzer
import sys
import getopt

def main(argv):
    try:
        opts, args = getopt.getopt(argv, '', ['raw','rel'])
    except getopt.GetoptError:
        print('error')
        sys.exit(2)
    myanalyzer = analyzer.analyzer()
    for opt, arg in opts:
        if opt == '--raw':
            print('Processing log data')
            myanalyzer.ProcessLogs()
        elif opt == '--rel':
            print('Processing user data')
            myanalyzer.RecognizeUser()

if __name__ == "__main__":
    print(sys.argv)    
    main(sys.argv[1:])