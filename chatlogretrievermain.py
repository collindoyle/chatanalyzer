import crawler
import time

limit = 1000

if __name__ == "__main__":
    i = 0
    mycralwer = crawler.crawler()
    while i < limit:
        print(i)
        mycralwer.GetPage()
        time.sleep(30)
        i += 1

        

    