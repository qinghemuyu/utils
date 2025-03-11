import os
import subprocess
import logging
import platform
from functools import wraps
from flask import Flask, request, jsonify, render_template_string
import argparse
import hashlib
import secrets

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 默认配置
DEFAULT_CONFIG = {
    'PORT': 8080,
    'HOST': '0.0.0.0',
    'PASSWORD_HASH': None,  # 将在首次运行时设置
    'SECRET_KEY': secrets.token_hex(16),
    'MAX_COMMAND_LENGTH': 1000,
    'ALLOWED_COMMANDS': [],  # 空列表表示允许所有命令
    'BLACKLISTED_COMMANDS': ['rm', 'del', 'rmdir', 'mv', 'cut', 'format', 'fdisk', 'dd']  # 默认黑名单命令
}

# 全局配置对象
config = DEFAULT_CONFIG.copy()

# 密码验证装饰器
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': '需要认证'}), 401
        
        try:
            password = auth_header.split(' ')[1]
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            if password_hash != config['PASSWORD_HASH']:
                logger.warning(f'认证失败: 来自 {request.remote_addr} 的无效密码')
                return jsonify({'error': '认证失败'}), 401
                
            logger.info(f'认证成功: 来自 {request.remote_addr} 的请求')
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f'认证过程中出错: {str(e)}')
            return jsonify({'error': '认证过程中出错'}), 500
            
    return decorated

