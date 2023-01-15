#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ctypes
import getopt
import os
import platform
import shutil
import sys
import time
import traceback

import inquirer
import requests

from lib.common import clear_dict, is_admin
from lib.frozen_dir import resource_path
from lib.json_file_operate import JsonFileOperate
from lib.ping import ping3
from lib.printer import printer
from lib.python_hosts import Hosts, HostsEntry
from lib.python_hosts import is_ipv4, is_ipv6
from lib.thread_pool import ThreadPoolManger

DEBUG = False

TITLE = 'wft'
APPNAME = 'WarframeTools'
VERSION = '1.1.0'
STATEMENT = '仅供学习使用，请勿用于非法用途'

# 版权
TITLE_CR = f'{APPNAME} v{VERSION}        Copyright (c) 2022 Lkeme'
ECHO_CR = f'欢迎使用: {APPNAME} 版本: {VERSION} 通知: {STATEMENT}'
ADD_ECHO_CR = f'自用版本 Copyright (c) 2022 Lkeme'  # None
PROJECT_CR = f'开源项目地址 https://github.com/lkeme/WarframeTools'

# 全局记录
GLOBAL_RESULTS = {}

# setting windows title
ctypes.windll.kernel32.SetConsoleTitleW(TITLE_CR)
os.system('chcp 65001 > NUL')


# boot
def boot() -> bool:
    if platform.system() != 'Windows':
        printer('当前只支持Windows系统', 'boot', 'red')
        return False
    printer(ECHO_CR, TITLE, 'yellow')
    if ADD_ECHO_CR is not None:
        printer(ADD_ECHO_CR, TITLE, 'yellow')
        printer(PROJECT_CR, TITLE, 'yellow')
    # printer(ECHO_CR, TITLE, 'magenta')
    # printer(ECHO_CR, TITLE, 'blue')
    # printer(ECHO_CR, TITLE, 'red')
    # printer(ECHO_CR, TITLE, 'green')
    # printer(ECHO_CR, TITLE, 'cyan')
    return True


# over
def over():
    # printer("Press 'D' to exit...")
    # while True:
    #     if ord(msvcrt.getch()) in [68, 100]:
    #         break
    os.system("pause >nul | set /p =请按任意键退出")
    sys.exit(0)


# 读取资源文件
def reader_wf_data(mode: str, force: bool = True) -> list:
    off_resources = reader_offline_wf_data()
    # 强制
    if not force:
        on_resources = reader_online_wf_data()
        if on_resources and off_resources:
            # 对比版本号
            if on_resources['VERSION'] > off_resources['VERSION']:
                printer('在线资源较新，使用在线资源文件', 'reader_wf_data', 'green')
                resources = on_resources
            else:
                printer('离线资源较新，使用离线资源文件', 'reader_wf_data', 'green')
                resources = off_resources
        else:
            printer('将使用离线资源文件', 'reader_wf_data', 'green')
            resources = off_resources
    else:
        printer('将使用离线资源文件', 'reader_wf_data', 'green')
        resources = off_resources

    wf = resources['warframe']
    maps = []
    for w in wf:
        if w['mode'] == mode:
            maps.append(w)
    return maps


# 读取在线资源文件
def reader_online_wf_data() -> dict:
    try:
        # dogfight360/UsbEAm/master/Usbeam/usbeam_new_20.xml
        url = 'https://ghproxy.com/https://raw.githubusercontent.com/lkeme/WarframeTools/main/data/WarframeIP.json'
        resources = requests.get(url, timeout=5).json()
        printer('读取在线资源文件成功', 'reader_online_wf_data', 'green')
        return resources
    except Exception as e:
        printer('拉取在线资源文件失败', 'reader_online_wf_data', 'red')
        return {}


# 读取离线资源文件
def reader_offline_wf_data() -> dict:
    resources = JsonFileOperate(
        filepath=resource_path('data'), filename='WarframeIP.json'
    ).operation_file()
    printer('拉取离线资源文件成功', 'reader_offline_wf_data', 'green')
    return resources


# 实现 ping 主机/ip
def ping(name: str, domain: str, addr: str, count=4):
    dst_addr = ''
    results = []  # 取值平均值
    for i in range(0, count):
        dst_addr, times = ping3(addr, i)
        if times > 0:
            # printer(f"<- 来自 {addr} 的回复: 字节=32 时间={int(times * 1000)}ms", 'ping3', 'green')
            printer(f"From {domain} [{dst_addr}] Reply 字节=32 时间={int(times * 1000)}ms", 'ping3', 'green')
            # time.sleep(0.7)
            results.append(int(times * 1000))
        elif times == -111:
            printer(f"From {domain} [{dst_addr}] Reply 字节=32 Invalid IP address.", 'ping3', 'red')
        else:
            # printer(f"<- 来自 {addr} 的回复: 字节=32 请求超时.", 'ping3', 'red')
            printer(f"From {domain} [{dst_addr}] Reply 字节=32 请求超时.", 'ping3', 'green')
    # return
    if len(results) == 0:
        return None
    else:
        return {
            "name": name,
            "domain": domain,
            "addr": dst_addr if dst_addr else domain,
            'times': int(sum(results) / len(results))
        }


