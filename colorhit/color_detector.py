import pyautogui
from PIL import ImageGrab
import time
import json
import keyboard
import os
import threading
from pynput.mouse import Listener

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'color_config.json')
    default_config = {
        "r_threshold": 150,
        "g_threshold": 100,
        "b_threshold": 100,
        "area_size": 30,
        "step": 2
    }
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("配置文件不存在，创建默认配置文件")
        try:
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config
        except Exception as e:
            print(f"创建配置文件失败: {e}")
            return default_config
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return default_config

def save_config(config):
    config_path = os.path.join(os.path.dirname(__file__), 'color_config.json')
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        print("颜色配置已保存")
    except Exception as e:
        print(f"保存配置文件失败: {e}")

def pick_color():
    print("进入取色模式，移动鼠标并点击以选择颜色...")
    picking = True
    result = None

    def get_screen_color(x, y):
        screen = ImageGrab.grab()
        width, height = screen.size
        if x < 0 or x >= width or y < 0 or y >= height:
            return None
        try:
            return screen.getpixel((x, y))
        except Exception as e:
            print(f"\r获取颜色失败: {e}")
            return None

    def on_click(x, y, button, pressed):
        nonlocal picking, result
        if pressed:
            color = get_screen_color(x, y)
            if color:
                r, g, b = color
                print(f"\r已选择颜色: R={r}, G={g}, B={b}")
                result = (r, g, b)
                picking = False
            else:
                print("\r无法获取当前位置的颜色，请在屏幕范围内选择")
            return False

    def show_current_color():
        while picking:
            try:
                x, y = pyautogui.position()
                color = get_screen_color(x, y)
                if color:
                    r, g, b = color
                    print(f"\r当前位置颜色: R={r}, G={g}, B={b}", end='')
                else:
                    print("\r当前位置超出屏幕范围", end='')
                time.sleep(0.1)
            except Exception as e:
                print(f"\r显示颜色时出错: {e}", end='')
                time.sleep(0.1)

    from pynput.mouse import Listener
    import threading

    color_thread = threading.Thread(target=show_current_color)
    color_thread.daemon = True
    color_thread.start()

    with Listener(on_click=on_click) as listener:
        listener.join()

    print()  # 换行
    return result

def is_target_color_present(image, config):
    width, height = image.size
    center_x = width // 2
    center_y = height // 2
    area_size = config['area_size']
    step = config['step']
    
    for x in range(center_x - area_size, center_x + area_size, step):
        for y in range(center_y - area_size, center_y + area_size, step):
            r, g, b = image.getpixel((x, y))
            if (abs(r - config['r_threshold']) < 20 and
                abs(g - config['g_threshold']) < 20 and
                abs(b - config['b_threshold']) < 20):
                return True
    return False

def main():
    config = load_config()
    print("按P键进行屏幕取色，按Ctrl+C停止运行")
    try:
        while True:
            if keyboard.is_pressed('p'):
                r, g, b = pick_color()
                config.update({
                    'r_threshold': r,
                    'g_threshold': g,
                    'b_threshold': b
                })
                save_config(config)
                print("按任意键继续...")
                keyboard.read_event(suppress=True)

            screen = ImageGrab.grab()
            if is_target_color_present(screen, config):
                pyautogui.click()
            
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("程序已停止")

if __name__ == "__main__":
    # 添加短暂延迟，有时间切换到目标窗口
    print("程序将在3秒后启动...")
    time.sleep(3)
    main()