# 主页
@app.route('/')
def index():
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>命令执行服务</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .container { margin-top: 20px; }
            input, textarea, button { width: 100%; padding: 10px; margin-bottom: 10px; }
            button { background-color: #4CAF50; color: white; border: none; cursor: pointer; }
            button:hover { background-color: #45a049; }
            pre { background-color: #f5f5f5; padding: 10px; border-radius: 5px; white-space: pre-wrap; }
            .hidden { display: none; }
            .tab { overflow: hidden; border: 1px solid #ccc; background-color: #f1f1f1; }
            .tab button { background-color: inherit; float: left; border: none; outline: none; cursor: pointer; padding: 14px 16px; transition: 0.3s; width: auto; }
            .tab button:hover { background-color: #ddd; }
            .tab button.active { background-color: #ccc; }
            .tabcontent { display: none; padding: 6px 12px; border: 1px solid #ccc; border-top: none; }
            .tabcontent.active { display: block; }
        </style>
    </head>
    <body>
        <h1>命令执行服务</h1>
        <div class="tab">
            <button class="tablinks active" onclick="openTab(event, 'CommandTab')">执行命令</button>
            <button class="tablinks" onclick="openTab(event, 'TipTab')">系统提示</button>
        </div>
        
        <div id="CommandTab" class="tabcontent active">
            <div class="container">
                <input type="password" id="password" placeholder="输入密码" />
                <textarea id="command" rows="3" placeholder="输入要执行的命令"></textarea>
                <button onclick="executeCommand()">执行命令</button>
                <div id="result" class="hidden">
                    <h3>执行结果:</h3>
                    <pre id="output"></pre>
                </div>
            </div>
        </div>
        
        <div id="TipTab" class="tabcontent">
            <div class="container">
                <input type="password" id="tip-password" placeholder="输入密码" />
                <textarea id="tip-content" rows="3" placeholder="输入要提示的内容"></textarea>
                <button onclick="showTip()">显示提示</button>
                <div id="tip-result" class="hidden">
                    <h3>提示结果:</h3>
                    <pre id="tip-output"></pre>
                </div>
            </div>
        </div>

        <script>
            function executeCommand() {
                const password = document.getElementById('password').value;
                const command = document.getElementById('command').value;
                const resultDiv = document.getElementById('result');
                const output = document.getElementById('output');
                
                if (!password || !command) {
                    alert('请输入密码和命令');
                    return;
                }
                
                fetch('/api/execute', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + password
                    },
                    body: JSON.stringify({ command: command })
                })
                .then(response => response.json())
                .then(data => {
                    resultDiv.classList.remove('hidden');
                    if (data.error) {
                        output.textContent = '错误: ' + data.error;
                    } else {
                        output.textContent = data.output;
                    }
                })
                .catch(error => {
                    resultDiv.classList.remove('hidden');
                    output.textContent = '请求错误: ' + error;
                });
            }
            
            function showTip() {
                const password = document.getElementById('tip-password').value;
                const tipContent = document.getElementById('tip-content').value;
                const resultDiv = document.getElementById('tip-result');
                const output = document.getElementById('tip-output');
                
                if (!password || !tipContent) {
                    alert('请输入密码和提示内容');
                    return;
                }
                
                fetch('/api/tip', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + password
                    },
                    body: JSON.stringify({ content: tipContent })
                })
                .then(response => response.json())
                .then(data => {
                    resultDiv.classList.remove('hidden');
                    if (data.error) {
                        output.textContent = '错误: ' + data.error;
                    } else {
                        output.textContent = data.message;
                    }
                })
                .catch(error => {
                    resultDiv.classList.remove('hidden');
                    output.textContent = '请求错误: ' + error;
                });
            }
            
            function openTab(evt, tabName) {
                // 隐藏所有标签内容
                var tabcontents = document.getElementsByClassName("tabcontent");
                for (var i = 0; i < tabcontents.length; i++) {
                    tabcontents[i].classList.remove("active");
                }
                
                // 移除所有标签按钮的活动状态
                var tablinks = document.getElementsByClassName("tablinks");
                for (var i = 0; i < tablinks.length; i++) {
                    tablinks[i].classList.remove("active");
                }
                
                // 显示当前标签，并添加活动状态到按钮
                document.getElementById(tabName).classList.add("active");
                evt.currentTarget.classList.add("active");
            }
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)

# API端点 - 执行命令
@app.route('/api/execute', methods=['POST'])
@require_auth
def execute_command():
    try:
        data = request.get_json()
        if not data or 'command' not in data:
            return jsonify({'error': '缺少命令参数'}), 400
            
        command = data['command']
        
        # 命令长度检查
        if len(command) > config['MAX_COMMAND_LENGTH']:
            logger.warning(f'命令过长: {len(command)} 字符')
            return jsonify({'error': f'命令过长，最大允许 {config["MAX_COMMAND_LENGTH"]} 字符'}), 400
            
        # 如果配置了允许的命令列表，检查命令是否在列表中
        if config['ALLOWED_COMMANDS'] and not any(command.startswith(cmd) for cmd in config['ALLOWED_COMMANDS']):
            logger.warning(f'尝试执行未授权的命令: {command}')
            return jsonify({'error': '未授权的命令'}), 403
        
        # 检查命令是否包含黑名单中的命令
        command_lower = command.lower()
        for blacklisted_cmd in config['BLACKLISTED_COMMANDS']:
            if blacklisted_cmd in command_lower:
                logger.warning(f'尝试执行黑名单命令: {command}')
                return jsonify({'error': f'禁止执行包含 "{blacklisted_cmd}" 的命令'}), 403
            
        logger.info(f'执行命令: {command}')
        
        # 执行命令并获取输出
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout
        error = result.stderr
        
        if result.returncode != 0:
            logger.warning(f'命令执行失败，返回码: {result.returncode}, 错误: {error}')
            return jsonify({'output': output, 'error': error, 'returncode': result.returncode})
            
        logger.info('命令执行成功')
        return jsonify({'output': output, 'returncode': result.returncode})
        
    except Exception as e:
        logger.error(f'执行命令时出错: {str(e)}')
        return jsonify({'error': f'执行命令时出错: {str(e)}'}), 500

# API端点 - 显示提示
@app.route('/api/tip', methods=['POST'])
@require_auth
def show_tip():
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'error': '缺少提示内容'}), 400
            
        content = data['content']
        
        # 检查提示内容长度
        if len(content) > config['MAX_COMMAND_LENGTH']:
            logger.warning(f'提示内容过长: {len(content)} 字符')
            return jsonify({'error': f'提示内容过长，最大允许 {config["MAX_COMMAND_LENGTH"]} 字符'}), 400
        
        logger.info(f'显示提示: {content}')
        
        # 根据不同操作系统显示提示
        system = platform.system()
        message = ''
        
        try:
            if system == 'Windows':
                # Windows系统使用PowerShell显示通知
                ps_script = f'powershell -Command "[System.Reflection.Assembly]::LoadWithPartialName(\'System.Windows.Forms\'); [System.Windows.Forms.MessageBox]::Show(\'{content}\')"'
                subprocess.run(ps_script, shell=True)
                message = '已在Windows系统上显示提示'
            elif system == 'Linux':
                # 尝试使用notify-send (需要安装libnotify-bin)
                try:
                    subprocess.run(['notify-send', 'System Notification', content], check=False)
                    message = '已使用桌面通知显示提示'
                except FileNotFoundError:
                    # 如果notify-send不可用，尝试使用终端输出
                    subprocess.run(['echo', f'\\033[1;31m提示: {content}\\033[0m'], shell=True)
                    message = '已在终端显示提示'
            elif system == 'Darwin':  # macOS
                # 使用osascript显示通知
                applescript = f'display notification "{content}" with title "系统通知"'
                subprocess.run(['osascript', '-e', applescript], check=False)
                message = '已在macOS系统上显示提示'
            else:
                # 未知系统，使用日志记录
                logger.info(f'系统提示: {content}')
                message = f'未知系统类型 {system}，已记录提示到日志'
                
            logger.info(f'提示显示成功: {message}')
            return jsonify({'message': message, 'success': True})
            
        except Exception as e:
            error_msg = f'显示提示时出错: {str(e)}'
            logger.error(error_msg)
            return jsonify({'error': error_msg, 'message': '尝试显示提示失败，请查看日志'}), 500
            
    except Exception as e:
        logger.error(f'处理提示请求时出错: {str(e)}')
        return jsonify({'error': f'处理提示请求时出错: {str(e)}'}), 500
        
