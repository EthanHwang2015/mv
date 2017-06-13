#encoding=utf8
import json
from bottle import route, default_app, request, static_file
import time
import datetime
import md5
import collections
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os
import ConfigParser
import hashlib
import traceback
import json
sys.path.append('/home/work/tools/libs')
from mongolib import Mongo
from esindex import ESIndex
from essearch import ESSearch, TransportError
import random
from im.usersig import gen_sig
import requests

from task import *

sys.path.append('/home/work/qcloudsms/demo/python')
import Qcloud.Sms.SmsSender as SmsSender

IMAGE_PATH = '/home/work/images/'
APPID = 1400023423

TASK_TXT = ['暂未接单', '接单,目前正在执行中', '已完成,等待确认付款', '已付款,等待评论', '对方已评价,等待你的评价','已发布,未付款','任务超时取消','任务手动取消','任务已删除']

def get_conf(section, key):
    conf = ConfigParser.ConfigParser()
    conf.read('service.conf')
    return conf.get(section, key)

def import_im(userid, name=None, icon=None):
    url = 'https://console.tim.qq.com/v4/im_open_login_svc/account_import?usersig=eJxljk1PhDAURff8CsJWY9pCEUzcSCZaMxODgo4rUqCtjQN0Svmaif9dxUnE*Lbn3Hfv0bJt20nWTxe0KJquNpmZFHPsK9sBzvkvVEqWGTWZq8t-kI1KapZRbpieIcQYIwCWjixZbSSXJ4OWlazhgrflezaX-DzwvtLI9ZC7VKSY4WaVRiSOSPfSsjghu0jfSsD302vYHRLAByGepxwhL*226JFzX8dErN-wQzGKw10uIO3hAFZD3NzkgdgRuvX3dOOp8fKsr*L79HpRaWTFToOCwA9B*GdQz3Qrm3oWEIAYIhd8n2N9WJ-wR15k&sdkappid=1400023423&identifier=admin1&random=99999999&contenttype=json'
    body = {}
    body['Identifier'] = userid
    if name is not None:
        body['Nick'] = name
    if icon is not None:
        body['FaceUrl'] = icon
    headers = {"Content-Type": "application/json"}
    r = requests.post(url, data=json.dumps(body), headers = headers, verify=False)
    msg = json.loads(r.text)
    print 'import_im' ,msg
    return msg['ErrorCode']

def update_im(userid, name=None, icon=None):
    url = 'https://console.tim.qq.com/v4/profile/portrait_set?usersig=eJxljk1PhDAURff8CsJWY9pCEUzcSCZaMxODgo4rUqCtjQN0Svmaif9dxUnE*Lbn3Hfv0bJt20nWTxe0KJquNpmZFHPsK9sBzvkvVEqWGTWZq8t-kI1KapZRbpieIcQYIwCWjixZbSSXJ4OWlazhgrflezaX-DzwvtLI9ZC7VKSY4WaVRiSOSPfSsjghu0jfSsD302vYHRLAByGepxwhL*226JFzX8dErN-wQzGKw10uIO3hAFZD3NzkgdgRuvX3dOOp8fKsr*L79HpRaWTFToOCwA9B*GdQz3Qrm3oWEIAYIhd8n2N9WJ-wR15k&identifier=admin1&sdkappid=1400023423&random=99999999&contenttype=json'
    body = {}
    body['From_Account'] = userid
    items = []
    if name is not None:
        items.append({'Tag':'Tag_Profile_IM_Nick', 'Value':name})
    if icon is not None:
        items.append({'Tag':'Tag_Profile_IM_Image', 'Value':icon})
    body['ProfileItem'] = items
    headers = {"Content-Type": "application/json"}
    print body
    r = requests.post(url, data=json.dumps(body), headers = headers, verify=False)
    msg = json.loads(r.text)
    return msg['ErrorCode']



@route('/')
def index():
    ret = {}
    sp = []
    sp.append('upload')
    sp.append('create_comment')
    sp.append('update_topic_comment')
    sp.append('search_comment')
    sp.append('del_topic_comment')
    sp.append('create_task')
    sp.append('update_task')
    sp.append('delete_task')
    sp.append('search_recv_task')
    sp.append('search_submit_task')
    sp.append('accept_task')
    sp.append('confirm_task')
    sp.append('task_status')
    sp.append('search_task_around')
    sp.append('skill')

    ret['support interfaces'] = sp
    return  ret
"""
#params process
"""

def VerifyArgs(request, args):
    for a in args:
        if a not in request.query:
            return a
    return None

def GetArgs(request, args):
    paramsDict = {}
    for a in args:
        paramsDict[a] = request.query.get(a)
    return paramsDict


