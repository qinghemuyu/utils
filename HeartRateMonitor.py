import tkinter as tk
from tkinter import ttk
import asyncio
import logging
from bleak import BleakScanner, BleakClient
import threading
import pystray
from PIL import Image
import os

# 添加日志配置
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('heart_rate.log'),
        logging.StreamHandler()
    ]
)

class HeartRateMonitor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes('-alpha', 1.0)
        self.root.attributes('-topmost', True)
        
        # 添加置顶状态标志（默认为True）
        self.always_on_top = True
        self.click_through = False
        
        # 创建主Frame并添加拖动功能
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标题栏Frame - 在心率显示模式下隐藏
        self.title_frame = ttk.Frame(self.main_frame)
        self.title_frame.pack(fill=tk.X)
        
        # 修改拖动标签样式 - 在心率显示模式下隐藏
        self.drag_label = ttk.Label(self.title_frame, text="≡", cursor="fleur")
        self.drag_label.pack(side=tk.LEFT, padx=5)
        
        # 绑定拖动事件到更多控件
        for widget in [self.drag_label, self.main_frame, self.title_frame]:
            widget.bind('<ButtonPress-1>', self.on_drag_start)
            widget.bind('<B1-Motion>', self.on_drag_motion)
        
        # 设备选择界面
        self.device_frame = ttk.Frame(self.main_frame)
        self.device_frame.pack(fill=tk.BOTH, expand=True)
        
        self.refresh_button = ttk.Button(self.device_frame, text="刷新设备列表", command=self.refresh_devices)
        self.refresh_button.pack(pady=5)
        
        self.device_list = tk.Listbox(self.device_frame, font=('Arial', 12))
        self.device_list.bind('<<ListboxSelect>>', self.on_select)
        self.device_list.pack(pady=10)
        
        self.label = ttk.Label(self.device_frame, text="选择你的设备:", font=('Arial', 24))
        self.label.pack(padx=20, pady=20)
        
        # 心率显示界面（初始隐藏）
        self.heart_frame = ttk.Frame(self.main_frame)
        self.heart_frame.configure(style='Transparent.TFrame')
        
        # 使用普通的tk.Label代替ttk.Label以获得更好的字体渲染效果
        self.heart_rate_label = tk.Label(
            self.heart_frame,
            text="❤ -- BPM",
            font=('Arial', 36, 'bold'),
            foreground='red',
            bg='white'  # 设置背景色为白色（会被透明）
        )
        self.heart_rate_label.pack(padx=20, pady=20)
        
        # 给心率标签也添加拖动功能
        self.heart_rate_label.bind('<ButtonPress-1>', self.on_drag_start)
        self.heart_rate_label.bind('<B1-Motion>', self.on_drag_motion)
        
        # 创建系统托盘图标
        self.create_system_tray()
        
        # 创建新的事件循环
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.run_event_loop, daemon=True)
        self.thread.start()
        
        # 只在启动时扫描一次
        self.refresh_devices()
        
        self.client = None  # 添加客户端引用
        self.connected = False  # 添加连接状态标志

        # 修改样式配置
        self.style = ttk.Style()
        self.style.configure('Transparent.TFrame', background='white')
        self.style.configure('Transparent.TLabel', background='white')
        # 设置设备列表背景
        self.device_list.configure(bg='white')

        self.font_size = 36  # 默认字体大小

    def run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def refresh_devices(self):
        """手动刷新设备列表"""
        self.refresh_button.config(state=tk.DISABLED)
        self.label.config(text="正在扫描...")
        asyncio.run_coroutine_threadsafe(self.scan_devices(), self.loop)

    async def scan_devices(self):
        self.device_list.delete(0, tk.END)
        try:
            logging.info('正在扫描蓝牙设备...')
            devices = await BleakScanner.discover(timeout=3.0)
            logging.info(f'发现{len(devices)}个蓝牙设备')
            self.devices = devices
            
            for d in devices:
                if d.name:
                    def insert_device(device=d):
                        self.device_list.insert(tk.END, device.name)
                        logging.info(f'发现设备: {device.name}, 地址: {device.address}')
                    self.root.after(0, insert_device)
            
            # 扫描完成后更新UI
            def scan_complete():
                self.refresh_button.config(state=tk.NORMAL)
                self.label.config(text="选择你的设备:")
            self.root.after(0, scan_complete)

        except Exception as e:
            error_msg = str(e)
            logging.error(f'设备扫描失败: {error_msg}', exc_info=True)
            def update_error():
                self.label.config(text=f"错误: {error_msg}")
                self.refresh_button.config(state=tk.NORMAL)
            self.root.after(0, update_error)

    def on_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            device_name = event.widget.get(index)
            asyncio.run_coroutine_threadsafe(self.handle_connection(device_name), self.loop)

    def on_drag_start(self, event):
        self._drag_start_x = event.x_root - self.root.winfo_x()
        self._drag_start_y = event.y_root - self.root.winfo_y()

    def on_drag_motion(self, event):
        x = event.x_root - self._drag_start_x
        y = event.y_root - self._drag_start_y
        self.root.geometry(f'+{x}+{y}')

    def create_system_tray(self):
        try:
            icon_path = os.path.join(os.path.dirname(__file__), 'heart_icon.ico')
            image = Image.open(icon_path)
            
            # 创建字体大小子菜单
            font_menu = pystray.Menu(
                pystray.MenuItem("小", lambda: self.change_font_size(24), radio=True, checked=lambda item: self.font_size == 24),
                pystray.MenuItem("中", lambda: self.change_font_size(36), radio=True, checked=lambda item: self.font_size == 36),
                pystray.MenuItem("大", lambda: self.change_font_size(48), radio=True, checked=lambda item: self.font_size == 48),
                pystray.MenuItem("特大", lambda: self.change_font_size(64), radio=True, checked=lambda item: self.font_size == 64)
            )
            
            # 创建系统托盘菜单
            menu = (
                pystray.MenuItem("切换设备", self.show_device_selection),
                pystray.MenuItem("固定穿透", self.toggle_click_through, checked=lambda item: self.click_through),
                pystray.MenuItem("置于顶层", self.toggle_always_on_top, checked=lambda item: self.always_on_top),
                pystray.MenuItem("字体大小", font_menu),  # 添加字体大小子菜单
                pystray.MenuItem("退出", self.quit_app)
            )
            
            self.icon = pystray.Icon(
                "heart_rate_monitor",
                image,
                "心率监测器",
                menu
            )
            
            threading.Thread(target=self.icon.run, daemon=True).start()
            
        except Exception as e:
            logging.error(f"创建系统托盘图标失败: {str(e)}", exc_info=True)
            quit_button = ttk.Button(self.title_frame, text="×", command=self.quit_app)
            quit_button.pack(side=tk.RIGHT, padx=5)

    def quit_app(self, icon=None):  # 添加icon参数以兼容pystray的回调
        try:
            if self.connected:
                asyncio.run_coroutine_threadsafe(self.disconnect_device(), self.loop)
            if hasattr(self, 'icon'):
                self.icon.stop()
            self.root.quit()
        except Exception as e:
            logging.error(f"退出程序时发生错误: {str(e)}", exc_info=True)
            self.root.quit()  # 确保程序能够退出

    def toggle_always_on_top(self):
        """切换窗口置顶状态"""
        self.always_on_top = not self.always_on_top
        self.root.attributes('-topmost', self.always_on_top)
        
        # 如果启用了点击穿透，需要保持置顶
        if self.click_through and not self.always_on_top:
            self.root.attributes('-topmost', True)
            self.always_on_top = True

    def toggle_click_through(self):
        """切换点击穿透状态"""
        self.click_through = not self.click_through
        if self.heart_frame.winfo_ismapped():  # 只在心率显示模式下生效
            if self.click_through:
                # 启用点击穿透时强制置顶
                self.root.attributes('-transparentcolor', 'white')
                self.root.attributes('-topmost', True)
                self.root.wm_attributes('-disabled', True)
                self.always_on_top = True
            else:
                # 禁用点击穿透时恢复原来的置顶状态
                self.root.attributes('-transparentcolor', 'white')
                self.root.attributes('-topmost', self.always_on_top)
                self.root.wm_attributes('-disabled', False)

    def show_device_selection(self):
        def _show():
            if self.connected:
                asyncio.run_coroutine_threadsafe(self.disconnect_device(), self.loop)
            self.heart_frame.pack_forget()
            self.title_frame.pack(fill=tk.X)
            self.root.attributes('-transparentcolor', '')
            self.root.configure(bg='SystemButtonFace')
            # 禁用点击穿透
            self.root.wm_attributes('-disabled', False)
            self.device_frame.pack(fill=tk.BOTH, expand=True)
            self.device_list.config(state=tk.NORMAL)
            self.refresh_devices()
            self.root.deiconify()
            self.root.lift()
            self.root.attributes('-topmost', self.always_on_top)  # 恢复置顶状态
        
        self.root.after(0, _show)

    def show_heart_rate_display(self):
        self.device_frame.pack_forget()
        self.title_frame.pack_forget()
        self.root.configure(bg='white')
        self.root.attributes('-transparentcolor', 'white')
        # 使用当前字体大小
        self.heart_rate_label.configure(font=('Arial', self.font_size, 'bold'))
        self.heart_frame.pack(fill=tk.BOTH, expand=True)
        # 根据当前点击穿透状态设置窗口属性
        if self.click_through:
            self.root.wm_attributes('-disabled', True)
            self.root.attributes('-topmost', True)
        else:
            self.root.attributes('-topmost', self.always_on_top)
        self.root.update_idletasks()
        self.root.geometry('')

    async def handle_connection(self, device_name):
        logging.info(f'尝试连接设备: {device_name}')
        self.device_list.config(state=tk.DISABLED)
        self.label.config(text="连接中...")
        for d in self.devices:
            if d.name == device_name and any('0000180d' in uuid for uuid in d.metadata['uuids']):
                await self.connect_device(d)
                break

    def handle_heart_rate(self, sender, data):
        logging.info(f'接收到原始心率数据: {bytes(data)}')
        heart_rate = data[1]
        logging.info(f'解析得到心率值: {heart_rate} BPM')
        def update_ui():
            self.heart_rate_label.config(
                text=f"❤ {heart_rate} BPM",
                bg='white',
                font=('Arial', self.font_size, 'bold')  # 确保使用当前字体大小
            )
            if self.device_frame.winfo_ismapped():
                self.show_heart_rate_display()
        self.root.after(0, update_ui)

    async def disconnect_device(self):
        try:
            if self.client and self.client.is_connected:
                await self.client.disconnect()
                logging.info("设备已断开连接")
            self.connected = False
        except Exception as e:
            logging.error(f"断开连接时发生错误: {str(e)}")

    async def connect_device(self, device):
        logging.debug(f'尝试建立BLE连接，目标地址: {device.address}')
        try:
            self.client = BleakClient(device, timeout=10.0)  # 添加超时时间
            # 使用 asyncio.wait_for 添加连接超时
            await asyncio.wait_for(self.client.connect(), timeout=10.0)
            logging.info(f'成功连接设备: {device.address}')
            
            # 尝试启动心率通知，也添加超时
            try:
                await asyncio.wait_for(
                    self.client.start_notify(
                        "00002a37-0000-1000-8000-00805f9b34fb",
                        self.handle_heart_rate
                    ),
                    timeout=5.0
                )
                self.connected = True
                self.show_heart_rate_display()
                
                while self.connected:
                    await asyncio.sleep(1)
                    
            except asyncio.TimeoutError:
                logging.error("启动心率通知超时")
                await self.client.disconnect()
                raise Exception("获取心率数据失败，请确认是否为心率设备")
                
        except asyncio.TimeoutError:
            logging.error("连接设备超时")
            self.connected = False
            def update_timeout_error():
                self.label.config(text="连接超时，请重试")
                self.device_list.config(state=tk.NORMAL)
            self.root.after(0, update_timeout_error)
            
        except Exception as e:
            logging.error(f"连接设备时发生错误: {str(e)}")
            self.connected = False
            def update_error():
                self.label.config(text=f"连接错误: {str(e)}")
                self.device_list.config(state=tk.NORMAL)
            self.root.after(0, update_error)
            
        finally:
            if not self.connected and self.client:
                try:
                    await self.client.disconnect()
                except:
                    pass

    def change_font_size(self, size):
        """更改字体大小"""
        self.font_size = size
        self.heart_rate_label.configure(font=('Arial', size, 'bold'))
        # 调整窗口大小以适应新的字体大小
        if self.heart_frame.winfo_ismapped():
            self.root.update_idletasks()
            self.root.geometry('')

if __name__ == "__main__":
    app = HeartRateMonitor()
    app.root.mainloop()
