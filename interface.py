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

sys.path.append('/home/work/qcloudsms/demo/python')
import Qcloud.Sms.SmsSender as SmsSender

IMAGE_PATH = '/home/work/images/'

def get_conf(section, key):
    conf = ConfigParser.ConfigParser()
    conf.read('service.conf')
    return conf.get(section, key)


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
TASK_TXT = ['暂未接单', '接单,目前正在执行中', '已完成,等待确认付款', '已付款,等待评论', '对方已评价,等待你的评价']

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
    params['task_status'] = 0
    params['start_location_name'] = params['start_location_name'].decode('utf8')
    #params['end_location_name'] = params['end_location_name'].decode('utf8')
    params['task_detail'] = params['task_detail'].decode('utf8')
        
    try:
        #check user,get user icon&username
        mongo = Mongo(db='mv', host='127.0.0.1', table='user')
        key = {'userid':params['userid']}
        mongo_res = mongo.find(filter_ = key)
        if mongo_res.count() == 0 or 'icon' not in mongo_res[0] or 'user_name' not in mongo_res[0]:
            ret['status'] = -3
            ret['msg'] =  'userid not register'
            return ret
        params['icon'] = mongo_res[0]['icon']
        params['user_name'] = mongo_res[0]['user_name']

        #task
        key = {'_id':params['task_id']}
        value = {"$set": params}
        mongo = Mongo(db='mv', host='127.0.0.1', table='task')
        print value
        mongo_ret = mongo.update(key, value)
        print mongo_ret

        ###province,city,area
        key = {'_id':'{}_{}_{}'.format(params['province'], params['citycode'], params['adcode'])}
        mongo = Mongo(db='mv', host='127.0.0.1', table='task_count')
        mongo_res = mongo.find(filter_ = key)
        if mongo_res.count() == 0:
            values = {}
            values['location'] = params['start_location']
            values['province'] = params['province']
            values['citycode'] = params['citycode']
            values['adcode'] = params['adcode']
            values['total'] = 1
            value = {"$set": values}
            mongo_ret = mongo.update(key, value)
        else:
            value = {"$inc": {"total":1}}
            mongo_ret = mongo.update(key, value)
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

    params['task_status'] = 0
    params['publish_time'] = time.time()
    key = {'_id':params['task_id'], 'userid':params['userid'], 'task_id':params['task_id']}
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

    filter_ = {'_id':params['task_id'], 'userid':params['userid'], 'task_id':params['task_id']}
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

    filter_ = {'_id':params['task_id'], 'userid':params['userid'], 'task_id':params['task_id']}
    try:
        mongo = Mongo(db='mv', host='127.0.0.1', table='task')
        if mongo.find(filter_ = filter_).count() == 0:
            ret['status'] = -2
            ret['msg'] = 'task not belong to this user'
            return ret


        mongo_ret = mongo.delete(filter_ = filter_)
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
        ret['status']= err.status_code
        ret['msg'] = err.error
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

    try:
        filter_ = {'dest_userid':params['userid']}
        mongo = Mongo(db='mv', host='127.0.0.1', table='task')
        mongo_ret = mongo.find(filter_ = filter_)
        tasks = []

        u_key = {'userid':params['userid']}
        user_ret = mongo.find(filter_ = u_key, table='user')
        src = {}
        if user_ret.count() > 0:
            src['userid'] = user_ret[0]['userid']
            src['user_name'] = user_ret[0]['user_name']
            src['icon'] = user_ret[0]['icon']

            for t in mongo_ret:
                u_key = {'userid':t['userid']}
                user_ret = mongo.find(filter_ = u_key, table='user')
                if user_ret.count() > 0:
                    t['dest_username'] = user_ret[0]['user_name']
                    t['dest_usericon'] = user_ret[0]['icon']
                    t['dest_userid'] = user_ret[0]['userid']
                    t['user_id'] = src['userid']
                    t['user_name'] = src['user_name']
                    t['icon'] = src['icon']

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

    try:
        filter_ = {'userid':params['userid']}
        tasks = []
        mongo = Mongo(db='mv', host='127.0.0.1', table='task')
        mongo_ret = mongo.find(filter_ = filter_)
        for t in mongo_ret:
            if 'dest_userid' in t:
                u_key = {'userid':t['dest_userid']}
                user_ret = mongo.find(filter_ = u_key, table='user')
                if user_ret.count() > 0:
                    print type(user_ret[0])
                    print user_ret[0]
                    t['dest_username'] = user_ret[0]['user_name']
                    t['dest_usericon'] = user_ret[0]['icon']

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
    key = {'task_id':params['task_id']}
    values = {'dest_userid': params['userid'], 'task_status':1}
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
        ret['status']= err.status_code
        ret['msg'] = err.error
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
    key = {'task_id':params['task_id'], 'dest_userid':params['userid']}
    values = {'dest_userid': params['userid'], 'task_status':2}
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

@route('/task_status', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['userid', 'task_id']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    key = {'task_id':params['task_id']}
    try:
        mongo = Mongo(db='mv', host='127.0.0.1', table='task')
        mongo_ret = mongo.find(filter_ = key)
        if mongo_ret.count() > 0:
            s = mongo_ret[0]
            s['status_txt'] = TASK_TXT[int(s['task_status'])]
            ret['results'] = json.dumps(s)
    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
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
                        results[r['province']]['location'] = r['location']
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
                        results[r['citycode']]['location'] = r['location']
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
                        results[r['adcode']]['location'] = r['location']
                    else:
                        results[r['adcode']]['total'] += r['total']
                ret['results'] = results.values()
 
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
            ret['results'] = {'userid':userid, 'iscomplete':0}
        else:
            complete = 1
            print mongo_res[0]
            if 'identity_id' not in mongo_res[0] or 'icon' not in mongo_res[0] or 'card' not in mongo_res[0]:
                complete = 0
            ret['results'] = {'userid': mongo_res[0]['userid'], 'iscomplete':complete}
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

    except:
        ret['status'] = -1
        ret['msg'] = 'write db failed'
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

