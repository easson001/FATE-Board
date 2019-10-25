# -*- coding: utf-8 -*-

# @Time     : 2018/11/20 14:33
# @Author   : tongtaozhu@tencent.com
# @FileName : bean.py

from CommMysql_local import CommMysql
import time
import copy


class Action(object):
    def __init__(self, logtime, logtype, activity_name, ui_name, input_content=None, time_cost=0):
        self.__logtime = logtime
        self.__logtype = logtype
        self.__activity_name = activity_name
        self.__ui_name = ui_name
        self.__input_content = input_content
        self.__time_cost = time_cost


class Custom(object):
    def __init__(self, guid=None, model=None, connect_network_type=None):
        self.__actions = list()
        self.__guid = guid
        self.__model = model
        self.__connect_network_type = connect_network_type

    def set_guid(self, guid):
        self.__guid = guid

    def get_guid(self):
        return self.__guid

    def get_connect_network_type(self):
        return self.__connect_network_type

    def set_connect_network_type(self, connect_network_type):
        self.__connect_network_type = connect_network_type

    def set_model(self, model):
        self.__model = model

    def get_model(self):
        return self.__model

    def set_action(self, action):
        self.__actions.append(action)

    guid = property(get_guid, set_guid)
    model = property(get_model, set_model)
    connect_network_type = property(get_connect_network_type, set_connect_network_type)

    def insert_to_db(self, demo):
        logline_dist_list = []  #批量入库提供写入效率
        for action in self.__actions:
            logline_dist={}
            logline_dist['guid'] = self.__guid
            logline_dist['model'] = self.__model
            logline_dist['connect_network_type'] = self.__connect_network_type
            logline_dist['logtype'] = action._Action__logtype
            logline_dist['activity_name'] = action._Action__activity_name
            logline_dist['ui_name'] = action._Action__ui_name
            logline_dist['input_content'] = action._Action__input_content
            logline_dist['logtime'] = action._Action__logtime
            logline_dist['time_cost'] = action._Action__time_cost
            logline_dist_list.append(logline_dist)
        if len(logline_dist_list) != 0:
            demo.insertMultiData('yyb_user_action', logline_dist_list)
            demo.commitData()

    def find_uiname_for_show(self):
        for action in self.__actions:
            if action._Action__logtype=='show':
                show_index = self.__actions.index(action)
                previous_action = self.__actions[show_index - 1]  #获取show日志的前一条日志
                if previous_action._Action__logtype=='click':
                    show_logtime = action._Action__logtime
                    click_logtime = previous_action._Action__logtime
                    time_offset = time.mktime(show_logtime.timetuple())- time.mktime(click_logtime.timetuple()) #先转化为绝对时间再相减
                    time_offset_mic = show_logtime.microsecond - click_logtime.microsecond  #获取毫秒级时间查
                    time_offset = time_offset + float(time_offset_mic)/1000000
                    if time_offset<1:  #如果和click日志和show日志时间差小于1秒就包click日志的ui_name给show日志的ui_name赋值
                        action._Action__ui_name = previous_action._Action__ui_name

    def optimize_uiname_for_show(self):
        activity_uiname_dist = {}
        for action in self.__actions:
            if action._Action__logtype == 'show':
                if action._Action__ui_name != '返回':
                    activity_uiname_dist[action._Action__activity_name] = action._Action__ui_name  #保存一个动态更新的activity跟ui_name的对照表
                elif activity_uiname_dist.has_key(action._Action__activity_name):
                    action._Action__ui_name = activity_uiname_dist[action._Action__activity_name]  #将ui_name为“返回”的show消息替换为有意义的ui_name

    def optimize_uiname_for_MainActivity(self):
        cur_MainActivity_name = '首页'
        for action in self.__actions:
            if action._Action__logtype == 'click':
                if action._Action__activity_name == 'android.widget.ImageView':
                    cur_MainActivity_name = action._Action__ui_name
                    add_show_action = copy.copy(action)  #新增一条MainActivity的show日志。人为让主界面的不同tab页面记录为不同的界面.如果不用copy 而用“=”，add_show_action和action会指向同一个变量
                    add_show_action._Action__logtype = 'show'
                    add_show_action._Action__activity_name = 'com.tencent.assistantv2.activity.MainActivity'
                    click_index = self.__actions.index(action)
                    self.__actions.insert((click_index + 1), add_show_action)
            elif action._Action__logtype == 'show':
                if action._Action__activity_name == 'com.tencent.assistantv2.activity.MainActivity':
                    action._Action__ui_name = cur_MainActivity_name

    def chinese_name(self, action, activity_ui_dist):
        #global activity_ui_dist
        activity_name_ch = action._Action__activity_name
        if activity_ui_dist.has_key(action._Action__activity_name):  # 将activity_name转换为更短，更易读的中文名
            activity_name_ch = activity_ui_dist[action._Action__activity_name]
        else:
            print action._Action__activity_name
        return activity_name_ch

    def get_activity_name_opt(self, action, activity_ui_dist):
        activity_name_ch = self.chinese_name(action, activity_ui_dist)
        activity_name_opt = activity_name_ch
        if action._Action__ui_name!='':  #在能获取到前一条click消息的名字时，将其作为show消息的备注
            activity_name_opt = "%s(%s)" % (activity_name_ch, action._Action__ui_name)
        return activity_name_opt

    def optimize_uiname_for_appLaunch(self, activity_ui_dist):
        '''
        为每条appLaunch日志组装一条有show日志拼装成的ui_name
        :param demo: 要查询对照表的数据库
        '''
        activity_list = []
        for action in reversed(self.__actions):
            if action._Action__logtype == 'show':  #将show日志的中文名装入list
                activity_name_opt = self.get_activity_name_opt(action, activity_ui_dist)
                activity_list.append(activity_name_opt)
            elif action._Action__logtype == 'response':
                action._Action__ui_name = '->'.join(reversed(activity_list))  #将list转换为str，存入appLaunch日志的ui_name字段
                if len(action._Action__ui_name)>1000:
                    action._Action__ui_name = 'more than 1000 Bit'


    def calc_timeCost(self, log_type):
        begin_time = 0
        end_time = 0
        found_end_action = 0
        for action in reversed(self.__actions):
            if found_end_action==0:
                end_time = action._Action__logtime
                found_end_action = 1
            if found_end_action==1:
                if action._Action__logtype==log_type:
                    begin_time = action._Action__logtime
                    time_cost = time.mktime(end_time.timetuple()) - time.mktime(begin_time.timetuple())   #先转化为绝对时间再相减
                    action._Action__time_cost = time_cost
                    found_end_action = 0

    def calc_launched_timeCost(self):
        '''
        本函数计算用户每次启动应用宝使用时长
        '''
        self.calc_timeCost('response')

    def calc_page_timeCost(self):
        '''
        本函数计算用户在应用宝的当前页面停留时长
        '''
        self.calc_timeCost('show')

