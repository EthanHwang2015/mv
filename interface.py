#encoding=utf8
import json
from bottle import route, default_app, request
import time
import datetime
import md5
import collections

@route('/')
def index():
    ret = {}
    sp = []
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
    sp.append('cofirm_task')
    sp.append('task_status')
    sp.append('search_task_around')

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

    if sn:
        sn_v = request.get_header('sn')
        js = json.dumps(request.orderedPost)
        md = md5.new()
        md.update(js)
        m = md.hexdigest()
        print m
        if sn_v is None:
            ret['msg'].format('sn')
            return ret
 
        print sn_v, m
        if sn_v != m:
            ret['msg'] = 'sn validation falied'
            return ret

    for a in args:
        if a not in request.forms:
            ret['msg'].format(a)
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

@route('<dirname>/<filename>')
def index(dirname, filename):
    path = '/tmp/' + dirname
    return static_file(filename, root=path)

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
@route('/search_comment', method='POST')
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
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['userid', 'money', 'publish_time','stop_time', 'task_detail', 'start_location', 'start_location_name', 'end_location', 'end_location_name', 'image_list']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)
    return ret

@route('/update_task', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['task_id','userid', 'money', 'publish_time','stop_time', 'task_detail', 'start_location', 'start_location_name', 'end_location', 'end_location_name', 'image_list']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va
    params = GetArgsPost(request, args)

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

    task= {}
    task['task_id'] = '1234'
    task['dest_userid'] = 'abc123'
    task['user_icon'] = 'http://abc123'
    task['money'] = 99
    task['publish_time'] = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
    task['stop_time_time'] = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
    task['task_detail'] = 'this a test task'
    task['start_location'] = '116.374841,116.374841'
    task['start_location_name'] = '新街口外大街23号院'
    task['end_location'] = '116.351844,39.920866'
    task['end_location_name'] = '北京市西城区三里河东路8号'
    task['task_status'] = 1
    task['image_list'] = ['http://1.png', 'http://2.png']

    tasks = []
    tasks.append(task)
    task['task_id'] = '456'
    task['dest_userid'] = 'abc456'
    task['user_icon'] = 'http://abc456'
    task['money'] = 199
    tasks.append(task)
 
    ret['results'] = tasks

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

    task= {}
    task['task_id'] = '1234'
    task['dest_userid'] = 'abc123'
    task['user_icon'] = 'http://abc123'
    task['money'] = 99
    task['publish_time'] = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
    task['stop_time_time'] = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
    task['task_detail'] = 'this a test task'
    task['start_location'] = '116.374841,116.374841'
    task['start_location_name'] = '新街口外大街23号院'
    task['end_location'] = '116.351844,39.920866'
    task['end_location_name'] = '北京市西城区三里河东路8号'
    task['task_status'] = 1
    task['image_list'] = ['http://1.png', 'http://2.png']

    tasks = []
    tasks.append(task)
    task['task_id'] = '456'
    task['dest_userid'] = 'abc456'
    task['user_icon'] = 'http://abc456'
    task['money'] = 199
    tasks.append(task)
 
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

    return ret

@route('/cofirm_task', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['userid', 'task_id']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

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

    ret['results'] = {}
    ret['results']['task_status'] = 0

    return ret

@route('/search_task_around', method='POST')
def index():
    ret = {}
    ret['status'] = 0
    ret['msg'] = 'ok'

    args = ['userid', 'current_time', 'from','to', 'location', 'radius']
    va = VerifyArgsPost(request, args)
    if va is not None:
        return va

    params = GetArgsPost(request, args)

    task= {}
    task['task_id'] = '1234'
    task['dest_userid'] = 'abc123'
    task['user_icon'] = 'http://abc123'
    task['money'] = 99
    task['publish_time'] = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
    task['stop_time_time'] = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
    task['task_detail'] = 'this a test task'
    task['start_location'] = '116.374841,116.374841'
    task['start_location_name'] = '新街口外大街23号院'
    task['end_location'] = '116.351844,39.920866'
    task['end_location_name'] = '北京市西城区三里河东路8号'
    task['task_status'] = 1
    task['image_list'] = ['http://1.png', 'http://2.png']

    tasks = []
    tasks.append(task)
    task['task_id'] = '456'
    task['dest_userid'] = 'abc456'
    task['user_icon'] = 'http://abc456'
    task['money'] = 199
    tasks.append(task)
 
    ret['results'] = tasks

    return ret



application = default_app()

