import crawler
import time
import analyzer

limit = 200

if __name__ == "__main__":
    i = 0
    mycralwer = crawler.crawler()
    # myanalyzer = analyzer.analyzer()
    sleeptime = 60
    while i < limit:        
        result = mycralwer.GetPage()
        i += result
        print(i)
        if result == 0:
            sleeptime += 10
        else:
            # myanalyzer = analyzer.analyzer()
            # myanalyzer.ProcessLogs()
            # myanalyzer.RecognizeUser()
            sleeptime = 60
        print('Get Page again in ' + str(sleeptime) + ' seconds')
        time.sleep(sleeptime)

