import datetime
import random
import sys
import pymysql
import requests


# 连接数据库
def Coonect():
    conn = pymysql.connect(
        host='localhost',
        user='task',
        password='123456',
        db='task',
        charset='utf8',
        autocommit=True,  # 如果插入数据，， 是否自动提交? 和conn.commit()功能一致。
        cursorclass=pymysql.cursors.DictCursor  # 返回时获取字段值
    )
    return conn


# 获取用户信息
def Getusers(conn):
    cur = conn.cursor()
    select_sql = "select * from nytdsign"
    cur.execute(select_sql)
    users = cur.fetchall()
    cur.close()
    return users


#  更新用户信息
def Updatedb(conn, type, info, data=None):
    cur = conn.cursor()
    if type == 0:  # 更新数据
        update_sql = 'update nytdsign set data= "' + data + '" where id="' + str(info['id']) + '";'
        cur.execute(update_sql)
    if type == 1:  # 获取姓名
        update_sql = 'update nytdsign set username= "' + Gologin(user['userid'], user['phoneid'])['data']['name'] + '" where id="' + str(info['id']) + '";'
        cur.execute(update_sql)
    if type == 2:  # 关闭打卡，更新数据
        if user['state'] == 1:
            update_sql = "update nytdsign set state=0 where id=" + str(info['id']) + ";"
            cur.execute(update_sql)
            update_sql = 'update nytdsign set data= "' + data + '" where id="' + str(info['id']) + '";'
            cur.execute(update_sql)
    cur.close()


# 登录
def Gologin(userid, phoneid):
    loginapi = "http://fyxt.nytdc.edu.cn:12078/api/login?mobile=" + phoneid + "&code=" + userid + "&openid=&dguid=61"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36"
    }
    loginfo = requests.get(url=loginapi, headers=headers).json()
    return loginfo


# 签到
def Gosign(usertoken):
    signapi = "http://fyxt.nytdc.edu.cn:12078/tApi/postCheckin"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36",
        "x-user-token": usertoken
    }
    signdata = {
        "date": Currdate(),  # 当前日期
        "ishubei": "否",  # 本人是否为中、高风险地区人员
        "fromWhere": "江苏省扬州市邗江区",  # 当前居住地
        "province": "江苏省",  # 当前居住省
        "city": "扬州市",  # 当前居住市
        "county": "邗江区",  # 当前居住区
        "tempnum1": randnum(),  # 早间体温
        "tempnum2": randnum(),  # 午间体温
        "tempnum3": randnum(),  # 晚间体温
        "isgohubei": "否",  # 14天内去过中、高风险地区
        "iscontacthubei": "否",  # 14天内是否接触过中、高风险地区人员
        "iscontactpatient": "否",  # 14天内是否接触确诊或疑似病人
        "istemp": "否",  # 是否有发热、咳嗽、乏力等症状
        "isfamilypatient": "否",  # 是否有家庭成员或亲戚朋友被隔离
        "isabroad": "否",  # 14天内接触过境外归国人员
        "isfamilyhubei": "正常",  # 共同居住人身体状况
    }
    signinfo = requests.post(url=signapi, data=signdata, headers=headers).json()
    return signinfo, signdata


# 随机体温 36.0~36.7
def randnum():
    num = random.randint(360, 368)
    num = float(num) / 10
    return num


# 获取当前日期
def Currdate():
    data = str(datetime.date.today())
    return data


if __name__ == '__main__':
    coon = Coonect()
    users = Getusers(coon)
    for user in users:
        userid = user['userid']
        phoneid = user['phoneid']
        data = user['data']
        loginfo = Gologin(userid, phoneid)
        if user['state'] == 1:
            if loginfo['code'] == 0:
                usertoken = loginfo['data']['token']
                if not user['username']:
                    Updatedb(coon, 1, user)
                signinfo, signdata = Gosign(usertoken)
                if signinfo['code'] == 0:
                    if data:
                        data += "," + str(signdata)
                        Updatedb(coon, 0, user, data)
                    else:
                        data = str(signdata)
                        Updatedb(coon, 0, user, data)
                    # print(userid + username + "打卡成功" + str(signdata))
                else:
                    if data:
                        data += ",{'date':'" + Currdate() + "','message':'打卡失败!!!'}"
                        Updatedb(coon, 0, user, data)
                    else:
                        data = "{'date':'" + Currdate() + "','message':'打卡失败!!!'}"
                        Updatedb(coon, 0, user, data)
                    # print(userid + username + "打卡失败!!!")
            else:
                if data:
                    data += ",{'date':'" + Currdate() + "','message':'登录失败!!!'}"
                    Updatedb(coon, 2, user, data)
                else:
                    data = "{'date':'" + Currdate() + "','message':'登录失败!!!'}"
                    Updatedb(coon, 2, user, data)
                # print(userid + username + "打卡失败!!!")
                # print(userid + "登录失败!!!")
    coon.close()
sys.exit(0)
