# -*- coding: utf-8 -*-
from qqbot import qqbotsched
from qqbot.utf8logger import DEBUG, INFO, ERROR
import time
import random

from config_reader import ConfigReader
from pocket48_handler import Pocket48Handler
from qqhandler import QQHandler

import global_config

pocket48_handler = None
qq_handler = None


def onInit(bot):
    # 初始化时被调用
    # 注意 : 此时 bot 尚未启动，因此请勿在本函数中调用 bot.List/SendTo/GroupXXX/Stop/Restart 等接口
    #       只可以访问配置信息 bot.conf
    # bot : QQBot 对象
    DEBUG('%s.onInit', __name__)


def onQrcode(bot, pngPath, pngContent):
    # 获取到二维码时被调用
    # 注意 : 此时 bot 尚未启动，因此请勿在本函数中调用 bot.List/SendTo/GroupXXX/Stop/Restart 等接口
    #       只可以访问配置信息 bot.conf
    # bot : QQBot 对象
    # pngPath : 二维码图片路径
    # pngContent : 二维码图片内容
    DEBUG('%s.onQrcode: %s (%d bytes)', __name__, pngPath, len(pngContent))


def onQQMessage(bot, contact, member, content):
    # 当收到 QQ 消息时被调用
    # bot     : QQBot 对象，提供 List/SendTo/GroupXXX/Stop/Restart 等接口，详见文档第五节
    # contact : QContact 对象，消息的发送者
    # member  : QContact 对象，仅当本消息为 群或讨论组 消息时有效，代表实际发消息的成员
    # content : str 对象，消息内容
    DEBUG('member: %s', str(getattr(member, 'uin')))
    # DEBUG('content: %s', content)
    # DEBUG('contact: %s', contact.ctype)

    if contact.ctype == 'group' and contact.qq in global_config.AUTO_REPLY_GROUPS:
        if content.startswith('-'):  # 以'-'开头才能触发自动回复
            if '@ME' in content:  # 在群中@机器人
                bot.SendTo(contact, member.name + '，' + random_str(global_config.AT_AUTO_REPLY))
            elif content == '-version':
                bot.SendTo(contact, 'QQbot-' + bot.conf.version)
            elif content == global_config.MEMBER_ATTR:  # 群消息输入成员缩写
                bot.SendTo(contact, random_str(global_config.I_LOVE))
            elif content in global_config.JIZI_KEYWORDS:  # 集资链接
                jizi_link = '\n'.join(global_config.JIZI_LINK)
                bot.SendTo(contact, '集资链接: %s' % jizi_link)
            elif content in global_config.WEIBO_KEYWORDS:  # 微博关键词
                weibo_link = global_config.WEIBO_LINK
                super_tag = global_config.SUPER_TAG
                bot.SendTo(contact, '微博: %s\n超级话题: %s' % (weibo_link, super_tag))
            elif content in global_config.GONGYAN_KEYWORDS:  # 公演关键词
                live_link = '\n'.join(global_config.LIVE_LINK)
                # strs = ConfigReader.get_property('profile', 'live_schedule').split(';')
                live_schedule = '\n'.join(global_config.LIVE_SCHEDULE)
                msg = '直播传送门: %s\n本周安排: %s' % (live_link, live_schedule)
                bot.SendTo(contact, msg)
            elif content in ['-统计']:
                histogram = ConfigReader.get_property('profile', 'histogram')
                msg = '公演统计链接: %s' % histogram
                bot.SendTo(contact, msg)
            else:  # 无法识别命令
                no_such_command = ConfigReader.get_property('profile', 'no_such_command')
                bot.SendTo(contact, no_such_command)


def onInterval(bot):
    # 每隔 5 分钟被调用
    # bot : QQBot 对象，提供 List/SendTo/GroupXXX/Stop/Restart 等接口，详见文档第五节
    DEBUG('%s.onInterval', __name__)


def onStartupComplete(bot):
    # 启动完成时被调用
    # bot : QQBot 对象，提供 List/SendTo/GroupXXX/Stop/Restart 等接口，详见文档第五节
    DEBUG('%s.onStartupComplete', __name__)
    global qq_handler, pocket48_handler

    # 先更新配置
    update_conf(bot)

    # 初始化QQHandler并更新联系人
    qq_handler = QQHandler()
    qq_handler.update()

    # 读取配置文件中的群号，进行处理，转化为QContact对象
    auto_reply_groups = qq_handler.list_group(global_config.AUTO_REPLY_GROUPS)
    member_room_msg_groups = qq_handler.list_group(global_config.MEMBER_ROOM_MSG_GROUPS)
    member_room_comment_groups = qq_handler.list_group(global_config.MEMBER_ROOM_COMMENT_GROUPS)

    pocket48_handler = Pocket48Handler(auto_reply_groups, member_room_msg_groups,
                                       member_room_comment_groups)


def onUpdate(bot, tinfo):
    # 某个联系人列表更新时被调用
    # bot : QQBot 对象，提供 List/SendTo/GroupXXX/Stop/Restart 等接口，详见文档第五节
    # tinfo : 联系人列表的代号，详见文档中关于 bot.List 的第一个参数的含义解释
    DEBUG('%s.onUpdate: %s', __name__, tinfo)


