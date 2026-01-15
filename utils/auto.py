import uiautomation as auto
import time
import sys


# 注意：运行此脚本需要安装 uiautomation 库
# 在命令行运行: pip install uiautomation

class WeChatAutomator:
    def __init__(self):
        print("正在连接微信窗口...")
        # 获取微信主窗口
        self.wechat_window = auto.WindowControl(Name="微信", ClassName="WeChatMainWndForPC")

    def activate_window(self):
        """激活并置顶微信窗口"""
        if self.wechat_window.Exists(maxSearchSeconds=2):
            self.wechat_window.SetActive()
            self.wechat_window.SetTopmost(True)
            self.wechat_window.SetTopmost(False)  # 取消置顶以免挡住其他操作
            return True
        else:
            print("未找到微信窗口，请先登录微信电脑版。")
            return False

    def search_and_click(self, name):
        """搜索并点击指定的好友/群/文件传输助手"""
        print(f"正在搜索: {name}")

        # 1. 快捷键 Ctrl+F (模拟按键)
        self.wechat_window.SendKeys('{Ctrl}f')
        time.sleep(0.5)

        # 2. 输入名称
        auto.SendKeys(name)
        time.sleep(1)

        # 3. 按回车进入聊天窗口
        auto.SendKeys('{Enter}')
        time.sleep(1)

        # 验证是否进入了正确的聊天窗口（检查标题栏）
        return True

    def forward_latest_message(self, target_group_name):
        """
        核心逻辑：
        假设你已经打开了 '资源来源窗口' (比如文件传输助手)，
        且最后一条消息就是你要发送的小程序卡片。
        """
        print("正在定位最后一条消息并准备转发...")

        # 定位消息列表控件
        msg_list = self.wechat_window.ListControl(Name="消息")

        if not msg_list.Exists(maxSearchSeconds=2):
            print("未找到消息列表，请确保微信窗口大小正常。")
            return

        # 获取最后一条消息
        last_msg = msg_list.GetLastChildControl()
        if not last_msg:
            print("列表为空，无法转发。")
            return

        # --- 尝试触发转发逻辑 (带重试机制) ---
        select_wnd = None

        for attempt in range(2):  # 尝试最多2次
            print(f"尝试第 {attempt + 1} 次点击转发...")

            # 1. 移动鼠标到消息中心并右键
            # 稍微移动一点位置，防止点到边缘
            last_msg.RightClick()
            time.sleep(0.8)

            # 2. 在右键菜单中寻找 "转发" 按钮
            menu = auto.MenuControl(ClassName="CMenuWnd")
            if menu.Exists(maxSearchSeconds=2):
                forward_btn = menu.MenuItemControl(Name="转发...")
                if forward_btn.Exists():
                    forward_btn.Click()
                    time.sleep(1)  # 等待窗口弹出
                else:
                    print("右键菜单中未找到'转发'选项。")
                    continue
            else:
                print("右键菜单未弹出，重试...")
                continue

            # 3. --- 增强版窗口搜索逻辑 ---
            # 策略A: 标准 ClassName (ContactSelectWnd)
            select_wnd = auto.WindowControl(ClassName="WeChatMainWndForPC")
            if select_wnd.Exists(maxSearchSeconds=1):
                break  # 找到了，跳出循环

            # 策略B: 窗口标题 Name (选择联系人 / 分发消息)
            # 有些版本微信叫 "选择联系人"，有些叫 "分发消息"
            # select_wnd = auto.WindowControl(Name="发送给")
            # if select_wnd.Exists(maxSearchSeconds=1):
            #     break
            #
            # select_wnd = auto.WindowControl(Name="分发消息")
            # if select_wnd.Exists(maxSearchSeconds=1):
            #     break

            print("未检测到转发窗口，准备重试...")
            select_wnd = None  # 重置

        if not select_wnd:
            print("错误：转发窗口一直未弹出。可能原因：")
            print("1. 微信版本更新导致窗口类名改变。")
            print("2. 电脑卡顿。")
            print("正在打印当前所有顶层窗口帮助调试:")
            for win in auto.GetRootControl().GetChildren():
                if win.ClassName.startswith("WeChat") or "联系人" in win.Name:
                    print(f" - Found Window: Name='{win.Name}', ClassName='{win.ClassName}'")
            return

        # --- 处理转发弹窗 ---
        print(f"转发窗口已找到，准备发送给: {target_group_name}")

        # 激活窗口，防止在后台无法输入
        select_wnd.SetActive()
        time.sleep(0.5)

        # --- 修复：精确定位搜索框 ---
        # 尝试寻找名为“搜索”的编辑框，或者直接找第一个编辑框
        search_edit = select_wnd.EditControl(Name="搜索")
        if not search_edit.Exists(maxSearchSeconds=1):
            search_edit = select_wnd.EditControl()  # 找任意编辑框

        if search_edit.Exists(maxSearchSeconds=2):
            print("找到搜索框，正在输入...")
            search_edit.Click()  # 关键：先点击聚焦
            time.sleep(0.2)
            search_edit.SendKeys(target_group_name)
        else:
            print("未找到明确的搜索框，尝试直接向窗口输入...")
            # 如果找不到编辑框，再尝试直接对窗口SendKeys
            select_wnd.SendKeys(target_group_name)

        time.sleep(1)  # 等待搜索结果

        # --- 优化：选中搜索结果 (多策略防报错) ---
        print("正在尝试选中搜索结果...")
        is_selected = False

        # 策略 1: 优先寻找复选框或单选框 (适配用户反馈的场景)
        # 很多版本微信转发界面，选中联系人本质上是勾选一个 CheckBox
        # 我们限制 searchDepth，避免扫到太深的地方，但在 DirectUI 中通常需要一点深度
        target_check = select_wnd.CheckBoxControl(searchDepth=6, foundIndex=1)
        if not target_check.Exists(maxSearchSeconds=0.5):
            # 或者是单选框
            target_check = select_wnd.RadioButtonControl(searchDepth=6, foundIndex=1)

        if target_check.Exists(maxSearchSeconds=0.5):
            target_check.Click()
            is_selected = True
            print("已点击搜索结果中的复选框/单选框。")

        # 策略 2: 标准 ListControl 查找 (如果上面没找到)
        if not is_selected:
            result_list = select_wnd.ListControl()
            if result_list.Exists(maxSearchSeconds=0.5):
                first_item = result_list.GetFirstChildControl()
                if first_item:
                    first_item.Click()
                    is_selected = True
                    print("已通过列表点击选中联系人项。")

        # 策略 3: 深度查找 ListItem
        if not is_selected:
            target_item = select_wnd.ListItemControl(searchDepth=5)
            if target_item.Exists(maxSearchSeconds=0.5):
                target_item.Click()
                is_selected = True
                print("通过深度搜索找到并选中联系人。")

        # --- 新增：未找到时的处理逻辑 (点击取消) ---
        if not is_selected:
            print(f"警告：未找到目标 '{target_group_name}' (搜索结果为空或无法选中)。")
            print("正在尝试点击取消按钮...")

            # 策略 1: 通过“发送”按钮定位旁边的“取消”按钮 (最稳健)
            # 这样可以绝对避免点到搜索框里的 "X" (那个按钮通常叫 "清除" 或 "取消")
            cancel_clicked = False

            # 先找发送按钮
            send_btn_ref = select_wnd.ButtonControl(Name="发送")
            if send_btn_ref.Exists(maxSearchSeconds=2):
                # 获取发送按钮的父容器 (底部工具栏)
                bottom_panel = send_btn_ref.GetParentControl().GetParentControl()
                if bottom_panel:
                    print('找到发送按钮的父容器了，正在列出所有子控件：')
                    # 遍历并打印所有子控件信息，帮助定位真正的取消按钮
                    for child in bottom_panel.GetChildren():
                        print(
                            f"Found Child -> Name: '{child.Name}', ClassName: '{child.ClassName}', ControlType: '{child.ControlTypeName}'")

                    # 在底部工具栏里找 "取消"
                    real_cancel = bottom_panel.ButtonControl(Name="取消")
                    if real_cancel.Exists(maxSearchSeconds=1):
                        real_cancel.Click()
                        cancel_clicked = True
                        print("已点击底部取消按钮。")
                        return

        # --- 点击 "发送" 按钮 ---
        # 只有在选中了目标的情况下才执行发送
        send_btn = select_wnd.ButtonControl(Name="发送")
        if not send_btn.Exists():
            # 尝试不带名字查找按钮，通常是最后一个按钮
            pass

        if send_btn.Exists():
            send_btn.Click()
            print("发送按钮已点击。")
        else:
            print("未找到发送按钮，尝试直接回车发送...")
            select_wnd.SendKeys('{Enter}')

        print("发送完成。")


