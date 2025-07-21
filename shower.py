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
    if not os.path.exists(alters_dir):
        return []
    return [os.path.join(alters_dir, filename) for filename in os.listdir(alters_dir)]


def read_alter_data(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"读取文件 {file_path} 出错: {str(e)}")
        return None


def is_valid_pixel_data(item):
    return isinstance(item, dict) and 'x' in item and 'y' in item and 'n' in item


def apply_pixel_changes(data):
    if isinstance(data, list):
        for item in data:
            if is_valid_pixel_data(item):
                screen.pixel(item['x'], item['y'], item['n'])


def render_from_alters(alter_file_path):
    """
    根据指定的 alters 文件中的变更数据实现单次 LED 屏幕渲染。

    :param alter_file_path: alters 文件的路径
    """
    try:
        # 验证文件路径是否在 alters 目录下
        if not os.path.abspath(alter_file_path).startswith(os.path.abspath('alters')):
            raise ValueError("非法的文件路径")
        with open(alter_file_path, 'r') as f:
            alter_data = json.load(f)

        for idx in alter_data:
            white_to_black = alter_data[idx][0]
            black_to_white = alter_data[idx][1]

            # 设置由白转黑的像素
            for pixel_coord in white_to_black:
                x, y = pixel_coord
                if 0 <= x < oled_width and 0 <= y < oled_height:
                    screen.pixel(x, y, 0)

            # 设置由黑转白的像素
            for pixel_coord in black_to_white:
                x, y = pixel_coord
                if 0 <= x < oled_width and 0 <= y < oled_height:
                    screen.pixel(x, y, 1)

        screen.show()
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"渲染出错: {str(e)}")


def render_all_from_alters():
    alters_dir = 'alters'
    alter_files = get_alter_files(alters_dir)
    for file_path in alter_files:
        data = read_alter_data(file_path)
        if data is not None:
            screen.fill(0)  # 清空屏幕
            apply_pixel_changes(data)
            screen.show()  # 每帧渲染后刷新屏幕
            sleep(0.01)  # 每帧之间延时 10ms

if __name__ == '__main__':
    render_all_from_alters()