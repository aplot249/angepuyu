import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import time
import datetime
import uiautomation as auto
import sys
import os
import json
import uuid
import subprocess


# --- 核心自动化逻辑 (保持不变，只是被调度器调用) ---

class WeChatAutomator:
    def __init__(self, logger_func):
        self.log = logger_func
        self.stop_flag = False
        self.wechat_window = None

    def connect_wechat(self):
        # 每次执行任务前尝试连接，确保窗口句柄最新
        self.wechat_window = auto.WindowControl(Name="微信", ClassName="WeChatMainWndForPC")

    def activate_window(self):
        """激活并置顶微信窗口"""
        if self.wechat_window.Exists(maxSearchSeconds=2):
            self.wechat_window.SetActive()
            try:
                self.wechat_window.SetTopmost(True)
                self.wechat_window.SetTopmost(False)
            except:
                pass
            return True
        else:
            self.log("错误：未找到微信窗口，请先登录微信电脑版。")
            return False

    def search_and_click(self, name):
        """搜索并点击指定的好友/群/文件传输助手"""
        self.wechat_window.SendKeys('{Ctrl}f')
        time.sleep(0.5)
        auto.SetClipboardText(name)
        time.sleep(0.2)
        self.wechat_window.SendKeys('{Ctrl}v')
        time.sleep(1)
        auto.SendKeys('{Enter}')
        time.sleep(1)
        return True

    def get_last_message_content(self):
        """获取当前聊天窗口最后一条消息的特征(Name)"""
        msg_list = self.wechat_window.ListControl(Name="消息")
        if not msg_list.Exists(maxSearchSeconds=1):
            return None
        last_msg = msg_list.GetLastChildControl()
        if not last_msg:
            return None
        return last_msg.Name

    def send_paste_only(self, text_content):
        """只粘贴发送文字"""
        if not text_content: return
        try:
            auto.SetClipboardText(text_content)
        except Exception as e:
            self.log(f"设置剪贴板失败: {e}")
            return
        time.sleep(0.5)
        self.wechat_window.SendKeys('{Ctrl}v')
        time.sleep(0.5)
        self.wechat_window.SendKeys('{Enter}')
        self.log("文字发送成功。")

    def set_clipboard_files(self, file_paths):
        """
        利用 PowerShell 将文件列表写入剪贴板 (模拟 Ctrl+C 复制文件)
        这样可以在微信中直接 Ctrl+V 粘贴发送图片/文件
        """
        if not file_paths: return False

        # 构建 PowerShell 命令
        # 使用 System.Windows.Forms.Clipboard.SetFileDropList
        # 注意：路径需要绝对路径，且不能有特殊字符导致命令截断，这里做简单处理
        try:
            abs_paths = [os.path.abspath(p) for p in file_paths]
            # 构造 Powershell 数组字符串: "path1", "path2"
            ps_paths = ",".join([f"'{p}'" for p in abs_paths])

            cmd = f"powershell -command \"& {{Add-Type -Assembly System.Windows.Forms; [System.Windows.Forms.Clipboard]::SetFileDropList([System.Collections.Specialized.StringCollection]({ps_paths}))}}\""

            # 运行命令，隐藏窗口
            subprocess.run(cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            return True
        except Exception as e:
            self.log(f"图片写入剪贴板失败: {e}")
            return False

    def send_clipboard_images(self):
        """粘贴并发送剪贴板中的图片/文件"""
        time.sleep(0.5)
        self.wechat_window.SendKeys('{Ctrl}v')
        time.sleep(1.0)  # 等待图片加载
        self.wechat_window.SendKeys('{Enter}')
        self.log("图片/文件粘贴发送成功。")

    def forward_latest_message(self, target_group_name):
        """转发最后一条消息"""
        self.log("正在定位最后一条消息并准备转发...")
        main_handle = self.wechat_window.NativeWindowHandle
        msg_list = self.wechat_window.ListControl(Name="消息")

        if not msg_list.Exists(maxSearchSeconds=2):
            self.log("未找到消息列表。")
            return

        last_msg = msg_list.GetLastChildControl()
        if not last_msg:
            self.log("列表为空。")
            return

        select_wnd = None
        for attempt in range(2):
            # 修改：将点击位置调整为 0.75 (避开最右侧头像，但依然靠右)
            last_msg.RightClick(ratioX=0.75)
            time.sleep(0.8)
            menu = auto.MenuControl(ClassName="CMenuWnd")
            if menu.Exists(maxSearchSeconds=2):
                forward_btn = menu.MenuItemControl(Name="转发...")
                if forward_btn.Exists():
                    forward_btn.Click()
                    time.sleep(1.5)
                else:
                    continue
            else:
                continue

            # 寻找转发弹窗
            for win in auto.GetRootControl().GetChildren():
                if win.ClassName in ["WeChatMainWndForPC", "ContactSelectWnd"]:
                    if win.NativeWindowHandle != main_handle and win.BoundingRectangle.width() > 0:
                        select_wnd = win
                        break
            if select_wnd: break

            # 备选方案
            active_wnd = auto.GetForegroundControl()
            if active_wnd and active_wnd.ProcessId == self.wechat_window.ProcessId:
                if active_wnd.NativeWindowHandle != main_handle:
                    select_wnd = active_wnd
                    break
            select_wnd = None

        if not select_wnd:
            self.log("错误：未能识别到转发弹窗。")
            return

        select_wnd.SetActive()
        time.sleep(0.5)

        search_edit = select_wnd.EditControl(Name="搜索")
        if not search_edit.Exists(maxSearchSeconds=1): search_edit = select_wnd.EditControl()

        if search_edit.Exists(maxSearchSeconds=2):
            search_edit.Click()
            time.sleep(0.2)
            auto.SetClipboardText(target_group_name)
            time.sleep(0.1)
            search_edit.SendKeys('{Ctrl}v')
        else:
            auto.SetClipboardText(target_group_name)
            time.sleep(0.1)
            select_wnd.SendKeys('{Ctrl}v')

        time.sleep(1.5)

        is_selected = False
        target_check = select_wnd.CheckBoxControl(searchDepth=6, foundIndex=1)
        if not target_check.Exists(maxSearchSeconds=0.5):
            target_check = select_wnd.RadioButtonControl(searchDepth=6, foundIndex=1)
        if target_check.Exists(maxSearchSeconds=0.5):
            target_check.Click()
            is_selected = True

        if not is_selected:
            result_list = select_wnd.ListControl()
            if result_list.Exists(maxSearchSeconds=0.5):
                first_item = result_list.GetFirstChildControl()
                if first_item:
                    first_item.Click()
                    is_selected = True

        if not is_selected:
            self.log(f"警告：未找到目标 '{target_group_name}'，尝试取消。")
            send_btn_ref = select_wnd.ButtonControl(Name="发送")
            if send_btn_ref.Exists(maxSearchSeconds=2):
                bottom_panel = send_btn_ref.GetParentControl().GetParentControl()
                if bottom_panel:
                    real_cancel = bottom_panel.ButtonControl(Name="取消")
                    if real_cancel.Exists(maxSearchSeconds=1):
                        real_cancel.Click()
                        return

        send_btn = select_wnd.ButtonControl(Name="发送")
        if send_btn.Exists():
            send_btn.Click()
        else:
            select_wnd.SendKeys('{Enter}')
        self.log("转发完成。")

    def send_file(self, target_group, file_path):
        self.log(f"准备发送文件给: {target_group}")
        file_path = file_path.replace('"', '').strip()
        file_path = os.path.normpath(file_path)

        if not os.path.exists(file_path):
            self.log(f"错误：文件不存在 {file_path}")
            return

        send_file_btn = self.wechat_window.ButtonControl(Name="发送文件")
        if not send_file_btn.Exists(maxSearchSeconds=2):
            send_file_btn = self.wechat_window.ButtonControl(Name="聊天图片")
        if not send_file_btn.Exists(maxSearchSeconds=1):
            self.log("错误：无法找到文件发送按钮。")
            return

        send_file_btn.Click()
        time.sleep(1)

        dialog = auto.WindowControl(ClassName="#32770")
        if dialog.Exists(maxSearchSeconds=3):
            try:
                auto.SetClipboardText(file_path)
                time.sleep(0.2)
                dialog.SendKeys('{Ctrl}v')
                time.sleep(0.5)
                dialog.SendKeys('{Enter}')
            except Exception as e:
                self.log(f"输入路径失败: {e}")
                return

        self.log("等待预览窗口...")
        time.sleep(2.5)

        current_wnd = auto.GetForegroundControl()
        if not current_wnd: current_wnd = self.wechat_window

        send_btn = current_wnd.ButtonControl(Name="发送")
        if not send_btn.Exists(maxSearchSeconds=1):
            send_btn = self.wechat_window.ButtonControl(Name="发送")

        is_sent = False
        if send_btn.Exists(maxSearchSeconds=2):
            for i in range(15):
                if send_btn.IsEnabled:
                    try:
                        send_btn.Click()
                        is_sent = True
                        break
                    except:
                        pass
                time.sleep(1.0)

        if not is_sent:
            current_wnd.SendKeys('{Enter}')

        self.log(f"文件发送流程结束 -> {target_group}")


# --- 图形界面与任务管理逻辑 ---

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("微信多任务群发调度系统 v3.1")
        self.root.geometry("1000x800")

        self.automator = None
        self.worker_thread = None
        self.is_running = False

        self.group_file = "groups.txt"
        self.task_file = "tasks.json"

        self.tasks = []
        self.default_groups = ["示例群1", "示例群2"]

        self.setup_ui()
        self.load_groups_from_file()
        self.load_tasks_from_file()

    def setup_ui(self):
        self.paned_win = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=5)
        self.paned_win.pack(fill="both", expand=True, padx=5, pady=5)

        # --- 左侧区域 ---
        self.frame_left = tk.Frame(self.paned_win, width=400)
        self.paned_win.add(self.frame_left, stretch="always")

        lbl_task_list = tk.Label(self.frame_left, text="任务调度列表", font=("Arial", 12, "bold"))
        lbl_task_list.pack(pady=5)

        columns = ("name", "type", "next_run", "status")
        self.tree = ttk.Treeview(self.frame_left, columns=columns, show='headings', height=20)
        self.tree.heading("name", text="任务名称")
        self.tree.heading("type", text="类型")
        self.tree.heading("next_run", text="下次运行")
        self.tree.heading("status", text="状态")

        self.tree.column("name", width=100)
        self.tree.column("type", width=60)
        self.tree.column("next_run", width=120)
        self.tree.column("status", width=60)

        self.tree.pack(fill="both", expand=True, padx=5)
        self.tree.bind("<<TreeviewSelect>>", self.on_task_select)

        frame_task_btns = tk.Frame(self.frame_left)
        frame_task_btns.pack(fill="x", pady=10)

        tk.Button(frame_task_btns, text="保存为新任务", bg="#e1f5fe", command=self.add_task).pack(side="left", padx=5,
                                                                                                  fill="x", expand=True)
        tk.Button(frame_task_btns, text="更新选中任务", bg="#fff9c4", command=self.update_task).pack(side="left",
                                                                                                     padx=5, fill="x",
                                                                                                     expand=True)
        tk.Button(frame_task_btns, text="删除任务", bg="#ffcdd2", command=self.delete_task).pack(side="left", padx=5,
                                                                                                 fill="x", expand=True)

        frame_scheduler = tk.LabelFrame(self.frame_left, text="总调度开关", padx=5, pady=5)
        frame_scheduler.pack(fill="x", padx=5, pady=10)

        self.btn_start = tk.Button(frame_scheduler, text="启动调度器", bg="green", fg="white",
                                   font=("Arial", 12, "bold"), command=self.start_scheduler)
        self.btn_start.pack(side="left", fill="x", expand=True, padx=5)
        self.btn_stop = tk.Button(frame_scheduler, text="停止", bg="red", fg="white", font=("Arial", 12, "bold"),
                                  state="disabled", command=self.stop_scheduler)
        self.btn_stop.pack(side="right", fill="x", expand=True, padx=5)

        self.log_area = scrolledtext.ScrolledText(self.frame_left, height=10, state='disabled')
        self.log_area.pack(fill="x", padx=5, pady=5)

        # --- 右侧区域 (编辑器) ---
        self.frame_right = tk.Frame(self.paned_win, width=500)
        self.paned_win.add(self.frame_right, stretch="always")

        lbl_editor = tk.Label(self.frame_right, text="任务编辑器 (配置下方内容后点击左侧保存)",
                              font=("Arial", 10, "bold"), fg="blue")
        lbl_editor.pack(pady=5)

        frame_name = tk.Frame(self.frame_right)
        frame_name.pack(fill="x", padx=10)
        tk.Label(frame_name, text="任务名称:").pack(side="left")
        self.entry_task_name = tk.Entry(frame_name)
        self.entry_task_name.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_task_name.insert(0, "我的任务1")

        self.notebook = ttk.Notebook(self.frame_right)
        self.notebook.pack(fill="x", padx=10, pady=5)

        self.tab_forward = tk.Frame(self.notebook, pady=10)
        self.notebook.add(self.tab_forward, text="  转发卡片  ")
        self.setup_tab_forward()

        self.tab_text = tk.Frame(self.notebook, pady=10)
        self.notebook.add(self.tab_text, text="  发送文字+图片  ")
        self.setup_tab_text()

        self.tab_file = tk.Frame(self.notebook, pady=10)
        self.notebook.add(self.tab_file, text="  发送大文件/视频  ")
        self.setup_tab_file()

        frame_groups = tk.LabelFrame(self.frame_right, text="目标群 (按住Ctrl可多选)", padx=10, pady=5)
        frame_groups.pack(fill="both", expand=True, padx=10, pady=5)

        self.listbox_groups = tk.Listbox(frame_groups, selectmode=tk.MULTIPLE, height=6)
        self.listbox_groups.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(frame_groups)
        scrollbar.pack(side="left", fill="y")
        self.listbox_groups.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.listbox_groups.yview)

        frame_grp_tools = tk.Frame(frame_groups)
        frame_grp_tools.pack(side="right", fill="y")
        self.entry_new_group = tk.Entry(frame_grp_tools, width=10)
        self.entry_new_group.pack(pady=2)
        tk.Button(frame_grp_tools, text="添加", command=self.add_group_to_pool).pack(fill="x")
        tk.Button(frame_grp_tools, text="删除", command=self.del_group_from_pool).pack(fill="x")
        tk.Button(frame_grp_tools, text="全选", command=self.select_all_groups).pack(fill="x")

        frame_timer = tk.LabelFrame(self.frame_right, text="执行时间规则", padx=10, pady=10)
        frame_timer.pack(fill="x", padx=10, pady=5)

        self.timer_mode = tk.StringVar(value="interval")

        tk.Radiobutton(frame_timer, text="间隔循环:", variable=self.timer_mode, value="interval").grid(row=0, column=0,
                                                                                                       sticky="w")
        self.entry_interval_h = tk.Entry(frame_timer, width=4);
        self.entry_interval_h.insert(0, "0");
        self.entry_interval_h.grid(row=0, column=2)
        tk.Label(frame_timer, text="时").grid(row=0, column=3)
        self.entry_interval_m = tk.Entry(frame_timer, width=4);
        self.entry_interval_m.insert(0, "30");
        self.entry_interval_m.grid(row=0, column=4)
        tk.Label(frame_timer, text="分").grid(row=0, column=5)

        tk.Radiobutton(frame_timer, text="每天固定:", variable=self.timer_mode, value="fixed").grid(row=1, column=0,
                                                                                                    sticky="nw",
                                                                                                    pady=(10, 0))
        tk.Label(frame_timer, text="(格式: HH:MM, 多个时间请换行或用逗号隔开)").grid(row=1, column=1, columnspan=5,
                                                                                     sticky="w", pady=(10, 0))

        self.entry_fixed_time = scrolledtext.ScrolledText(frame_timer, height=6, width=30)
        self.entry_fixed_time.grid(row=2, column=0, columnspan=6, padx=5, pady=5, sticky="ew")
        self.entry_fixed_time.insert("1.0", "09:30, 18:00")

        tk.Radiobutton(frame_timer, text="立刻执行一次:", variable=self.timer_mode, value="once").grid(row=3, column=0,
                                                                                                       sticky="w",
                                                                                                       pady=(10, 0))
        tk.Label(frame_timer, text="(保存任务后立即执行，执行完即止)").grid(row=3, column=1, columnspan=5, sticky="w",
                                                                           pady=(10, 0))

    # --- 编辑器内部组件布局 ---
    def setup_tab_forward(self):
        tk.Label(self.tab_forward, text="来源名称:").pack(anchor="w", padx=10)
        self.entry_source = tk.Entry(self.tab_forward, width=40)
        self.entry_source.insert(0, "文件传输助手")
        self.entry_source.pack(padx=10, pady=5, fill="x")

        self.var_skip_duplicate = tk.BooleanVar(value=False)
        tk.Checkbutton(self.tab_forward, text="防重复(检测最后一条消息)", variable=self.var_skip_duplicate).pack(
            anchor="w", padx=10)

    def setup_tab_text(self):
        # 左侧：文字输入
        frame_t_left = tk.Frame(self.tab_text)
        frame_t_left.pack(side="left", fill="both", expand=True, padx=(5, 0))

        tk.Label(frame_t_left, text="发送文字(选填):").pack(anchor="w")
        self.text_content = scrolledtext.ScrolledText(frame_t_left, height=8, width=25)
        self.text_content.pack(fill="both", expand=True, pady=2)

        self.var_skip_duplicate_text = tk.BooleanVar(value=False)
        tk.Checkbutton(frame_t_left, text="防重复检测", variable=self.var_skip_duplicate_text).pack(anchor="w")

        # 右侧：图片列表
        frame_t_right = tk.Frame(self.tab_text)
        frame_t_right.pack(side="right", fill="both", expand=True, padx=(5, 5))

        tk.Label(frame_t_right, text="发送图片(选填,可多选):").pack(anchor="w")

        # 图片列表框
        self.listbox_images = tk.Listbox(frame_t_right, height=6)
        self.listbox_images.pack(fill="both", expand=True, pady=2)

        btn_frame = tk.Frame(frame_t_right)
        btn_frame.pack(fill="x")
        tk.Button(btn_frame, text="选择图片...", command=self.browse_images).pack(side="left", fill="x", expand=True)
        tk.Button(btn_frame, text="清空图片", command=lambda: self.listbox_images.delete(0, tk.END)).pack(side="right",
                                                                                                          fill="x",
                                                                                                          expand=True)

    def setup_tab_file(self):
        tk.Label(self.tab_file, text="文件路径:").pack(anchor="w", padx=10)
        f_frame = tk.Frame(self.tab_file)
        f_frame.pack(fill="x", padx=10)
        self.entry_file_path = tk.Entry(f_frame)
        self.entry_file_path.pack(side="left", fill="x", expand=True)
        tk.Button(f_frame, text="浏览...", command=self.browse_file).pack(side="right", padx=5)

    # --- 辅助功能 ---
    def browse_file(self):
        filename = filedialog.askopenfilename()
        if filename:
            self.entry_file_path.delete(0, tk.END)
            self.entry_file_path.insert(0, filename)

    def browse_images(self):
        filenames = filedialog.askopenfilenames(title="选择图片",
                                                filetypes=[("Images", "*.jpg;*.jpeg;*.png;*.bmp;*.gif")])
        if filenames:
            for f in filenames:
                self.listbox_images.insert(tk.END, f)

    def log(self, message):
        def _log():
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            self.log_area.config(state='normal')
            self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_area.see(tk.END)
            self.log_area.config(state='disabled')

        self.root.after(0, _log)

    # --- 群组池管理 ---
    def load_groups_from_file(self):
        if not os.path.exists(self.group_file):
            with open(self.group_file, "w", encoding="utf-8") as f:
                f.write("\n".join(self.default_groups))

        self.listbox_groups.delete(0, tk.END)
        try:
            with open(self.group_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip(): self.listbox_groups.insert(tk.END, line.strip())
        except:
            pass

    def save_pool_to_file(self):
        all_groups = self.listbox_groups.get(0, tk.END)
        with open(self.group_file, "w", encoding="utf-8") as f:
            f.write("\n".join(all_groups))

    def add_group_to_pool(self):
        name = self.entry_new_group.get().strip()
        if name:
            self.listbox_groups.insert(tk.END, name)
            self.entry_new_group.delete(0, tk.END)
            self.save_pool_to_file()

    def del_group_from_pool(self):
        selection = self.listbox_groups.curselection()
        if selection:
            for i in reversed(selection):
                self.listbox_groups.delete(i)
            self.save_pool_to_file()

    def select_all_groups(self):
        self.listbox_groups.select_set(0, tk.END)

    # --- 任务管理 (CRUD) ---
    def load_tasks_from_file(self):
        if os.path.exists(self.task_file):
            try:
                with open(self.task_file, "r", encoding="utf-8") as f:
                    self.tasks = json.load(f)
            except:
                self.tasks = []
        self.refresh_task_list()

    def save_tasks_to_file(self):
        with open(self.task_file, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, indent=4, ensure_ascii=False)

    def refresh_task_list(self):
        # 清空树形图
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 重新填充
        for task in self.tasks:
            next_run_str = "-"
            status = "等待中"

            if task.get('disabled', False):
                if task.get('timer_mode') == 'once':
                    status = "已完成"
                    next_run_str = "-"
                else:
                    status = "已停用"
                    next_run_str = "-"
            else:
                if task.get('next_run'):
                    next_run_str = datetime.datetime.fromtimestamp(task['next_run']).strftime("%m-%d %H:%M:%S")

            self.tree.insert('', tk.END, values=(task['name'], task['type_name'], next_run_str, status), iid=task['id'])

    def get_ui_data(self):
        """从右侧编辑器获取当前配置数据"""
        data = {}
        data['id'] = str(uuid.uuid4())  # 生成新ID，如果是更新则会被覆盖
        data['name'] = self.entry_task_name.get().strip() or "未命名任务"

        selected_indices = self.listbox_groups.curselection()
        if not selected_indices:
            messagebox.showwarning("提示", "请至少选择一个目标群！")
            return None
        data['groups'] = [self.listbox_groups.get(i) for i in selected_indices]

        current_tab = self.notebook.index(self.notebook.select())
        data['mode_index'] = current_tab

        if current_tab == 0:  # 转发
            data['type_name'] = "转发卡片"
            data['source_name'] = self.entry_source.get().strip()
            data['skip_duplicate'] = self.var_skip_duplicate.get()
        elif current_tab == 1:  # 文字+图片
            data['type_name'] = "发送文字+图片"
            data['text_msg'] = self.text_content.get("1.0", tk.END).strip()
            data['image_paths'] = list(self.listbox_images.get(0, tk.END))  # 获取所有图片路径
            data['skip_duplicate_text'] = self.var_skip_duplicate_text.get()

            if not data['text_msg'] and not data['image_paths']:
                messagebox.showwarning("错误", "文字和图片不能同时为空")
                return None
        elif current_tab == 2:  # 文件
            data['type_name'] = "发送文件"
            data['file_path'] = self.entry_file_path.get().strip()
            if not data['file_path']:
                messagebox.showwarning("错误", "文件路径不能为空")
                return None

        # 获取时间规则
        data['timer_mode'] = self.timer_mode.get()
        data['interval_h'] = self.entry_interval_h.get() or "0"
        data['interval_m'] = self.entry_interval_m.get() or "0"
        data['fixed_time'] = self.entry_fixed_time.get("1.0", tk.END).strip()

        data['next_run'] = time.time()
        data['disabled'] = False

        return data

    def add_task(self):
        task = self.get_ui_data()
        if task:
            task['next_run'] = self.calculate_next_run(task, first_run=True)
            self.tasks.append(task)
            self.save_tasks_to_file()
            self.refresh_task_list()
            self.log(f"任务 [{task['name']}] 已添加。")

    def update_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先在左侧列表选择要更新的任务")
            return

        task_id = selected[0]
        new_data = self.get_ui_data()
        if new_data:
            for i, task in enumerate(self.tasks):
                if task['id'] == task_id:
                    new_data['id'] = task_id
                    new_data['next_run'] = self.calculate_next_run(new_data, first_run=True)
                    self.tasks[i] = new_data
                    break

            self.save_tasks_to_file()
            self.refresh_task_list()
            self.log(f"任务 [{new_data['name']}] 已更新。")

    def delete_task(self):
        selected = self.tree.selection()
        if not selected: return
        task_id = selected[0]

        self.tasks = [t for t in self.tasks if t['id'] != task_id]
        self.save_tasks_to_file()
        self.refresh_task_list()
        self.log("任务已删除。")

    def on_task_select(self, event):
        """点击列表时回显数据到编辑器"""
        selected = self.tree.selection()
        if not selected: return
        task_id = selected[0]

        task = next((t for t in self.tasks if t['id'] == task_id), None)
        if not task: return

        self.entry_task_name.delete(0, tk.END)
        self.entry_task_name.insert(0, task['name'])

        self.listbox_groups.selection_clear(0, tk.END)
        all_groups = self.listbox_groups.get(0, tk.END)
        for g in task.get('groups', []):
            try:
                idx = all_groups.index(g)
                self.listbox_groups.selection_set(idx)
            except:
                pass

        mode = task['mode_index']
        self.notebook.select(mode)

        if mode == 0:
            self.entry_source.delete(0, tk.END)
            self.entry_source.insert(0, task.get('source_name', ''))
            self.var_skip_duplicate.set(task.get('skip_duplicate', False))
        elif mode == 1:
            self.text_content.delete("1.0", tk.END)
            self.text_content.insert("1.0", task.get('text_msg', ''))
            self.var_skip_duplicate_text.set(task.get('skip_duplicate_text', False))

            # 回显图片
            self.listbox_images.delete(0, tk.END)
            for img in task.get('image_paths', []):
                self.listbox_images.insert(tk.END, img)

        elif mode == 2:
            self.entry_file_path.delete(0, tk.END)
            self.entry_file_path.insert(0, task.get('file_path', ''))

        self.timer_mode.set(task.get('timer_mode', 'interval'))
        self.entry_interval_h.delete(0, tk.END);
        self.entry_interval_h.insert(0, task.get('interval_h', '0'))
        self.entry_interval_m.delete(0, tk.END);
        self.entry_interval_m.insert(0, task.get('interval_m', '0'))

        self.entry_fixed_time.delete("1.0", tk.END)
        self.entry_fixed_time.insert("1.0", task.get('fixed_time', ''))

    # --- 调度器逻辑 ---

    def calculate_next_run(self, task, first_run=False):
        now = time.time()

        if task.get('timer_mode') == 'once':
            return now + 2

        if task['timer_mode'] == 'interval':
            try:
                h = int(task.get('interval_h', 0))
                m = int(task.get('interval_m', 0))
                delta = h * 3600 + m * 60
                if delta <= 0: delta = 60
            except:
                delta = 60

            if first_run:
                return now + 2
            else:
                return now + delta

        else:  # fixed time
            raw_time_str = task.get('fixed_time', '').replace("，", ",").replace("\n", ",")
            target_strs = [t.strip() for t in raw_time_str.split(",") if t.strip()]

            if not target_strs: return now + 3600

            dt_now = datetime.datetime.now()
            candidates = []
            for t_str in target_strs:
                try:
                    th, tm = map(int, t_str.split(":"))
                    dt_target = dt_now.replace(hour=th, minute=tm, second=0, microsecond=0)
                    if dt_target.timestamp() > now:
                        candidates.append(dt_target.timestamp())
                    else:
                        candidates.append(dt_target.timestamp() + 24 * 3600)
                except:
                    pass

            if candidates:
                return min(candidates)
            return now + 60

    def scheduler_loop(self):
        self.log("调度器已启动，开始扫描任务...")

        with auto.UIAutomationInitializerInThread():
            self.automator = WeChatAutomator(self.log)
            self.automator.connect_wechat()
            if not self.automator.activate_window():
                self.stop_scheduler_ui()
                return

            while self.is_running:
                now = time.time()
                next_task = None

                sorted_tasks = sorted(self.tasks, key=lambda x: x['next_run'])

                for task in sorted_tasks:
                    if task.get('disabled', False): continue

                    if now >= task['next_run']:
                        self.execute_task(task)

                        if task.get('timer_mode') == 'once':
                            task['disabled'] = True
                            task['next_run'] = 0
                            self.log(f"任务 [{task['name']}] 已完成，自动停用。")
                        else:
                            task['next_run'] = self.calculate_next_run(task)

                        self.save_tasks_to_file()
                        self.refresh_task_list()
                        time.sleep(2)
                        break

                time.sleep(1)

        self.log("调度器已停止")
        self.stop_scheduler_ui()

    def execute_task(self, task):
        self.log(f"▶ 开始执行任务: {task['name']}")

        mode = task['mode_index']
        groups = task.get('groups', [])

        if not self.automator.activate_window(): return

        source_signature = None
        if mode == 0 and task.get('skip_duplicate', False):
            self.automator.search_and_click(task.get('source_name'))
            source_signature = self.automator.get_last_message_content()
            if source_signature:
                self.log(f"  [防重] 已获取源特征: {source_signature[:8]}...")

        for i, group in enumerate(groups):
            if not self.is_running: break

            self.log(f"  -> 处理目标: {group}")

            # --- 转发模式 ---
            if mode == 0:
                if task.get('skip_duplicate', False) and source_signature:
                    self.automator.search_and_click(group)
                    target_sig = self.automator.get_last_message_content()
                    if target_sig == source_signature:
                        self.log("    [跳过] 消息已存在")
                        continue
                    else:
                        self.automator.search_and_click(task.get('source_name'))
                        self.automator.forward_latest_message(group)
                else:
                    if i > 0:
                        self.automator.search_and_click(task.get('source_name'))
                    elif i == 0 and not task.get('skip_duplicate'):
                        self.automator.search_and_click(task.get('source_name'))
                    self.automator.forward_latest_message(group)

            # --- 文字+图片模式 ---
            elif mode == 1:
                self.automator.search_and_click(group)
                should_send = True

                text_msg = task.get('text_msg', '')
                image_paths = task.get('image_paths', [])

                if task.get('skip_duplicate_text', False):
                    last = self.automator.get_last_message_content()
                    if last == text_msg:
                        self.log("    [跳过] 文字已存在")
                        should_send = False

                if should_send:
                    # 1. 发送文字
                    if text_msg:
                        self.automator.send_paste_only(text_msg)
                        time.sleep(1)

                        # 2. 发送图片 (通过 PowerShell 设置剪贴板文件列表)
                    if image_paths:
                        self.log(f"    准备发送 {len(image_paths)} 张图片...")
                        success = self.automator.set_clipboard_files(image_paths)
                        if success:
                            self.automator.send_clipboard_images()

            # --- 文件模式 ---
            elif mode == 2:
                self.automator.send_file(group, task.get('file_path'))

            time.sleep(2)

        self.log(f"⏹ 任务 [{task['name']}] 执行完毕")

    def start_scheduler(self):
        if not self.tasks:
            messagebox.showwarning("提示", "任务列表为空，请先添加任务")
            return

        self.is_running = True
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")

        self.worker_thread = threading.Thread(target=self.scheduler_loop)
        self.worker_thread.daemon = True
        self.worker_thread.start()

    def stop_scheduler(self):
        self.is_running = False
        self.log("正在停止调度器...")

    def stop_scheduler_ui(self):
        def _reset():
            self.btn_start.config(state="normal")
            self.btn_stop.config(state="disabled")

        self.root.after(0, _reset)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()