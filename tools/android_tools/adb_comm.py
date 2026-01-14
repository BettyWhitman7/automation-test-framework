from tools.communication.cmd_comm import call_cmd
from subprocess import Popen
import uuid

import re
import time
import traceback


class ADB:
    def __init__(self, device):
        self._deviceName = device

    def connect(self, deviceName):
        """
        连接设备
        :param deviceName: android手机的序列号或ip:port
        :return: true:连接成功，false:连接失败
        """
        self._deviceName = deviceName
        connectInfo = call_cmd("adb connect " + deviceName)

        return connectInfo.find("connected to %s" % deviceName) != -1, connectInfo

    def power_off(self):
        """
        关闭设备
        """
        cmd = f'adb -s {self._deviceName} shell reboot -p'
        Popen(cmd)

    def reboot(self):
        """
        重启设备
        """
        cmd = f'adb -s {self._deviceName} shell reboot'
        Popen(cmd)

    def click_volume_add(self):
        """
        点击增加音量按钮
        """
        cmd = 'adb -s {} shell input keyevent 24'.format(self._deviceName)
        return call_cmd(cmd)

    def click_volume_sub(self):
        """
        点击减小音量按钮
        """
        cmd = 'adb -s {} shell input keyevent 25'.format(self._deviceName)
        return call_cmd(cmd)

    def get_alarm_media_volume(self):
        """
        获取闹钟音量信息
        """
        return self.__get_media_volume('alarm')

    def get_system_media_volume(self):
        """
        获取系统音量信息
        """
        return self.__get_media_volume('system')

    @staticmethod
    def get_system_volume_music_headphone(d_name):
        cmd = 'adb -s {} shell settings get system volume_music_headphone'.format(d_name)
        result = call_cmd(cmd).strip()
        if result == "null":
            return call_cmd(cmd).strip()
        return result

    def get_music_media_volume(self):
        """
        获取音乐音量信息
        """
        return self.__get_media_volume('music')

    def get_tel_ring_media_volume(self):
        """
        获取手机铃声信息
        """
        return self.__get_media_volume('ring')

    def set_system_volume(self, volume):
        """
        设置系统音量大小
        """
        self.__set_media_volume('system', volume)

    def set_ring_volume(self, volume):
        """
        设置响铃音量大小
        """
        self.__set_media_volume('ring', volume)

    def set_alarm_volume(self, volume):
        """
        设置闹钟音量大小
        """
        self.__set_media_volume('alarm', volume)

    def set_music_volume(self, volume):
        """
        设置音乐音量大小
        """
        self.__set_media_volume('music', volume)

    def is_app_installed(self, appPackage: str):
        """
        手机上指定的app是否已经安装
        :param appPackage: app包的packge
        :return: true:已安装，false:未安装
        """
        cmd = 'adb -s {} shell pm list packages -3|findstr {}'.format(self._deviceName, appPackage)
        return call_cmd(cmd).replace(' ', '') != ''

    def install_apk(self, path):
        """
        安装安装包
        :param path: apk历经
        :return:
        """
        cmd = 'adb -s {} install -r {}'.format(self._deviceName, path)
        return call_cmd(cmd)

    def uninstall_apk(self, appPackage: str):
        """
        卸载指定的程序
        :param appPackage: app包的packge
        :return: true:卸载成功，false:卸载失败
        """
        cmd = 'adb -s {} uninstall {}'.format(self._deviceName, appPackage)
        if self.is_app_installed(appPackage):
            return call_cmd(cmd).find('Success') != -1

    def clear_cache(self, package):
        cmd = f'adb -s {self._deviceName} shell pm clear {package}'
        return call_cmd(cmd)

    def uninstall_uiautomator2_server(self):
        """
        卸载appium server
        """
        cmd = 'adb -s {}  uninstall io.appium.uiautomator2.server'.format(self._deviceName)
        return call_cmd(cmd).find('Success') != -1

    def uninstall_uiautomator2_server_test(self):
        """
        卸载appium server test
        adb  uninstall io.appium.uiautomator2.server.test
        """
        cmd = 'adb -s {}  uninstall io.appium.uiautomator2.server.test'.format(self._deviceName)
        return call_cmd(cmd).find('Success') != -1

    def open_camera_permission(self, apkpath):
        """
        打开应用拍照权限
        """
        cmd = 'adb -s %s -d shell pm grant %s android.permission.CAMERA' % (self._deviceName, self.get_package(apkpath))
        return call_cmd(cmd)

    def open_callphone_permission(self, apkpath):
        """
        打开应用拨打电话权限
        """
        cmd = 'adb -s %s -d shell pm grant %s android.permission-group.CALL_PHONE' % (
            self._deviceName, self.get_package(apkpath))
        return call_cmd(cmd)

    def get_package(self, apkpath: str):
        """
        获取安装程序的package
        :param apkpath: app安装程序在本地的地址
        :return:
        """
        cmd = 'aapt dump badging {} | findstr package'.format(apkpath)
        info = call_cmd(cmd)
        result = re.search("name='.*?'", info)
        if result is None:
            return None
        return result.group().replace('name=', '').replace("'", '')

    def get_battery_info(self):
        """
        在指定执行机上运行 adb shell dumpsys battery,获取电池的信息
         * 相关参数介绍:
         * status: 1            #电池状态：2：充电状态 ，其他数字为非充电状态
         * health: 2            #电池健康状态：只有数字2表示good
         * present: true        #电池是否安装在机身
         * level: 55            #电量: 百分比
         * voltage: 3977         #电池电压
         * current now: -335232  #电流值，负数表示正在充电
         * temperature: 335      #电池温度，单位是0.1摄氏度
         * technology: Li-poly    #电池种类=
        :return:
        """
        cmd = 'adb -s {} shell dumpsys battery'.format(self._deviceName)
        return call_cmd(cmd)

    def awake(self):
        """
        唤醒设备
        :return:
        """
        cmd = 'adb -s {} shell input keyevent 26'.format(self._deviceName)
        return call_cmd(cmd)

    def get_platform_version(self):
        """
        获取手机系统版本
        :return:
        """
        cmd = 'adb -s {} shell getprop ro.build.version.release'.format(self._deviceName)
        return call_cmd(cmd).replace(' ', '').replace('\n', '')

    def get_mUnrestrictedScreen(self):
        """
        获取手机的分辨率
        :return: widthxheight
        """
        cmd = 'adb -s {} shell "dumpsys window | grep mUnrestrictedScreen"'.format(self._deviceName)
        out: str = call_cmd(cmd).replace('\n', '')
        return out.strip().split(' ')[-1]

    def get_brand(self):
        """
        获取手机的厂商名字
        :return:
        """
        cmd = 'adb -s {} shell getprop ro.product.brand'.format(self._deviceName)
        return call_cmd(cmd)

    def get_model(self):
        """
        获取手机设备型号: eg: PCAM00
        :return:
        """
        cmd = 'adb -s {} shell getprop ro.product.model'.format(self._deviceName)
        return call_cmd(cmd)

    def is_screen_lock(self):
        """
        屏幕是否解锁状态
        :return: 解锁:true
        """
        cmd = 'adb -s {} shell dumpsys window policy | findstr mAwake'.format(self._deviceName)
        return call_cmd(cmd).find('mAwake=true') != -1

    def start_tel(self, tel):
        """
        打电话
        :param tel: 要拨打电话的号码
        :return:
        """
        cmd = 'adb -s %s shell am start -a android.intent.action.CALL tel:%s' % (self._deviceName, tel)
        return call_cmd(cmd)

    def cancel_tel(self):
        """
        挂电话
        :return:
        """
        cmd = 'adb -s {} shell input  keyevent  KEYCODE_ENDCALL'.format(self._deviceName)
        return call_cmd(cmd)

    def get_battery_more(self):
        """
        获取整个设别的电量消耗信息 adb shell dumpsys batterystats
        :return:
        """
        cmd = 'adb -s {} shell dumpsys batterystats|more +10'.format(self._deviceName)
        return call_cmd(cmd)

    def getMemTotal(self):
        """
        获取手机的总内存
        :return: 内存的大小,eg:3006156kB
        """
        cmd = 'adb -s {} shell cat /proc/meminfo |findstr MemTotal'.format(self._deviceName)
        return int(call_cmd(cmd).replace(' ', '').replace('MemTotal:', '').replace('\n', '').replace('kB', ''))

    def getMemFree(self):
        """
        获取手机内存剩余量
        :return: 剩余内存的大小,eg:95892kB
        """
        cmd = 'adb -s {} shell cat /proc/meminfo |findstr MemFree'.format(self._deviceName)
        mem = call_cmd(cmd).replace(' ', '').replace('MemFree:', '').replace('\n', '').replace('kB', '')
        try:
            mem = int(mem)
        except Exception:
            traceback.print_exc()
            mem = None
        return mem

    def cpu_info(self):
        """
        获取cpu信息
        :return: 处理器，cpu核数
        """
        cmd_processor = 'adb -s %s shell cat /proc/cpuinfo | findstr Processor' % self._deviceName
        cmd_cpu_nums = 'adb -s %s shell cat /proc/cpuinfo' % self._deviceName
        out_cmd_processor = call_cmd(cmd_processor).split(':')[-1]
        out_cmd_cpu_nums = call_cmd(cmd_cpu_nums)
        num_cpu = out_cmd_cpu_nums.count('processor')
        return out_cmd_processor, num_cpu

    def screen(self):
        """
        截屏 手机截屏,保存在/sdcard 下， 文件的名字为uuid
        :return: (cmd命令执行信息,截图在手机的保存地址)
        """
        path = '/sdcard/{}.png'.format(uuid.uuid1().__str__().replace('-', ''))
        cmd = 'adb -s {} shell screencap -p {}'.format(self._deviceName, path)
        return call_cmd(cmd), path

    def rm_file(self, path):
        """
        删除文件
        :param path: android系统下文件路径
        :return:
        """
        cmd = 'adb -s {} shell rm {}'.format(self._deviceName, path)
        return call_cmd(cmd)

    def pull(self, remote: str, local: str):
        """
         从远程端的指定路径copy文件到本地
         :param remote 文件在手机端的地址
         :param local 文件在本地的地址
        :return:
        """
        cmd = 'adb -s {} pull {} {}'.format(self._deviceName, remote, local)
        return local + '/' + remote.split('/')[-1], call_cmd(cmd)

    def push(self, local: str, remote: str):
        """
         从本机的指定路径copy文件到手机
         :param local 文件在本地的地址
         :param remote 文件在手机端的地址
        :return:
        """
        cmd = 'adb -s {} push {} {}'.format(self._deviceName, local, remote)
        return call_cmd(cmd)

    def get_cpu_info(self):
        """
        获取cpu信息
        :return:
        """
        cmd = 'adb -s {} shell cat /proc/cpuinfo'.format(self._deviceName)
        return call_cmd(cmd)

    def clear(self, apkpath):
        """
        adb shell pm clear 包
        清楚包的操作数据和缓存
        @param apkpath: apk安装包路径
        @return: 成功:Success
        """
        cmd = 'adb -s %s shell pm clear %s' % (self._deviceName, self.get_package(apkpath))
        return call_cmd(cmd=cmd)

    def get_versionCode(self, apkpath: str):
        """
        获取安装app程序的版本
        :param apkpath: app安装程序在本地的地址

        :return:
        """
        cmd = 'aapt dump badging {} | findstr package'.format(apkpath)
        info = call_cmd(cmd)
        result = re.search("versionCode='.*?'", info)
        if result is None:
            return None
        return result.group().replace('versionCode=', '')

    def get_versionName(self, apkpath: str):
        """
        获取测试程序的 versionName
        :param apkpath: app安装程序在本地的地址
        :return:
        """
        cmd = 'aapt dump badging {} | findstr package'.format(apkpath)
        info = call_cmd(cmd)
        result = re.search("versionName='.*?'", info)
        if result is None:
            return None
        return result.group().replace('versionName=', '')

    def get_activity(self, apkpath: str):
        """
        获取测试程序的 入口activity
        :param apkpath: app安装程序在本地的地址
        :return:
        """
        cmd = 'aapt dump badging {} | findstr launchable-activity'.format(apkpath)
        info = call_cmd(cmd)
        result = re.search("name='.*?'", info)
        if result is None:
            return None
        return result.group().replace('name=', '').replace("'", '')

    def press_home(self):
        cmd = f'adb -s {self._deviceName} shell input keyevent 3'
        return call_cmd(cmd)

    def long_press_acc(self, secs=5):
        """
        长按电源键
        :return:
        """
        cmd = f'adb -s {self._deviceName} shell input keyevent 26 --longpress {secs}'
        return call_cmd(cmd)

    def long_press_volume_add(self, secs):
        """
        长按增加音量键
        :return:
        """
        cmds = [
            f'adb -s {self._deviceName} shell sendevent /dev/input/event2 1 115 1',
            f'adb -s {self._deviceName} shell sendevent /dev/input/event2 0 0 0',
            f'adb -s {self._deviceName} shell sendevent /dev/input/event2 1 115 0',
            f'adb -s {self._deviceName} shell sendevent /dev/input/event2 0 0 0',
        ]
        self.__long_press(cmds, secs=secs)

    def long_press_volume_sub(self, secs):
        """
        长按减小音量键
        :return:
        """
        cmds = [
            f'adb -s {self._deviceName} shell sendevent /dev/input/event2 1 114 1',
            f'adb -s {self._deviceName} shell sendevent /dev/input/event2 0 0 0',
            f'adb -s {self._deviceName} shell sendevent /dev/input/event2 1 114 0',
            f'adb -s {self._deviceName} shell sendevent /dev/input/event2 0 0 0',
        ]
        self.__long_press(cmds, secs=secs)

    def long_click_panel_air(self, sec=3):
        """
        长按面板空调应急启动开关
        :param sec: 长按时间
        :return:
        """
        cmd = f'adb -s {self._deviceName} shell input keyevent 136 --longpress {sec}'
        return call_cmd(cmd)

    def acc_off(self):
        """
        ACC OFF
        :return:
        """
        cmd = f"adb -s {self._deviceName} shell input keyevent 131"
        return call_cmd(cmd)

    def acc_on(self):
        """
        ACC ON
        :return:
        """
        cmd = f"adb -s {self._deviceName} shell input keyevent 132"
        return call_cmd(cmd)

    def long_press_power(self, secs):
        """
        长按power
        :param secs: 按键时长
        :return:
        """
        cmds = [f'adb -s {self._deviceName}  shell sendevent /dev/input/event2 1 116 1',
                f'adb -s {self._deviceName} shell sendevent /dev/input/event2 0 0 0',
                f'adb -s {self._deviceName} shell sendevent /dev/input/event2 1 116 0',
                f'adb -s {self._deviceName} shell sendevent /dev/input/event2 0 0 0']
        self.__long_press(cmds, secs)

    def execute_adb_cmd(self, cmd):
        """
        执行adb命令，例如 adb shell getprop ro.product.model
        :param cmd adb命令，和在命令行输入的内容一致
        :return 命令行输入的内容
        """
        return call_cmd(cmd)

    def __long_press(self, keyevents: list, secs):
        [self.execute_adb_cmd(cmd) for cmd in keyevents[:2]]
        time.sleep(secs)
        [self.execute_adb_cmd(cmd) for cmd in keyevents[2:]]

    def __get_media_volume(self, name):
        """
        获取媒体音量信息
        :param name
            system ring music alarm
        :return 当前音量,最小音量, 最大音量
        """
        volume_id = ['system', 'ring', 'music', 'alarm']
        assert name in volume_id, f'name必须在{str(volume_id)}中'
        cmd = f'adb -s {self._deviceName} shell media volume --show --stream {volume_id.index(name) + 1} --get'
        volume_info = call_cmd(cmd).strip().split('\n')[-1]
        cur, min, max = re.compile('\d+').findall(volume_info)
        return int(cur), int(min), int(max)

    def __set_media_volume(self, name, volume):
        """
        获取媒体音量信息
        :param name
            system ring music alarm
        :return 音量信息
        """
        volume_id = ['system', 'ring', 'music', 'alarm']
        assert name in volume_id, f'name必须在{str(volume_id)}中'
        cmd = f'adb -s {self._deviceName} shell media volume --show --stream {volume_id.index(name) + 1} --set {volume}'
        return call_cmd(cmd).strip()

    def __long_click(self, keycode, sec=5):
        """
        :param keycode 按键值
        :param sec: 长按时间
        :return:
        """
        cmd = f'adb -s {self._deviceName} shell input keyevent {keycode} --longpress {sec}'
        return call_cmd(cmd)

    def panel_air_click(self, sec=5):
        """
        面板空调控制开关按钮
        :param sec: 时间
        :return:
        """
        cmd = f'adb -s {self._deviceName} shell input keyevent 136 --longpress {sec}'
        return call_cmd(cmd)

    def coordinate_swipe(self, startx, starty, stopx, stopy, sec):
        """
        坐标滑动
        :param startx: 开始x坐标
        :param starty: 开始y坐标
        :param stopx: 结束x坐标
        :param stopy: 结束y坐标
        :param sec: 时间（ms）
        :return:
        """
        cmd = f"adb -s {self._deviceName} shell input swipe {startx} {starty} {stopx} {stopy} {sec}"
        return call_cmd(cmd)

    def get_bluetooth_state(self):
        """
        查看蓝牙模块状态
        :return: 0：关闭； 1：开启
        """
        cmd = f'adb -s {self._deviceName} shell settings get global bluetooth_on'
        return call_cmd(cmd)

    def get_screen_brightness(self):
        """
        获取当前屏幕的亮度
        """
        cmd = f'adb -s {self._deviceName} shell settings get system screen_brightness'
        return call_cmd(cmd)

    def get_wifi_signal(self):
        """
        获取wifi信号强度
        """
        cmd = f'adb -s {self._deviceName} shell wpa_cli -iwlan0 -g@android:wpa_wlan0 IFNAME=wlan0 scan_results'
        return call_cmd(cmd)