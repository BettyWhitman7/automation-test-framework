from enum import Enum
from tools.communication.cmd_comm import call_cmd


class BroadcastKey(Enum):
    POWER = 132
    HOME = 131
    VOLUME_ADD = 138
    VOLUME_SUB = 139
    LAST = 135
    NEXT = 134
    VOICE_CONNECT = 315
    MUTE_HUNG = 314
    MODE = 141


class Broadcast:

    def __init__(self, device):
        self._device = device

    def __send_broad(self, c):
        return call_cmd(f'adb -s {self._device} shell am broadcast -a {c}')

    def connectivity_change(self):
        """
        网络连接发生变化
        :return:
        """
        return self.__send_broad('android.net.conn.CONNECTIVITY_CHANGE')

    def screen_on(self):
        """
        屏幕点亮
        :return:
        """
        return self.__send_broad('android.intent.action.SCREEN_ON')

    def screen_off(self):
        """
        屏幕熄灭
        :return:
        """
        return self.__send_broad('android.intent.action.SCREEN_OFF')

    def battery_low(self):
        """
        电量低，会弹出电量低提示框
        :return:
        """
        return self.__send_broad('android.intent.action.BATTERY_LOW')

    def battery_okay(self):
        """
        电量恢复了
        :return:
        """
        return self.__send_broad('android.intent.action.BATTERY_OKAY')

    def boot_completed(self):
        """
        设备启动完毕
        :return:
        """
        return self.__send_broad('android.intent.action.BOOT_COMPLETED')

    def device_storage_low(self):
        """
        存储空间过低
        :return:
        """
        return self.__send_broad('android.intent.action.DEVICE_STORAGE_LOW')

    def device_storage_ok(self):
        """
        存储空间恢复
        :return:
        """
        return self.__send_broad('android.intent.action.DEVICE_STORAGE_OK')

    def package_added(self):
        """
        安装了新的应用
        :return:
        """
        return self.__send_broad('android.intent.action.PACKAGE_ADDED')

    def state_change(self):
        """
        WiFi 连接状态发生变化
        :return:
        """
        return self.__send_broad('android.net.wifi.STATE_CHANGE')

    def wifi_state_changed(self):
        """
        WiFi 状态变为启用/关闭/正在启动/正在关闭/未知
        :return:
        """
        return self.__send_broad('android.net.wifi.WIFI_STATE_CHANGED')

    def battery_changed(self):
        """
        电池电量发生变化
        :return:
        """
        return self.__send_broad('android.intent.action.BATTERY_CHANGED')

    def input_method_changed(self):
        """
        系统输入法发生变化
        :return:
        """
        return self.__send_broad('android.intent.action.INPUT_METHOD_CHANGED')

    def action_power_connected(self):
        """
        外部电源连接
        :return:
        """
        return self.__send_broad('android.intent.action.ACTION_POWER_CONNECTED')

    def action_power_disconnected(self):
        """
        外部电源断开连接
        :return:
        """
        return self.__send_broad('android.intent.action.ACTION_POWER_DISCONNECTED')

    def dreaming_starteddreaming_started(self):
        """
        系统开始休眠
        :return:
        """
        return self.__send_broad('android.intent.action.DREAMING_STARTED')

    def dreaming_stopped(self):
        """
        系统停止休眠
        :return:
        """
        return self.__send_broad('android.intent.action.DREAMING_STOPPED')

    def wallpaper_changed(self):
        """
        壁纸发生变化
        :return:
        """
        return self.__send_broad('android.intent.action.WALLPAPER_CHANGED')

    def headset_plug(self):
        """
        插入耳机
        :return:
        """
        return self.__send_broad('android.intent.action.HEADSET_PLUG')

    def media_unmounted(self):
        """
        卸载外部介质
        :return:
        """
        return self.__send_broad('android.intent.action.MEDIA_UNMOUNTED')

    def media_mounted(self):
        """
        挂载外部介质
        :return:
        """
        return self.__send_broad('android.intent.action.MEDIA_MOUNTED')

    def power_save_mode_changed(self):
        """
        省电模式开启
        :return:
        """
        return self.__send_broad('android.os.action.POWER_SAVE_MODE_CHANGED')

    @staticmethod
    def send_broadcast_jh(device: str, key_code: BroadcastKey, key_action):
        cmd = "adb -s {} shell am broadcast -a com.yaxon.telematics.ACTION_KEY_EVENT --ei keycode {} --ei keyaction {}"
        call_cmd(cmd.format(device, key_code, key_action))