def main():
    # --- 配置区域 ---
    SOURCE_CHAT = "文件传输助手"  # 这里存放你的小程序卡片

    # 修改为列表，支持多个目标群
    TARGET_GROUPS = [
        "中坦綜合诊所",
        "Co Co Home",
        "坦桑发声群",
        "Bestn广州",
        "东非商业圈",
        "坦桑灵味中国美食",
        "坦桑达市信息",
        "坦桑@桑达",
        "印象浏阳",
        "坦桑尼亚休闲按摩",
        "非洲创业群",
        "坦桑三羊广告",
        "时光里音乐餐厅",
        "坦桑云之南",
        "皇家乐园水疗",
        "一品香美食群",
        "闽南牛肉汤福清",
        "北斗星理发2群",
        "坦华人一家",
        "坦桑空运海运-叮当",
        "坦桑尼亚中国",
        "环宇&海安 服务",
        "坦桑-中华会馆湘菜馆",
        "坦桑尼亚贸易信息",
        "【中非同城】坦桑信息港①群",
        "【中非同城】坦桑信息港③群",
        "长春饭店",
        "非常好酒店",
        "阿鲁沙华人群",
        "日日鲜美食店",
        "中国城超市内",
        "科鲁东升机电",
        "达市天水",
        "天正律所",
        "坦桑尼亚多多马",
        "坦桑尼亚投资咨询",
        "坦桑尼亚金沙赌场",
        "中华会馆美食住宿群",
        "坦桑尼亚进出口贸易",
        "姆贝亚之星酒店",
        "北京商会网上会员",
        "中国城螺蛳粉",
        "中国城会员群11群",
        "华信国际",
        "达市GPS定位安装",
        "倾颜美业",
        "川渝商会信息",
        "华夏商务服务中心",
        "坦桑尼亚回国交流群",
        "东北饺子馆",
    ]
    # ----------------

    automator = WeChatAutomator()

    if automator.activate_window():
        print("第一步：进入存放卡片的聊天窗口...")
        # 1. 先去源头找到卡片
        automator.search_and_click(SOURCE_CHAT)

        # 2. 循环转发给列表中的每个群
        print(f"检测到 {len(TARGET_GROUPS)} 个目标群，开始逐个发送...")

        for i, group in enumerate(set(TARGET_GROUPS)):
            print(f"\n[{i + 1}/{len(TARGET_GROUPS)}] 正在处理目标: {group}")

            # 每次发送前确保微信窗口是激活状态
            automator.activate_window()

            # 转发最后一条消息给当前目标
            automator.forward_latest_message(group)

            # 发送完一个后稍微等待，避免操作过快被风控或UI未刷新
            if i < len(TARGET_GROUPS) - 1:
                print("等待 1 秒后继续发送下一个...")
                time.sleep(1)

        print("\n所有群发任务执行完毕。")


if __name__ == "__main__":
    main()