def onPlug(bot):
    # 本插件被加载时被调用，提供 List/SendTo/GroupXXX/Stop/Restart 等接口，详见文档第五节
    # 提醒：如果本插件设置为启动时自动加载，则本函数将延迟到登录完成后被调用
    # bot ： QQBot 对象
    DEBUG('%s.onPlug', __name__)


def onUnplug(bot):
    # 本插件被卸载时被调用
    # bot ： QQBot 对象，提供 List/SendTo/GroupXXX/Stop/Restart 等接口，详见文档第五节
    DEBUG('%s.onUnplug', __name__)


def onExit(bot, code, reason, error):
    # MainLoop（主循环）终止时被调用， Mainloop 是一个无限循环，QQBot 登录成功后便开始运
    # 行，当且仅当以下事件发生时 Mainloop 终止：
    #     1） 调用了 bot.Stop() ，此时：
    #         code = 0, reason = 'stop', error = None
    #     2） 调用了 bot.Restart() ，此时：
    #         code = 201, reason = 'restart', error = None
    #     3） 调用了 bot.FreshRestart() ，此时：
    #         code = 202, reason = 'fresh-restart', error = None
    #     4） 调用了 sys.exit(x) （ x 不等于 0,201,202,203 ），此时：
    #         code = x, reason = 'system-exit', error = None
    #     5） 登录的 cookie 已过期，此时：
    #         code = 203, reason = 'login-expire', error = None
    #     6） 发生未知错误 e （暂未出现过，出现则表明 qqbot 程序内部可能存在错误），此时：
    #         code = 1, reason = 'unknown-error', error = e
    #
    # 一般情况下：
    #     发生 1/2/3/4 时，可以安全的调用 bot.List/SendTo/GroupXXX 等接口
    #     发生 5/6 时，调用 bot.List/SendTo/GroupXXX 等接口将出错
    #
    # 一般情况下，用户插件内的代码和运行错误会被捕捉并忽略，不会引起 MainLoop 的退出
    #
    # 本函数被调用后，会执行 sys.exit(code) 退出本次进程并返回到父进程，父进程会根据
    # “ code 的数值” 以及 “是否配置为自动重启模式” 来决定是否重启 QQBot 。
    #

    DEBUG('%s.onExit: %r %r %r', __name__, code, reason, error)


def onExpire(bot):
    # 登录过期时被调用
    # 注意 : 此时登录已过期，因此请勿在本函数中调用 bot.List/SendTo/GroupXXX/Stop/Restart 等接口
    #       只可以访问配置信息 bot.conf
    # bot : QQBot 对象
    DEBUG('ON-EXPIRE')


def random_str(strs):
    return random.choice(strs)


@qqbotsched(hour='10')
def restart_sche(bot):
    DEBUG('RESTART scheduled')
    bot.FreshRestart()


@qqbotsched(minute='*/30')
def update_conf(bot):
    """
    每隔1分钟读取配置文件
    :param bot:
    :return:
    """
    DEBUG('读取配置文件')
    global_config.AUTO_REPLY_GROUPS = ConfigReader.get_property('qq_conf', 'auto_reply_groups').split(';')
    global_config.MEMBER_ROOM_MSG_GROUPS = ConfigReader.get_property('qq_conf', 'member_room_msg_groups').split(';')
    global_config.MEMBER_ROOM_COMMENT_GROUPS = ConfigReader.get_property('qq_conf', 'member_room_comment_groups').split(';')

    member_name = ConfigReader.get_property('root', 'member_name')
    global_config.ROOM_ID = ConfigReader.get_member_room_number(member_name)

    global_config.JIZI_KEYWORDS = ConfigReader.get_property('profile', 'jizi_keywords').split(';')
    global_config.JIZI_LINK = ConfigReader.get_property('profile', 'jizi_link').split(';')

    global_config.WEIBO_KEYWORDS = ConfigReader.get_property('profile', 'weibo_keywords').split(';')
    global_config.GONGYAN_KEYWORDS = ConfigReader.get_property('profile', 'gongyan_keywords').split(';')
    global_config.LIVE_LINK=ConfigReader.get_property('profile', 'live_link').split(';')
    global_config.LIVE_SCHEDULE = ConfigReader.get_property('profile', 'live_schedule').split(';')

    global_config.WEIBO_LINK = ConfigReader.get_property('profile', 'weibo_link')
    global_config.SUPER_TAG = ConfigReader.get_property('profile', 'super_tag')

    global_config.MEMBER_ATTR = ConfigReader.get_property('profile', 'member_attr')
    global_config.I_LOVE = ConfigReader.get_property('profile', 'i_love').split(';')

    global_config.AT_AUTO_REPLY = ConfigReader.get_property('profile', 'at_auto_reply').split(';')


@qqbotsched(second='*/30')
def get_room_msgs(bot):
    global qq_handler, pocket48_handler

    r1 = pocket48_handler.get_member_room_msg(global_config.ROOM_ID)
    pocket48_handler.parse_room_msg(r1)
    r2 = pocket48_handler.get_member_room_comment(global_config.ROOM_ID)
    pocket48_handler.parse_room_msg(r2)

    timestamp = min(pocket48_handler.last_monitor_time + 30, int(time.time()))
    if pocket48_handler.last_monitor_time + 60 <= int(time.time()):
        timestamp = int(time.time())
    pocket48_handler.last_monitor_time = timestamp

