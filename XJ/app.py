from flask import Flask, request, jsonify, send_from_directory
import pyodbc
import os
from PIL import Image, ImageDraw, ImageFont
import datetime
import random
import io
import base64

app = Flask(__name__)

# SQL Server配置
server = 'localhost'
database = 'DonationDB'
username = 'sa'
password = '123456'
driver = '{ODBC Driver 11 for SQL Server}'  # 使用系统中已有的驱动

# 连接字符串
connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'

@app.route('/')
def index():
    return send_from_directory(os.path.join(app.root_path, ''), 'index.html')

@app.route('/verify.html')
def verify_page():
    return send_from_directory(os.path.join(app.root_path, ''), 'verify.html')

@app.route('/submit_message.html')
def submit_message_page():
    return send_from_directory(os.path.join(app.root_path, ''), 'submit_message.html')

@app.route('/show_message.html')
def show_message_page():
    return send_from_directory(os.path.join(app.root_path, ''), 'show_message.html')

@app.route('/certificate.html')
def certificate_page():
    return send_from_directory(os.path.join(app.root_path, ''), 'certificate.html')

@app.route('/admin.html')
def admin_page():
    return send_from_directory(os.path.join(app.root_path, ''), 'admin.html')


@app.route('/verify', methods=['POST'])
def verify_order_number():
    data = request.get_json()
    order_number = data.get('orderNumber')

    try:
        # 连接数据库
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        cursor.execute("SELECT id, Flag FROM dbo.Users WHERE OrderNumber = ? COLLATE SQL_Latin1_General_CP1_CS_AS", order_number)
        result = cursor.fetchone()

        if result:
            user_id = result.id
            if result.Flag == 1:
                return jsonify(success=False, message='该订单已提交过留言')
            return jsonify(success=True, message='身份验证成功', userId=user_id)
        else:
            return jsonify(success=False, message='身份验证失败')
    except Exception as e:
        print(f"SQL error: {e}")
        return jsonify(success=False, message='服务器错误')
    finally:
        cursor.close()
        conn.close()

@app.route('/submit_message', methods=['POST'])
def submit_message():
    data = request.get_json()
    name = data.get('name')
    message = data.get('message')
    user_id = data.get('userId')

    try:
        # 连接数据库
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO dbo.Messages (Name, Message, UserId) VALUES (?, ?, ?)", name, message, user_id)
        conn.commit()

        # 更新用户的Flag状态
        cursor.execute("UPDATE dbo.Users SET Flag = 1 WHERE id = ?", user_id)
        conn.commit()

        cursor.execute("SELECT TOP 1 Id, Name, Message FROM dbo.Messages ORDER BY Id DESC")
        last_message = cursor.fetchone()

        new_message = {"id": last_message.Id, "name": last_message.Name, "message": last_message.Message}
        return jsonify(success=True, message='留言提交成功', new_message=new_message)
    except Exception as e:
        print(f"SQL error: {e}")
        return jsonify(success=False, message='留言提交失败')
    finally:
        cursor.close()
        conn.close()

@app.route('/get_messages', methods=['GET'])
def get_messages():
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        cursor.execute("SELECT Name, Message FROM dbo.Messages ORDER BY Id DESC")
        rows = cursor.fetchall()

        messages = [{"name": row.Name, "message": row.Message} for row in rows]
        return jsonify(success=True, messages=messages)
    except Exception as e:
        print(f"SQL error: {e}")
        return jsonify(success(False, message='无法获取留言'))
    finally:
        cursor.close()
        conn.close()

@app.route('/generate_certificate', methods=['POST'])
def generate_certificate():
    try:
        data = request.get_json()
        user_name = data.get('name')
        message_id = data.get('message_id')
        order_number = data.get('order_number')  # 获取订单号

        # 检查 message_id 是否正确传递
        if not message_id:
            print("Message ID 未传递")
            return jsonify(success=False, message='Message ID 未传递')

        # 打开海报图片
        poster_path = './玺佳海报模板.jpg'
        poster = Image.open(poster_path)

        font_path = "./fonts/思源宋体Medium.otf"
        font_size = 58
        font = ImageFont.truetype(font_path, font_size)

        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # 检查订单号是否为特定的订单号
        if order_number == '0827':
            random_number = '0827'
        else:
            # 获取已用的随机数
            cursor.execute("SELECT CertificateNumber FROM dbo.CertificateNumbers")
            used_numbers = [row.CertificateNumber for row in cursor.fetchall()]

            # 生成不重复的随机数
            available_numbers = set(range(0, 8888)) - set(used_numbers) - {'0827'}
            if not available_numbers:
                return jsonify(success=False, message='无可用随机数')

            random_number = "{:04}".format(random.choice(list(available_numbers)))
        
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")

        draw = ImageDraw.Draw(poster)
        name_position = (550, 815)
        number_position = (960, 1010)
        date_position = (560, 1690)

        draw.text(name_position, user_name, font=font, fill="black")
        draw.text(number_position, str(random_number), font=font, fill="black")
        draw.text(date_position, current_date, font=font, fill="black")

        buffered = io.BytesIO()
        poster.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        # 将随机数和留言ID写入CertificateNumbers表
        print(f"Inserting Certificate Number: {random_number} with Message ID: {message_id}")
        cursor.execute("INSERT INTO dbo.CertificateNumbers (CertificateNumber, MessageId) VALUES (?, ?)", random_number, message_id)
        conn.commit()

        return jsonify(success=True, image_data=img_str)
    except Exception as e:
        print(f"Error generating certificate: {e}")
        return jsonify(success=False, message='生成证书失败')
    finally:
        cursor.close()
        conn.close()



@app.route('/get_all_messages', methods=['GET'])
def get_all_messages():
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        cursor.execute("SELECT Id, Name, Message FROM dbo.Messages ORDER BY Id DESC")
        rows = cursor.fetchall()

        messages = [{"id": row.Id, "name": row.Name, "message": row.Message} for row in rows]
        return jsonify(success=True, messages=messages)
    except Exception as e:
        print(f"SQL error: {e}")
        return jsonify(success=False, message='无法获取留言')
    finally:
        cursor.close()
        conn.close()

@app.route('/delete_messages', methods=['POST'])
def delete_messages():
    data = request.get_json()
    message_ids = data.get('message_ids')

    if not message_ids:
        return jsonify(success=False, message='没有指定要删除的留言')

    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dbo.Messages WHERE Id IN ({})".format(','.join('?' * len(message_ids))), message_ids)
        conn.commit()
        return jsonify(success=True, message='留言删除成功')
    except Exception as e:
        print(f"SQL error: {e}")
        return jsonify(success=False, message='删除留言失败')
    finally:
        cursor.close()
        conn.close()


@app.route('/styles.css')
def styles():
    return send_from_directory(os.path.join(app.root_path, ''), 'styles.css')

@app.route('/img/<path:filename>')
def img(filename):
    return send_from_directory(os.path.join(app.root_path, 'img'), filename)

@app.route('/fonts/<path:filename>')
def fonts(filename):
    return send_from_directory(os.path.join(app.root_path, 'fonts'), filename)

if __name__ == '__main__':
    app.run(debug=True, host='192.168.11.190', port=5000)