# 设置初始密码

# 设置初始密码
def setup_password():
    if not config['PASSWORD_HASH']:
        password = secrets.token_urlsafe(12)  # 生成一个随机密码
        config['PASSWORD_HASH'] = hashlib.sha256(password.encode()).hexdigest()
        print(f"\n初始密码已生成: {password}")
        print(f"密码哈希: {config['PASSWORD_HASH']}")
        print("请保存此密码，它只会显示一次！\n")
    else:
        print(f"\n使用现有密码哈希: {config['PASSWORD_HASH']}\n")

# 解析命令行参数
def parse_args():
    parser = argparse.ArgumentParser(description='带密码验证的命令执行服务')
    parser.add_argument('--port', type=int, default=DEFAULT_CONFIG['PORT'], help='服务监听端口')
    parser.add_argument('--host', type=str, default=DEFAULT_CONFIG['HOST'], help='服务监听地址')
    parser.add_argument('--password', type=str, help='设置访问密码（将会被哈希存储）')
    parser.add_argument('--max-command-length', type=int, default=DEFAULT_CONFIG['MAX_COMMAND_LENGTH'], 
                        help='最大命令长度')
    parser.add_argument('--allowed-commands', type=str, nargs='+', help='允许执行的命令前缀列表')
    parser.add_argument('--blacklisted-commands', type=str, nargs='+', help='禁止执行的命令关键词列表')
    
    args = parser.parse_args()
    
    # 更新配置
    config['PORT'] = args.port
    config['HOST'] = args.host
    config['MAX_COMMAND_LENGTH'] = args.max_command_length
    
    if args.allowed_commands:
        config['ALLOWED_COMMANDS'] = args.allowed_commands
        print(f"允许的命令前缀: {', '.join(args.allowed_commands)}")
        
    if args.blacklisted_commands:
        config['BLACKLISTED_COMMANDS'] = args.blacklisted_commands
        print(f"黑名单命令关键词: {', '.join(args.blacklisted_commands)}")
    else:
        print(f"使用默认黑名单命令关键词: {', '.join(config['BLACKLISTED_COMMANDS'])}")
    
    if args.password:
        config['PASSWORD_HASH'] = hashlib.sha256(args.password.encode()).hexdigest()
        print(f"已设置自定义密码，哈希值: {config['PASSWORD_HASH']}")

# 主函数
def main():
    parse_args()
    setup_password()
    
    print(f"启动服务于 {config['HOST']}:{config['PORT']}")
    print(f"可通过浏览器访问 http://{config['HOST'] if config['HOST'] != '0.0.0.0' else 'localhost'}:{config['PORT']}/")
    
    app.secret_key = config['SECRET_KEY']
    app.run(host=config['HOST'], port=config['PORT'])

if __name__ == '__main__':
    main()
