# coding:utf-8
#----配置文件------

GithubToken = "" #GITHUBAPITOKEN
PerPageLimit = 50 #每页条数
THREAD_COUNT = 5 #GitHub有限制不建议太大
TIMEOUT = 20 #超时时间


InformationRegex = {"mail" : r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",
                    "domain" : r"(http[s]*://[^<|\"|?]*)",
                    "pass1" : r"(pass[^<|?]{30})",
                    "pass2" : r"(password[^<|?]{30})",
                    "pass3" : r"(pwd[^<|?]{30})",
                    "root" : r"(root[^<|?]{0,30})",
                    "title" : r"<title>(.*)<\/title>",
                    "ip" : r"([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:*[0-9]{0,5})"}