# get hosts path
def get_root_hosts():
    default = '{}/Windows/System32/drivers/etc/hosts'
    return default.format(os.environ['SystemDrive'])


# backup hosts
def backup() -> bool:
    rh = get_root_hosts()
    if not os.path.exists('./hosts.bak'):
        shutil.copyfile(rh, './hosts.bak')
        printer('首次运行,备份hosts文件成功', 'backup', 'green')
        return True
    else:
        return False


# restore hosts
def restore_backup() -> bool:
    if not os.path.exists('./hosts.bak'):
        printer('未找到可用的备份文件', 'restore_backup', 'red')
        return False
    rh = get_root_hosts()
    if os.path.exists(rh):
        shutil.copyfile('./hosts.bak', rh)
        printer('还原hosts文件成功', 'restore_backup', 'green')
        return True
    else:
        printer('还原hosts文件失败', 'restore_backup', 'red')
        return False


# 模式
def pattern(mode: str) -> list:
    # 第一次备份
    backup()
    # 读取资源文件
    resources = reader_wf_data(mode)
    # 两次结果
    one_hosts, two_hosts = [], []
    #
    for resource in resources:
        printer(f"开始检测: {resource['name']} 节点有效数量: {len(resource['addresses'])}", 'pattern', 'cyan')
        # 创建线程池
        repeat = []
        thread_pool = ThreadPoolManger(25)
        for addr in resource['addresses']:
            # 是否重复
            if addr in GLOBAL_RESULTS.keys():
                repeat.append({"name": resource['name'], 'domain': resource['domain_name'], 'addr': addr,
                               'times': GLOBAL_RESULTS[addr]})
                continue
            thread_pool.add_job(ping, *(resource['name'], resource['domain_name'], addr, 1))
        # 整合过滤
        results = clear_dict(thread_pool.wait_finish())
        # 重复
        results = results + repeat
        # 排序
        results = sorted(results, key=lambda x: x['times'], reverse=False)
        # 添加全局节点
        for result in results:
            GLOBAL_RESULTS[result['addr']] = result['times']
        # 保留两次结果
        one_hosts.append(results[0])
        two_hosts.append(results[1])

    #
    print('\n')
    for index, hosts in enumerate([one_hosts, two_hosts]):
        print(f'第{index + 1}结果')
        for r in hosts:
            printer(f"domain: {r['domain']} ip: {r['addr']} ping: {r['times']}ms", 'pattern', 'blue')
    #
    print('\n')
    choice = input('选择你需要的结果(1/2): ')
    if choice not in ['1', '2']:
        hosts = one_hosts
        printer('选择错误,默认使用第1结果', 'pattern', 'red')
    else:
        hosts = {'1': one_hosts, '2': two_hosts}[choice]
        printer(f'选择成功,使用第{choice}结果', 'pattern', 'green')

    printer('所有测试结果: \n', 'pattern', 'white')
    for h in hosts:
        printer(f"{h['addr']} {h['domain']}", 'pattern', 'blue')
    return hosts


# 写入并刷新DNS
def write_hosts(hosts: Hosts):
    hosts.write()
    os.popen("ipconfig /flushdns", 'r')


# 获取实体
def get_hosts_entries(address, names, comment):
    if is_ipv4(address):
        return HostsEntry(entry_type='ipv4', address=address, names=names, comment=comment)
    elif is_ipv6(address):
        return HostsEntry(entry_type='ipv6', address=address, names=names, comment=comment)
    else:
        raise ValueError("Invalid Entry Type")


# 游戏加速模式
def normal(mode='normal'):
    results = pattern(mode)
    #
    if input('是否设置到Hosts文件(y/n): ') not in ['y', 'Y']:
        return
    # 开始写入
    hosts = Hosts(path=get_root_hosts())

    entry_list = []
    for r in results:
        # 先删除
        hosts.remove_all_matching(name=r['domain'])
        # 后写入
        entry_list.append(get_hosts_entries(address=r['addr'], names=[r['domain']], comment=r['name']))
    hosts.add(entry_list)
    write_hosts(hosts)
    printer("设置游戏加速模式完成", 'normal', 'green')


