import html.parser


class ipqueryparser(html.parser.HTMLParser):    
    def __init__(self):
        super(ipqueryparser, self).__init__()
        self.datalist = list()
        self.neednextdata = False

    def handle_starttag(self, tag, attrs):        
        print("Encountered a start tag:", tag)
        if tag == 'td':
            self.neednextdata = True
        
    def handle_endtag(self, tag):
        print("Encountered an end tag :", tag)
        if tag == 'td':
            self.neednextdata = False

    def handle_data(self, data):
        print("Encountered some data  :", data)
        if self.neednextdata:
            self.datalist.append(data)

    def feed(self, data):
        self.datalist.clear()
        super(ipqueryparser,self).feed(data)



