from machine import Pin, SoftI2C
import ssd1306
from time import sleep
import json
import os

# ESP32 Pin assignment 
i2c = SoftI2C(scl=Pin(1), sda=Pin(3))

oled_width = 128
oled_height = 64

screen = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)


def get_alter_files(alters_dir):
    try:
        # 使用生成器表达式代替列表推导式，减少内存使用
        return sorted(f for f in os.listdir(alters_dir) if f.startswith('alter') and f.endswith('.txt'))
    except OSError:
        return []


def render_all_from_alters():
    alters_dir = 'alters'
    alter_files = get_alter_files(alters_dir)

    # 确保目录路径以斜杠结尾
    if not alters_dir.endswith('/'):
        alters_dir += '/'

    for filename in alter_files:
        file_path = alters_dir + filename
        try:
            with open(file_path, 'r') as f:
                alter_data = json.load(f)
            
            screen.fill(0)  # 清空屏幕
            for idx in alter_data:
                white_to_black = alter_data[idx][0]
                black_to_white = alter_data[idx][1]

                # 批量处理像素变更
                for x, y in white_to_black:
                    if 0 <= x < oled_width and 0 <= y < oled_height:
                        screen.pixel(x, y, 0)

                for x, y in black_to_white:
                    if 0 <= x < oled_width and 0 <= y < oled_height:
                        screen.pixel(x, y, 1)

            screen.show()  # 刷新屏幕
            print('2')
            sleep(1)  # 每帧之间延时 10ms
            
            # 显式删除大对象以释放内存
            del alter_data
        except Exception as e:
            print('Error processing', filename, ':', str(e))
            # 发生异常时也尝试释放内存
            try:
                del alter_data
            except:
                pass
#         except Exception:
#             pass  # 简化异常处理，节省内存

# 移除未使用的 render_from_alters 函数以节省内存

if __name__ == '__main__':
    print('1')
    render_all_from_alters()
    print('4')