# 下载更新模式
def update(mode='update'):
    results = pattern(mode)
    #
    if input('是否设置到Hosts文件(y/n): ') not in ['y', 'Y']:
        return
    # 开始写入
    hosts = Hosts(path=get_root_hosts())
    # 保存逻辑
    domains = ['content.warframe.com', 'arbiter.warframe.com', 'origin.warframe.com', 'api.warframe.com']
    entry_backup = []
    for domain in domains:
        r = hosts.find_all_matching(name=domain)
        if not r:
            continue
        entry_backup += r
        hosts.remove_all_matching(name=domain)

    # 写入逻辑
    entry_list = []
    for r in results:
        # 写入
        entry_list.append(get_hosts_entries(address=r['addr'], names=[r['domain']], comment=r['name']))
    hosts.add(entry_list)
    write_hosts(hosts)
    printer("设置下载更新模式完成", 'update', 'green')
    # 恢复逻辑
    printer("请使用该规则后记得清除恢复，否则将导致可能无法登录等错误", 'update', 'green')
    if input('是否已结束使用(y/n: )') not in ['y', 'Y']:
        return
    # 删除
    for r in results:
        hosts.remove_all_matching(name=r['domain'])
    write_hosts(hosts)
    #
    if not entry_backup:
        # 如果不存在备份就打印
        printer("删除加速模式完成", 'update', 'green')
    else:
        # 如果存在备份就恢复
        hosts.add(entry_backup)
        write_hosts(hosts)
        printer("恢复加速模式完成", 'update', 'green')
    results = pattern(mode)
    #
    if input('是否设置到Hosts文件(y/n): ') not in ['y', 'Y']:
        return
    # 开始写入
    hosts = Hosts(path=get_root_hosts())

    entry_list = []
    for r in results:
        # 先删除
        hosts.remove_all_matching(name=r['domain'])
        # 后写入
        entry_list.append(get_hosts_entries(address=r['addr'], names=[r['domain']], comment=r['name']))
    hosts.add(entry_list)
    write_hosts(hosts)
    printer("设置游戏加速模式完成", 'normal', 'green')


# WarframeMarket加速模式
def market(mode='market'):
    results = pattern(mode)
    #
    if input('是否设置到Hosts文件(y/n): ') not in ['y', 'Y']:
        return
    # 开始写入
    hosts = Hosts(path=get_root_hosts())

    entry_list = []
    for r in results:
        # 先删除
        hosts.remove_all_matching(name=r['domain'])
        # 后写入
        entry_list.append(get_hosts_entries(address=r['addr'], names=[r['domain']], comment=r['name']))
    hosts.add(entry_list)
    write_hosts(hosts)
    printer('设置WarframeMarket加速模式完成', 'market', 'green')


# 重置模式
def reset():
    #
    if input('是否要清除所有已应用的加速节点(y/n): ') not in ['y', 'Y']:
        return
    # 开始写入
    hosts = Hosts(path=get_root_hosts())
    # 保存逻辑
    domains = ['content.warframe.com', 'arbiter.warframe.com', 'origin.warframe.com', 'api.warframe.com',
               'warframe.market', 'api.warframe.market']
    for domain in domains:
        hosts.remove_all_matching(name=domain)
    write_hosts(hosts)
    printer("重置加速模式完成", 'reset', 'green')


# 错误的模式选项
def error():
    printer('错误的模式选项', 'error', 'red')


# 操作
def operator(actions: dict, action: str):
    method = actions.get(action, error)
    if method:
        method()


# 交互
def interactive():
    actions = {
        '(1) 游戏加速模式': normal,
        '(2) 下载更新模式': update,
        '(3) WarframeMarket加速模式': market,
        '(4) 重置加速模式': reset,
        '(5) 恢复备份Hosts文件': restore_backup,
        '(6) 退出': sys.exit,
    }
    questions = [
        inquirer.List(
            'action', message="需要执行什么模式?",
            choices=actions.keys(),
        ),
    ]
    answers = inquirer.prompt(questions)
    operator(actions, answers['action'])


def opt():
    opts, args = getopt.getopt(sys.argv[1:], '-h-v-d', ['help', 'version', 'debug'])
    for opt_name, opt_value in opts:
        if opt_name in ('-h', '--help'):
            printer(ECHO_CR, 'Help', 'magenta')
            over()
        if opt_name in ('-v', '--version'):
            printer(VERSION, 'Version', 'magenta')
            over()
        if opt_name in ('-d', '--debug'):
            global DEBUG
            DEBUG = True
            printer('当前使用调试模式', 'Help', 'magenta')


if __name__ == "__main__":
    opt()
    try:
        # print(resource_path(os.path.join('data', 'WarframeIP.json')))
        start_time = time.time()
        #
        if boot() and (True if DEBUG else is_admin()):
            interactive()
        else:
            printer("请使用管理员权限运行脚本", TITLE, 'red')
            printer("鼠标右键 ”以管理员身份运行”", TITLE, 'red')
        #
        end_time = time.time()
        printer("耗时: {:.2f}秒".format(end_time - start_time), TITLE, 'blue')
        over()
    except KeyboardInterrupt:
        print('\n')
        printer("用户中断强制退出", TITLE, 'red')
        sys.exit(0)
    except Exception as e:
        if DEBUG:
            printer(f'出现全局错误: {e} 发生行数: {traceback.format_exc()}', TITLE, 'red')
        else:
            printer(f'出现全局错误: {e}', TITLE, 'red')
        printer(f'请记录错误并联系作者哦', TITLE, 'red')
        time.sleep(60)
        sys.exit(0)