def VerifyArgsPost(request, args, sn=True):
    ret = {}
    ret['status'] = -1
    ret['msg'] = '{} params required'
    print request.forms.allitems()
    for a in args:
        if a not in request.forms:
            ret['msg'] = '{} params required'.format(a)
            return ret
    if sn:
        sn_v = request.get_header('sn')
        allitems = sorted(request.forms.allitems(), key = lambda item:item[0])
        enc = ''
        for item in allitems:
            enc += '{}={}&'.format(item[0],item[1])
        enc = enc[0:len(enc)-1]
        print enc
        md = md5.new()
        md.update(enc)
        m = md.hexdigest()
        if sn_v is None:
            ret['msg'] = '{} params required'.format('sn')
            return ret
 
        print 'truth sn:{}'.format(m)
        if sn_v != m:
            ret['msg'] = 'sn validation falied'
            return ret

    return None

def GetArgsPost(request, args, sn=True):
    paramsDict = {}
    for a in args:
        paramsDict[a] = request.forms.get(a)

    return paramsDict

"""
#static files
"""

@route('/images/<filePath:path>')
def index(filePath):
    path = IMAGE_PATH + filePath
    print path
    return static_file(filePath, root=IMAGE_PATH)

@route('/skill')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'
 
    skills = []
    with open('skill.txt', 'r') as f:
        for l in f:
            skills.append(l.strip())
    ret['results'] = skills
    return ret

