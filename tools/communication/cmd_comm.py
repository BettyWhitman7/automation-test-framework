import re
import subprocess
# import wexpect
import time
from subprocess import Popen, PIPE

def call_adb_cmd(commands):
    """ 命令行执行函数 -- 可执行多行
    :commands: 命令(此参数为列表，可以参考main中的示例)
    :return: 结果（返回两个值：1.命令行输出内容 2.错误信息）
    :此命令会自动执行adb shell 所以commands中直接写需要在adb shell环境下执行的命令即可
    :有些命令反应迟钝，需要自行添加 “sleep [时间]” 以防后续命令快速执行而无结果返回（可以参考main中的示例）
    """
    # Concatenate commands with semicolons
    command_string = ' ; '.join(commands)
    # Start the adb shell process with the command string
    process = subprocess.Popen(['adb', 'shell', command_string],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True)
    # Read the output and errors
    output, errors = process.communicate()
    # Return the output and any errors
    return output, errors


def call_cmd(cmd) -> str:
    """ 命令行执行命令
    :param cmd: 命令
    :return: 结果
    """
    res = Popen(cmd, stdout=PIPE, encoding="UTF8")
    out, err = res.communicate()
    res.kill()
    return out

def devices() -> list:
    """ 通过adb devices返回设备号
    :return: 设备号
    """
    info = call_cmd("adb devices")
    result = re.findall('\n(.*?)\t', info, re.S)
    if len(result) == 0:
        raise Exception("没有连接的设备")
    return result

if __name__ == "__main__":
    # List of commands to execute
    commands = [
        'echo "Starting commands..."',
        "cat /dev/smd8 &\n"
        "sleep 1\n" # 这里需要休眠一秒以等待上面命令执行成功
        "echo -e 'AT+CCID\r\n' > /dev/smd8\n" #核心命令
        "sleep 1\n" #等待1秒，等核心命令执行完成
        'echo "Commands completed."'
    ]

    # Execute the commands through adb shell
    output, errors = call_adb_cmd(commands)
    print("Output:")
    print(output)
    if errors:
        print("Errors:")
        print(errors)
