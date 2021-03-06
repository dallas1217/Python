#!/usr/bin/env python
#-*- coding=utf-8 -*-

import urllib2
import json
import time
import threading
import os
import sys
import numpy as np
import csv
import smtplib
from email.MIMEText import MIMEText 
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders

class Json_code(threading.Thread):
    #初始化了一些需要的变量,预期端口和用户名密码之类的
    def __init__(self,argv):
        threading.Thread.__init__(self)
        self.port_list = [80,81,6080,8080,8088,443,1935,22,51999,843,7911,9394,19394,19999,161,53,21108 ,1989,10051,800]
        self._argv = argv
        self._time = time.strftime('%Y-%m-%d %H:%m')
        self.mailto_list=["xxx@163.com","xxxx@163.com"]
        self.mail_host="smtp.163.com" 
        self.mail_user="xxxx"
        self.mail_pass="xxxx"
        self.mail_postfix="163.com"
    
    #从接口获取数据,并进行json处理
    def Retrieve_data(self):
        _url = "https://xxxx.xxx.com/xxxx/ports?tags={}".format(self._argv)
        _headers = { 'API-KEY':'xxx','API-SECRET':'xxxxx','API-ID':'xxxxx'}
        _reques = urllib2.Request(url=_url,headers=_headers)
        _response = urllib2.urlopen(_reques)
        _result = _response.read()
        
        _data = json.loads(_result)
        #判断接口获取值为空就报警及退出
        if _data["data"]["list"]:
            return _data
        else:
            #t.Send_mail(self.mailto_list,self._argv+"接口异常","接口获取数据为空!")
            print self._argv+"ports接口异常,获取数据为空"
            sys.exit(3)

    #获取IP列表
    def Get_IP_List(self):
        _url = "https://xxxx.xxxx.com/outerapi/assets_list?tag={}".format(self._argv)
        _headers = { 'API-KEY':'xxxx','API-SECRET':'xxxx','API-ID':'xxxx'}
        _reques = urllib2.Request(url=_url,headers=_headers)
        _response = urllib2.urlopen(_reques)
        _result = _response.read()
        
        _data = json.loads(_result)
        #判断接口获取值为空就报警及退出
        if _data:
            return _data
        else:
            #self.Send_mail(self.mailto_list,self._argv+"接口异常","接口获取数据为空!")
            print self._argv+"assets_list接口异常,获取数据为空"
            sys.exit(3)

    #IP是否增加
    def Ip_alignment(self):
        Ip_list = []
        ip_list_def = self.Get_IP_List()["data"][0]["list"]
        ip_json = self.Retrieve_data()["data"]["list"]
        #测试IP增加的情况
        #ip_json["192.168.1.1"] = ["22","44"]
        Ip_list = [ip for ip in ip_json if np.in1d(ip,ip_list_def) == [False]]
        return Ip_list 
            

    #判断和预期值的差
    def Port_alignment(self):
        #最终结果字典
        dict_port = {}
        #调用Retrieve_data函数获取ip及对应端口列表
        self.new_json = self.Retrieve_data()["data"]["list"]
        for key,value in  self.new_json.items():
            _tmp = []
            for p in value:
                #如果端口在预计的列表里的话就pass
                if int(p) in self.port_list:
                    pass
                else:
                    #否则就扔到一个临时的列表里
                    _tmp.append(p)
            if _tmp:
            	#然后IP和对应端口进行组装
            	dict_port[key] = _tmp

        return dict_port

    #用来发送邮件            
    def Send_mail(self,to_list,sub, body, file_path, file_name):
        msg = MIMEMultipart()
        me="Tencent"+"<"+self.mail_user+"@"+self.mail_postfix+">"  
        #msg.MIMEText(content,_subtype='plain',_chars:et='utf-8') 
        body=MIMEText(body)
        msg.attach(body)
                
        part = MIMEBase('application', 'octet-stream')        
        part.set_payload(open(file_path,'rb').read())    
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename=%s' %file_name)
        msg.attach(part)

        msg["Accept-Language"]="zh-CN"
        msg["Accept-Charset"]="ISO-8859-1,utf-8" 
        msg['Subject'] = sub  
        msg['From'] = me  
        msg['To'] = ";".join(to_list) 

 
        try:  
            server = smtplib.SMTP_SSL()  
            server.connect(self.mail_host, port=465)  
            server.login(self.mail_user, self.mail_pass)  
            server.sendmail(me, to_list, msg.as_string())  
            server.close()  
            return True  
        except Exception as e:  
            print(str(e)) 
            return False 
    
    def Csv(self, file_path, mode, ip, port, status ):
        write_file = open(file_path+".csv",mode)
        write_csv = csv.writer(write_file)
        write_csv.writerow([ip, port, status])
        write_file.flush()
         
   
#继承Json_code父类
class Utils(Json_code):
    def __init__(self,argv):
        Json_code.__init__(self,argv)
        if os.path.exists("csv"):
            pass
        else:
            os.mkdir("csv")

    #将IP相关写入日志
    def Ip_count(self):
        ip_data = Json_code.Ip_alignment(self)
        _time = time.strftime('%Y-%m-%d')
        self.Csv("csv/"+self._argv+"-ip-"+_time,"w", "Ip", "Port", "Status")

        if ip_data:
            ip = ','.join(ip_data).encode('utf-8')
            self.Csv("csv/"+self._argv+"-ip-"+_time, "a", ip, "ignore", "increase") 

            self.Send_mail(self.mailto_list,"[ERR]"+self._argv+"[NEW IP]","IP related forms","csv/"+self._argv+"-ip-"+_time+".csv", self._argv+"-ip-"+_time+".csv")

    #将端口相关写入日志
    def Port_count(self):
        port_data = Json_code.Port_alignment(self)
        _time = time.strftime('%Y-%m-%d')
        self.Csv("csv/"+self._argv+"-port-"+_time, "w", "Ip", "Port", "Status")

        for k,v in port_data.items():
                v = [l.encode('utf-8') for l in v ]
                self.Csv("csv/"+self._argv+"-port-"+_time,"a",  k, v, "incompatible")
        self.Send_mail(self.mailto_list,"[ERR]"+self._argv+"[port error]","Does not meet the expected port","csv/"+self._argv+"-port-"+_time+".csv",self._argv+"-port-"+_time+".csv")
    
    #执行总体代码
    def run(self):
    	self.Ip_count()
        self.Port_count()
         
if __name__ == "__main__":
    argv = sys.argv[1]
    t = Utils(argv)
    t.start()
    for t in threading.enumerate(): 
        if t is threading.currentThread(): 
            continue
        t.join() 