"""
#upload img
"""
@route('/upload', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'
    ret['url'] = ''

    args = ['userid']
    va = VerifyArgsPost(request, args, sn=False)
    if va is not None:
        return va
    params = GetArgsPost(request, args)
    try: 
        uploadfile=request.files.get('data')
        hstr = str(datetime.datetime.now()) + request.remote_addr
        hstr += uploadfile.filename 
        md5 = hashlib.md5()
        md5.update(hstr)
        uploadfile.filename = md5.hexdigest() + '.' +  uploadfile.filename.split('.')[-1]
        path = IMAGE_PATH + params['userid'] + '/'
        if not os.path.exists(path):
            os.makedirs(path)
        uploadfile.save(path, overwrite=True)
        ret['url'] = 'http://115.28.25.154:9090/images/{}/{}'.format(params['userid'], uploadfile.filename)
    except:
        ret['status'] = -1
        ret['msg'] = 'upload failed'
        print traceback.format_exc()

    return ret

"""
#comment interface
"""
@route('/create_comment', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['userid', 'relative_id', 'relative_type','content', 'comment_time', 'relative_comment_id']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)
    print params
    return  ret

@route('/update_topic_comment', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['comment_id', 'userid', 'content','comment_time']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)
    return ret

@route('/search_comment2', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['relative_id', 'relative_type']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va
    params = GetArgsPost(request, args)

    comments = {}
    comments['comment_id'] = '1234'
    comments['content'] = 'this is test comment'
    comments['userid'] = 'abc123'
    comments['comment_time'] = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
    comments['dest_userid'] = -1

    ret['results'] = []
    ret['results'].append(comments)
    comments['comment_id'] = '4567'
    comments['userid'] = 'abc4567'
    comments['dest_userid'] = 'abc123' 
    ret['results'].append(comments)
    return ret

@route('/del_topic_comment', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['comment_id', 'userid']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)
    return ret


"""
#task interface
"""

@route('/create_task', method='POST')
def index():
    #uploadfile=request.files.get('data')
    #uploadfile.filename
    #uploadfile.save(path, overwrite=True)
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    verify_args = ['userid', 'money', 'task_detail', 'start_location', 'start_location_name', 'province', 'citycode', 'adcode']#, 'gridcode']
    va = VerifyArgsPost(request, verify_args)
    if va is not None:
        return va
    args = ['userid', 'money', 'stop_time', 'task_detail', 'start_location', 'start_location_name', 'end_location', 'end_location_name', 'image_list', 'province', 'citycode', 'adcode', 'gridcode']
    params = GetArgsPost(request, args)
    params['publish_time'] = time.time()
    params['task_id'] = "{}_{}".format(params['userid'], params['publish_time'])
    #params['task_status'] = 0
    #已发布,未付款
    params['task_status'] = 5
    params['start_location_name'] = params['start_location_name'].decode('utf8')
    #params['end_location_name'] = params['end_location_name'].decode('utf8')
    params['task_detail'] = params['task_detail'].decode('utf8')

    params['creater_userid'] = params['userid']
    del params['userid']
        
    try:
        #check user,get user icon&username
        mongo = Mongo(db='mv', host='127.0.0.1', table='user')
        key = {'userid':params['creater_userid']}
        mongo_res = mongo.find(filter_ = key)
        if mongo_res.count() == 0 or 'icon' not in mongo_res[0] or 'user_name' not in mongo_res[0]:
            ret['status'] = -3
            ret['msg'] =  'userid not register'
            return ret
        params['creater_icon'] = mongo_res[0]['icon']
        params['creater_username'] = mongo_res[0]['user_name']

        #task
        key = {'_id':params['task_id']}
        value = {"$set": params}
        mongo = Mongo(db='mv', host='127.0.0.1', table='task')
        print value
        mongo_ret = mongo.update(key, value)
        print mongo_ret

        ###province,city,area
        key = {'_id':'{}_{}_{}'.format(params['province'].encode('utf8'), params['citycode'], params['adcode'])}
        #key = {'citycode':params['citycode'], 'adcode':params['adcode']}
        mongo = Mongo(db='mv', host='127.0.0.1', table='task_count')
        value = {"$inc": {"total":1}}
        mongo_ret = mongo.update(key, value)
        print mongo_ret
        ret['results'] = {'task_id':params['task_id']}

    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        print traceback.format_exc()
        return ret

    try:
        es = ESIndex('127.0.0.1:9200', '20170107', 'mv')
        es_ret = es.Index(params['task_id'], params)
        print es_ret

    except TransportError as err:
        ret['status']= err.status_code
        ret['msg'] = err.error
        print err

    return ret

#cancel_task之后调用
@route('/repost_task', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    verify_args = ['task_id','userid']
    va = VerifyArgsPost(request, verify_args)
    if va is not None:
        return va

    args = ['task_id', 'userid', 'money', 'stop_time', 'task_detail', 'start_location', 'start_location_name', 'end_location', 'end_location_name', 'image_list']
    params = GetArgsPost(request, args)

    params['creater_userid'] = params['userid']
    del params['userid']
 
    #等待接单
    params['task_status'] = 0
    params['publish_time'] = time.time()
    key = {'_id':params['task_id'], 'creater_userid':params['creater_userid'], 'task_id':params['task_id']}
    value = {"$set": params}
    try:
        mongo = Mongo(db='mv', host='127.0.0.1', table='task')
        if mongo.find(filter_ = key).count() == 0:
            ret['status'] = -2
            ret['msg'] = 'task not belong to this user'
            return ret

        mongo_ret = mongo.update(key, value)
        print mongo_ret
    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        print traceback.format_exc()

    try:
        
        filter_ = {'task_id':params['task_id']}
        mongo_ret = mongo.find(filter_ = filter_)
        for t in mongo_ret:
            es = ESIndex('127.0.0.1:9200', '20170107', 'mv')
            t.pop('_id', None)
            print json.dumps(t)
            es_ret = es.Index(params['task_id'], json.dumps(t))
            print es_ret
            break
    except TransportError as err:
        ret['status']= err.status_code
        ret['msg'] = err.error
        print traceback.format_exc()

    return ret



@route('/update_task', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    verify_args = ['task_id','userid']
    va = VerifyArgsPost(request, verify_args)
    if va is not None:
        return va

    args = ['task_id', 'userid', 'money', 'stop_time', 'task_detail', 'start_location', 'start_location_name', 'end_location', 'end_location_name', 'image_list']
    params = GetArgsPost(request, args)

    params['creater_userid'] = params['userid']
    del params['userid']
 
    #已发布,未付款
    params['task_status'] = 5
    params['publish_time'] = time.time()
    key = {'_id':params['task_id'], 'creater_userid':params['creater_userid'], 'task_id':params['task_id']}
    value = {"$set": params}
    try:
        mongo = Mongo(db='mv', host='127.0.0.1', table='task')
        if mongo.find(filter_ = key).count() == 0:
            ret['status'] = -2
            ret['msg'] = 'task not belong to this user'
            return ret

        mongo_ret = mongo.update(key, value)
        print mongo_ret
    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        print traceback.format_exc()

    try:
        
        filter_ = {'task_id':params['task_id']}
        mongo_ret = mongo.find(filter_ = filter_)
        for t in mongo_ret:
            es = ESIndex('127.0.0.1:9200', '20170107', 'mv')
            t.pop('_id', None)
            print json.dumps(t)
            es_ret = es.Index(params['task_id'], json.dumps(t))
            print es_ret
            break
    except TransportError as err:
        ret['status']= err.status_code
        ret['msg'] = err.error
        print traceback.format_exc()

    return ret

@route('/task_detail', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['userid', 'task_id']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)

    params['creater_userid'] = params['userid']
    del params['userid']
 
    filter_ = {'_id':params['task_id'], 'creater_userid':params['creater_userid'], 'task_id':params['task_id']}
    try:
        mongo = Mongo(db='mv', host='127.0.0.1', table='task')
        mongo_ret = mongo.find(filter_ = filter_)
        if mongo_ret.count() == 0:
            ret['status'] = -2
            ret['msg'] = 'task not belong to this user'
            return ret
        ret['results'] = mongo_ret[0]
    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        print traceback.format_exc()

    return ret

@route('/cancel_task', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['userid', 'task_id']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)

    params['creater_userid'] = params['userid']
    del params['userid']
 
    filter_ = {'_id':params['task_id'], 'creater_userid':params['creater_userid'], 'task_id':params['task_id']}
    try:
        mongo = Mongo(db='mv', host='127.0.0.1', table='task')
        if mongo.find(filter_ = filter_).count() == 0:
            ret['status'] = -2
            ret['msg'] = 'task not belong to this user'
            return ret

        key = {'_id':params['task_id'], 'creater_userid':params['creater_userid'], 'task_id':params['task_id']}
        #'任务手动取消'
        params['task_status'] = 7
        value = {"$set": params}
        mongo_ret = mongo.update(key, value)
        print mongo_ret
    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        print traceback.format_exc()

    try:
        es = ESIndex('127.0.0.1:9200', '20170107', 'mv')
        es_ret = es.delete(params['task_id'])
        print es_ret

    except TransportError as err:
        #ret['status']= err.status_code
        #ret['msg'] = err.error
        print traceback.format_exc()

    return ret


@route('/delete_task', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['userid', 'task_id']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)

    params['creater_userid'] = params['userid']
    del params['userid']
 
    filter_ = {'_id':params['task_id'], 'creater_userid':params['creater_userid'], 'task_id':params['task_id']}
    try:
        mongo = Mongo(db='mv', host='127.0.0.1', table='task')
        if mongo.find(filter_ = filter_).count() == 0:
            ret['status'] = -2
            ret['msg'] = 'task not belong to this user'
            return ret

        key = {'_id':params['task_id'], 'creater_userid':params['creater_userid'], 'task_id':params['task_id']}
        #'任务已删除'
        params['task_status'] = 8
        value = {"$set": params}
        mongo_ret = mongo.update(key, value)
        print mongo_ret
    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        print traceback.format_exc()

    try:
        es = ESIndex('127.0.0.1:9200', '20170107', 'mv')
        es_ret = es.delete(params['task_id'])
        print es_ret

    except TransportError as err:
        #ret['status']= err.status_code
        #ret['msg'] = err.error
        print traceback.format_exc()

    return ret

@route('/search_recv_task', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['userid', 'from', 'to']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)

    params['accepter_userid'] = params['userid']
    del params['userid']

    try:
        #查询任务表，取出我接单的所有任务
        filter_ = {'accepter_userid':params['accepter_userid']}
        mongo = Mongo(db='mv', host='127.0.0.1', table='task')
        mongo_ret = mongo.find(filter_ = filter_)
        tasks = []

        #取出我的个人信息
        u_key = {'userid':params['accepter_userid']}
        user_ret = mongo.find(filter_ = u_key, table='user')
        accepter = {}
        if user_ret.count() > 0:
            accepter['userid'] = user_ret[0]['userid']
            accepter['user_name'] = user_ret[0]['user_name']
            accepter['icon'] = user_ret[0]['icon']
            #取出我接到的每个任务中，创建者的信息
            for t in mongo_ret:
                u_key = {'userid':t['creater_userid']}
                creater_user_ret = mongo.find(filter_ = u_key, table='user')
                if user_ret.count() > 0:
                    t['creater_username'] = creater_user_ret[0]['user_name']
                    t['creater_usericon'] = creater_user_ret[0]['icon']
                    t['creater_userid'] = creater_user_ret[0]['userid']
                    t['accepter_userid'] = accepter['userid']
                    t['accepter_username'] = accepter['user_name']
                    t['accepter_usericon'] = accepter['icon']

                t['status_txt'] = TASK_TXT[int(t['task_status'])]
                tasks.append(t)

            ret['results'] = tasks
        else:
            ret['status'] = -1
            ret['msg'] = 'user not exists'
    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        print traceback.format_exc()
    return ret

@route('/search_submit_task', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['userid', 'from', 'to']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)
    params['creater_userid'] = params['userid']
    del params['userid']

    try:
        filter_ = {'creater_userid':params['creater_userid']}
        tasks = []
        mongo = Mongo(db='mv', host='127.0.0.1', table='task')
        mongo_ret = mongo.find(filter_ = filter_)
        for t in mongo_ret:
            if 'accepter_userid' in t:
                u_key = {'userid':t['accepter_userid']}
                user_ret = mongo.find(filter_ = u_key, table='user')
                if user_ret.count() > 0:
                    print type(user_ret[0])
                    print user_ret[0]
                    t['accepter_username'] = user_ret[0]['user_name']
                    t['accepter_usericon'] = user_ret[0]['icon']

            t['status_txt'] = TASK_TXT[int(t['task_status'])]
            tasks.append(t)
    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        print traceback.format_exc()

    ret['results'] = tasks

    return ret

@route('/accept_task', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['userid', 'task_id']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)

    params['accepter_userid'] = params['userid']
    del params['userid']


    key = {'task_id':params['task_id']}
    values = {'accepter_userid': params['accepter_userid'], 'task_status':1}
    value = {"$set": values}
    try:
        mongo = Mongo(db='mv', host='127.0.0.1', table='task')
        mongo_ret = mongo.update(key, value)
        print mongo_ret
    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        print traceback.format_exc()

    try:
        es = ESIndex('127.0.0.1:9200', '20170107', 'mv')
        es_ret = es.delete(params['task_id'])
        print es_ret

    except TransportError as err:
        #ret['status']= err.status_code
        #ret['msg'] = err.error
        print traceback.format_exc()

    return ret

@route('/confirm_task', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['userid', 'task_id']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)

    params['accepter_userid'] = params['userid']
    del params['userid']

    key = {'task_id':params['task_id'], 'accepter_userid':params['accepter_userid']}
    values = {'accepter_userid': params['accepter_userid'], 'task_status':2}
    value = {"$set": values}
    try:
        mongo = Mongo(db='mv', host='127.0.0.1', table='task')
        mongo_ret = mongo.update(key, value)
        print mongo_ret
    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        print traceback.format_exc()


    return ret

@route('/set_task_status', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['task_id', 'task_status']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)
    key = {'task_id':params['task_id']}
    value = {"$set": {'task_status':params['task_status']}}
    try:
        mongo = Mongo(db='mv', host='127.0.0.1', table='task')
        mongo_ret = mongo.update(key, value)
        print mongo_ret
    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        print traceback.format_exc()

    try:
        
        filter_ = {'task_id':params['task_id']}
        mongo_ret = mongo.find(filter_ = filter_)
        for t in mongo_ret:
            es = ESIndex('127.0.0.1:9200', '20170107', 'mv')
            t.pop('_id', None)
            t['task_status'] = params['task_status']
            print json.dumps(t)
            es_ret = es.Index(params['task_id'], json.dumps(t))
            print es_ret
            break
    except TransportError as err:
        ret['status']= err.status_code
        ret['msg'] = err.error
        print traceback.format_exc()



    return ret



@route('/task_status', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['userid', 'task_id']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)
    key = {'task_id':params['task_id']}
    try:
        mongo = Mongo(db='mv', host='127.0.0.1', table='task')
        mongo_ret = mongo.find(filter_ = key)
        if mongo_ret.count() > 0:
            s = mongo_ret[0]
            s['status_txt'] = TASK_TXT[int(s['task_status'])]
            #ret['results'] = {'task_status':s['task_status'], 'status_txt':s['status_txt']}
            ret['results'] = s
            #ret['status'] = s['task_status']
    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        print traceback.format_exc()

    return ret

@route('/recv_notify', method='POST')
def index():
    print request.forms
    return 'success'


@route('/recharge', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['userid', 'money']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)
 
    try:
        key = {'userid':params['userid'], '_id':params['userid']}
        value = {"$set": params}
        mongo = Mongo(db='mv', host='127.0.0.1', table='account')

    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        ret.pop('results', None)
        print traceback.format_exc()

    return ret

@route('/balance', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['userid']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)
 
    try:
        key = {'userid':params['userid']}
        mongo = Mongo(db='mv', host='127.0.0.1', table='account')
        mongo_ret = mongo.find(filter_ = key)
        if mongo_ret.count() > 0:
            money = mongo_ret[0]
            ret['results'] = {'money':money}
    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        ret.pop('results', None)
        print traceback.format_exc()

    return ret

#trade 
@route('/pay_task', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    #pay_type:0=余额, 1=支付宝, 2＝微信
    args = ['userid', 'task_id', 'pay_type', 'money']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)
    try:
        create_tm = time.time()
        md = md5.new()
        md.update('{}_{}_{}'.format(userid, task_id, create_tm))
        trade_no = '{}#{}'.format(userid, md.hexdigest())

        key = {'userid':params['userid'], '_id':params['userid']}
        value = {"$set": params}
        mongo = Mongo(db='mv', host='127.0.0.1', table='trade')

        results = {}
        results['trade_no'] = trade_no
        results['notify_url'] = 'http://115.28.25.154:9090/recv_notify'
        ret['results'] = results

    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        ret.pop('results', None)
        print traceback.format_exc()
    return ret
 

@route('/trade_history', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['userid', 'comment_id']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)
    try:
        pass
    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        ret.pop('results', None)
        print traceback.format_exc()

    return ret
 


@route('/search_task_count', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['userid', 'location', 'zoomLevel', 'province', 'citycode', 'adcode']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)
    radius = 20
    params['current_time'] = 0
    try:
        mongo = Mongo(db='mv', host='127.0.0.1', table='task_count')
        if params['zoomLevel'] == '0':
            mongo_res = mongo.find(filter_ = {})
            if mongo_res.count() > 0:
                results = {}
                for r in mongo_res:
                    if r['province'] not in results:
                        results[r['province']] = {}
                        results[r['province']]['province'] = r['province']
                        results[r['province']]['total'] = r['total']
                        results[r['province']]['location'] = r['p_center']
                    else:
                        results[r['province']]['total'] += r['total']
                ret['results'] = results.values()
        elif params['zoomLevel'] == '1':    
            mongo_res = mongo.find(filter_ = {'province':params['province']})
            if mongo_res.count() > 0:
                results = {}
                for r in mongo_res:
                    if r['citycode'] not in results:
                        results[r['citycode']] = {}
                        results[r['citycode']]['citycode'] = r['citycode']
                        results[r['citycode']]['total'] = r['total']
                        results[r['citycode']]['location'] = r['c_center']
                    else:
                        results[r['citycode']]['total'] += r['total']
                ret['results'] = results.values()
 
        elif params['zoomLevel'] == '2':    
            mongo_res = mongo.find(filter_ = {'province':params['province'], 'citycode':params['citycode']})
            if mongo_res.count() > 0:
                results = {}
                for r in mongo_res:
                    if r['adcode'] not in results:
                        results[r['adcode']] = {}
                        results[r['adcode']]['adcode'] = r['adcode']
                        results[r['adcode']]['total'] = r['total']
                        results[r['adcode']]['location'] = r['d_center']
                    else:
                        results[r['adcode']]['total'] += r['total']
                ret['results'] = results.values()

        elif params['zoomLevel'] == '3':    
                es = ESSearch('127.0.0.1:9200')
                index = '20170107'
                doc_type = 'mv'
                location = params['location']
                radius = 3
                start = 0
                to = 10
                aggs = es.search(index, doc_type, location, radius, 0, start=start, size=to-start, agg=True)
                #print aggs
                rets = []
                for key in aggs:
                    buckets = aggs[key]['buckets']
                    for bucket in buckets:
                        item = {}
                        item['areacode'] = bucket['key']
                        item['total'] = bucket['doc_count']
                        lat = (bucket['cell']['bounds']['top_left']['lat'] + bucket['cell']['bounds']['bottom_right']['lat'])/2
                        lon = (bucket['cell']['bounds']['top_left']['lon'] + bucket['cell']['bounds']['bottom_right']['lon'])/2
                        item['location'] = '{},{}'.format(lat,lon)
                        rets.append(item)
                ret['results'] = rets
            

    except TransportError as err:
        ret['status']= err.status_code
        ret['msg'] = err.error
        print err

    return ret 

@route('/search_task_around', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['userid', 'from','to', 'location', 'radius']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)

    radius = params['radius']
    params['current_time'] = 0
    try:
        es = ESSearch('127.0.0.1:9200')
        index = '20170107'
        doc_type = 'mv'
        start = int(params['from'])
        to = int(params['to'])
        total, es_ret = es.search(index, doc_type, params['location'], params['radius'], params['current_time'], start=start, size=to-start)
        ret['results'] = es_ret

    except TransportError as err:
        ret['status']= err.status_code
        ret['msg'] = err.error
        print err

    return ret


"""
#user login
"""

def send_idf(phone, idf, tm='15'):
    appid = 1400023423
    appkey = "0d5efc34640b340899eb8205c65f6e6c"    
    phone_number = "18611063680"
    templ_id = 9697

    single_sender = SmsSender.SmsSingleSender(appid, appkey)

    params = [idf, tm]
    result = single_sender.send_with_param("86", phone, templ_id, params, "", "", "")
    rsp = json.loads(result)
    return rsp

@route('/idfcode', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['tel']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)

    idfcode = random.randint(1000, 9999)

    key = {'tel':params['tel']}
    params['idfcode'] = idfcode
    value = {"$set": params}
    try:
        mongo = Mongo(db='mv', host='127.0.0.1', table='idfcode')
        mongo_ret = mongo.update(key, value)
        print mongo_ret
    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        print traceback.format_exc()

    #ret['results'] = {'idfcode':idfcode}
    if ret['status'] == 0:
        rsp = send_idf(params['tel'], str(idfcode))
        print rsp
    return ret


@route('/login', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['tel', 'idf_code','device_id']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)

    try:
        key = {'tel':params['tel']}
        idfcode = int(params['idf_code'])
        mongo = Mongo(db='mv', host='127.0.0.1', table='idfcode')
        mongo_res = mongo.find(filter_ = key)
        if mongo_res.count() == 0 or mongo_res[0]['idfcode'] != idfcode:
            ret['status'] = -1
            ret['msg'] = 'idfcode error'
            return ret

        mongo = Mongo(db='mv', host='127.0.0.1', table='user')
        key = {'tel':params['tel']}
        mongo_res = mongo.find(filter_ = key)
        if mongo_res.count() == 0:
            md = md5.new()
            md.update(params['tel']+params['idf_code'])
            userid = md.hexdigest()
            key = {'tel':params['tel']}
            valueDict = {}
            valueDict['tel'] = params['tel']
            valueDict['_id'] = userid
            valueDict['userid'] = userid
            #valueDict['passwd'] = params['device_id']
            valueDict['device_id'] = params['device_id']
            value = {"$set": valueDict}
            mongo.update(key, value)
            sig = gen_sig(userid, APPID)
            ret['results'] = {'userid':userid, 'iscomplete':0, 'usersig':sig}
        else:
            complete = 1
            print mongo_res[0]
            if 'identity_id' not in mongo_res[0] or 'icon' not in mongo_res[0] or 'card' not in mongo_res[0]:
                complete = 0
            userid = mongo_res[0]['userid']
            sig = gen_sig(userid, APPID)
            ret['results'] = {'userid': userid, 'iscomplete':complete, 'usersig':sig}
    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        ret.pop('results', None)
        print traceback.format_exc()

    return ret

@route('/register', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['tel', 'passwd', 'idf_code','device_id']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)

    try:
        key = {'tel':params['tel']}
        idfcode = int(params['idf_code'])
        mongo = Mongo(db='mv', host='127.0.0.1', table='idfcode')
        mongo_res = mongo.find(filter_ = key)
        for r in mongo_res:
            if idfcode != r['idfcode']:
                ret['status'] = -1
                ret['msg'] = 'idfcode error'
                return ret

        mongo = Mongo(db='mv', host='127.0.0.1', table='user')
        key = {'tel':params['tel']}
        mongo_res = mongo.find(filter_ = key)
        if  params['tel'] == mongo_res[0]['tel']:
            ret['status'] = -2
            ret['msg'] = 'user registered'
            return ret

        md = md5.new()
        md.update(params['tel']+params['passwd'])
        userid = md.hexdigest()
        key = {'tel':params['tel']}
        valueDict = {}
        valueDict['tel'] = params['tel']
        valueDict['_id'] = userid
        valueDict['userid'] = userid
        valueDict['passwd'] = params['device_id']
        valueDict['device_id'] = params['device_id']
        value = {"$set": valueDict}
        mongo_ret = mongo.update(key, value)
        ret['results'] = {'userid':userid}
        #print mongo_ret
    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        ret.pop('results', None)
        print traceback.format_exc()

    return ret
 
@route('/update_personal_detail', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    verify_args = ['userid', 'name', 'gender', 'nation', 'address', 'sinature']
    va = VerifyArgsPost(request, verify_args)
    if va is not None:
        return va

    args = ['userid', 'name', 'gender', 'nation', 'address', 'sinature']
    params = GetArgsPost(request, args)

    try:
        key = {'userid':params['userid']}
        value = {"$set": params}
        mongo = Mongo(db='mv', host='127.0.0.1', table='user')
        mongo_ret = mongo.update(key, value)

        sig = gen_sig(params['userid'], APPID)

        ret['usersig'] = sig

    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        ret.pop('results', None)
        print traceback.format_exc()

    return ret
 
@route('/update_personal', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    #verify_args = ['userid', 'user_name', 'skill', 'card', 'identity_type', 'identity_id', 'icon', 'wallpaper']
    verify_args = ['userid', 'user_name', 'skill', 'card', 'identity_type', 'identity_id']
    va = VerifyArgsPost(request, verify_args)
    if va is not None:
        return va

    #args = ['userid', 'user_name', 'skill', 'card', 'identity_type', 'identity_id', 'icon']
    args = ['userid', 'user_name', 'skill', 'card', 'identity_type', 'identity_id', 'icon', 'wallpaper']
    params = GetArgsPost(request, args)

    try:
        key = {'userid':params['userid']}
        value = {"$set": params}
        mongo = Mongo(db='mv', host='127.0.0.1', table='user')
        mongo_ret = mongo.update(key, value)

        import_im(params['userid'], name=params['user_name'], icon=params['icon'])

    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        ret.pop('results', None)
        print traceback.format_exc()

    return ret


@route('/get_userid_by_tel', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    verify_args = ['tel']
    va = VerifyArgsPost(request, verify_args)
    if va is not None:
        return va

    args = ['tel']
    params = GetArgsPost(request, args)
    try:
        key = {'tel':params['tel']}
        mongo = Mongo(db='mv', host='127.0.0.1', table='user')
        mongo_ret = mongo.find(filter_ = key)
        if mongo_ret.count() != 0:
            detail = {}
            needs = ['userid', 'name', 'icon']
            for n in needs:
                if n in mongo_ret[0]:
                    detail[n] = mongo_ret[0][n]
            ret['results'] = detail
    except:
        ret['status'] = -1
        ret['msg'] = 'read db failed'
        ret.pop('results', None)
        print traceback.format_exc()
    return ret
    
@route('/get_personal', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    verify_args = ['userid']
    va = VerifyArgsPost(request, verify_args)
    if va is not None:
        return va

    args = ['userid']
    params = GetArgsPost(request, args)
    try:
        key = {'userid':params['userid']}
        mongo = Mongo(db='mv', host='127.0.0.1', table='user')
        mongo_ret = mongo.find(filter_ = key)
        if mongo_ret.count() != 0:
            ret['results'] = mongo_ret[0]
    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        ret.pop('results', None)
        print traceback.format_exc()
    return ret
"""
#comment
"""
@route('/create_comment', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['userid', 'task_id', 'dest_userid','content', 'comment_time', 'parent_id']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)
    try:
        md = md5.new()
        md.update(params['userid']+params['task_id']+params['dest_userid']+params['parent_id']+params['comment_time'])
        comment_id = md.hexdigest()
        params['comment_id'] = comment_id

        key = {'_id':comment_id}
        value = {"$set": params}
 
        mongo = Mongo(db='mv', host='127.0.0.1', table='comment')
        mongo.update(key, value)
    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        ret.pop('results', None)
        print traceback.format_exc()

    return ret
@route('/update_comment', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['comment_id', 'userid', 'content', 'comment_time']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)
    try:

        key = {'_id':params['comment_id'], 'userid':params['userid']}
        value = {"$set": params}
 
        mongo = Mongo(db='mv', host='127.0.0.1', table='comment')
        mongo.update(key, value)
    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        ret.pop('results', None)
        print traceback.format_exc()
    return ret

@route('/search_comment', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['task_id']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)
    try:

        key = {'task_id':params['task_id'], 'parent_id':'-1', 'dest_userid':'-1'}
 
        mongo = Mongo(db='mv', host='127.0.0.1', table='comment')
        mongo_ret = mongo.find(filter_ = key)
        comments = []
        for p in mongo_ret:
            comment_id = p['comment_id']
            sub_comment = []
            u_key = {'userid':p['userid']}
            user_ret = mongo.find(filter_ = u_key, table='user')
            if user_ret.count() > 0:
                p['user_name'] = user_ret[0]['user_name']
                p['user_icon'] = user_ret[0]['icon']
            #sub_comment.append(p)
            comments.append(p)
            key = {'task_id':params['task_id'], 'parent_id':comment_id}
            sub_ret = mongo.find(filter_ = key, table='comment')
            for s in sub_ret:
                u_key = {'userid':s['userid']}
                user_ret = mongo.find(filter_ = u_key, table='user')
                if user_ret.count() > 0:
                    s['user_name'] = user_ret[0]['user_name']
                    s['user_icon'] = user_ret[0]['icon']
                u_key = {'userid':s['dest_userid']}
                user_ret = mongo.find(filter_ = u_key, table='user')
                if user_ret.count() > 0:
                    s['dest_user_name'] = user_ret[0]['user_name']
                    s['dest_user_icon'] = user_ret[0]['icon']
                #sub_comment.append(s)
                comments.append(s)
            #comments.append(sub_comment)
        ret['results'] = comments
        print comments
    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        ret.pop('results', None)
        print traceback.format_exc()

    return ret
 


@route('/delete_comment', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['userid', 'comment_id']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)
    try:
        key = {'_id':params['comment_id'], 'userid':params['userid']}
        mongo = Mongo(db='mv', host='127.0.0.1', table='comment')
        if mongo.find(filter_ = key).count() == 0:
            ret['status'] = -2
            ret['msg'] = 'comment not belong to this user'
            return ret

        mongo_ret = mongo.delete(filter_ = key)
    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
        ret.pop('results', None)
        print traceback.format_exc()

    return ret
 
application = default_app()

