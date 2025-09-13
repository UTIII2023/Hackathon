from imports import *

class Information:
    data_set = numpy.array([])
    def __init__(self, url):
        self.url = url
        self.response = requests.get(url)
        self.content = BeautifulSoup(self.response.content, "html.parser")
        Information.pull_info(self.url, self.content, self.response)

    @classmethod
    def pull_info(cls, url, content, class_tag):
        content_div = content.find("div", class_=input(f"{content}\nEnter the class name of the div you want to extract text from: \n"))
        if content_div:
            text = content_div.get_text(strip=True)
            numpy.append(cls.data_set, text)
            print("added into the dataset")

        else:
            print("Content not found")        