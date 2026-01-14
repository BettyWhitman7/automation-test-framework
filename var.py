class globals_var:
    power_serial = None  # 继电器串口
    log_serial = None  # 日志串口
    slf_serial = None  # 一线通串口
    usb_can = None  # USBCAN
    config_path = None  # 配置文件路径
    is_video_playing = False  # 是否正在播放视频
    current_step = 0  # 当前步骤
    line_num = 0  # 当前行数
    current_feature = None  # 当前功能
    current_scenario = None  # 当前场景
    start_time = None  # 开始时间
    end_time = None  # 结束时间
    protocol = None  # 协议
    eff = 1
    rtr = 0
    scenario_stop = [False]  # 场景停止标志
    #   fudaiA6
    current_testdata_dir = ""  # 当前测试数据目录
    test_report_excel = None
    #   fudaiA6
    android_device = None
    d = None
    temp_data = {}
    encryption_info = {"fun": "seed_and_key_fudai_a6", "level": [1]}
    transmit_ids = ["18DA54F9"]
    rev_ids = ["18DAF954"]
    test_result_map = {}
    excel_wb = None
    is_can_init = False
    window = None
    model = None
    is_hex = False
    port_map = {}
    dialog_info = {
        "title": "",
        "msg": "",
        "result": True
    }
    log_cache = {}  # 日志缓存
    base = None
    vin = ""
    iccid = ""
    gpsid = ""
    result = {}
    tsp = None  # 平台名称
    mqttx = None
