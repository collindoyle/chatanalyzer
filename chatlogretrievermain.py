import crawler
import time

limit = 100

if __name__ == "__main__":
    i = 0
    mycralwer = crawler.crawler()
    while i < limit:
        print(i)
        result = mycralwer.GetPage()
        time.sleep(30)
        i += result

        

    