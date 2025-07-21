from PIL import Image
import os
import tqdm
import json



def image_to_hex_list(image_path):
    # 打开图片并调整为128x64尺寸
    img = Image.open(image_path)
    
    # 转换为灰度模式并调整尺寸（仅当尺寸不符时）
    img_gray = img.convert('L')
    if img_gray.size != (128, 64):
        img_gray = img_gray.resize((128, 64), Image.NEAREST)
    pixels = img_gray.getdata()
    
    hex_list = []
    binary_buffer = []
    
    for pixel in pixels:
        # 黑色(0)转为'0'，白色(非0)转为'1'
        bit = '0' if pixel == 0 else '1'
        binary_buffer.append(bit)
        
        # 每8位转换为一个十六进制数
        if len(binary_buffer) == 8:
            binary_str = ''.join(binary_buffer)
            int_value = int(binary_str, 2)
            hex_list.append(int_value)
            binary_buffer = []
    
    return hex_list


def process_images_and_save_batches(batch_threshold=255):
    # 定义图片文件夹和批次文件夹路径
    images_folder = os.path.join(os.path.dirname(__file__), 'images')
    batches_folder = os.path.join(os.path.dirname(__file__), 'batches')
    
    # 创建或确认 batches 文件夹存在
    os.makedirs(batches_folder, exist_ok=True)
    print(f'[INFO] 已创建或确认 batches 文件夹存在: {batches_folder}')
    
    # 获取 images 文件夹中的所有图片文件
    image_files = [f for f in os.listdir(images_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    total_images = len(image_files)
    print(f'[INFO] 找到 {total_images} 张图片')
    
    # 初始化批次和计数器
    batch = {} 
    batch_num = 1
    
    for idx, image_file in enumerate(tqdm.tqdm(image_files, desc='处理图片进度', unit='img', unit_scale=True, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]', leave=True), start=1):
        try:
            image_path = os.path.join(images_folder, image_file)
            hex_data = image_to_hex_list(image_path)
            batch[idx] = hex_data
        except Exception as e:
            print(f'[ERROR] 处理图片 {image_file} 时出错: {str(e)}')
            continue
        
        if idx % batch_threshold == 0 or idx == total_images:
            batch_file = os.path.join(batches_folder, f'batch{batch_num}.txt')
            with open(batch_file, 'w') as f:
                json.dump(batch, f)
            print(f'[INFO] 已保存批次 {batch_num} 到 {batch_file}')
            batch = {} 
            batch_num += 1
    
    print('[INFO] 所有图片处理完成')


def compare_batch_images_and_save_diffs():
    '''
    使用batches文件夹中的数据，比较前一个图片和后一个元素的像素区别，
    根据这些区别的像素位置（在128x64的屏幕上的x,y坐标，从上到下y从0开始增大到63，
    从左到右x从0开始增大到127）及更改类型（由白变黑或者由黑变白），
    重新输出一个新的字典，字典的每一项索引仍为编号，内容是一个列表，
    列表有两项，第一项存储由白转黑的像素的x、y坐标，
    第二项存储由黑转白的像素的x、y坐标，这些x、y坐标也用一个列表表示，比如[12,34]。
    字典的存储和打包方式和之前生成batches中的数据时的方式一样，但存储到alters文件夹中
    '''
    ########特别注意########
    #第一项存储由白1转黑0的像素的x、y坐标，
    #第二项存储由黑0转白1的像素的x、y坐标，

    # 定义批次文件夹和变更文件夹路径
    batches_folder = os.path.join(os.path.dirname(__file__), 'batches')
    alters_folder = os.path.join(os.path.dirname(__file__), 'alters')

    # 创建或确认 alters 文件夹存在
    os.makedirs(alters_folder, exist_ok=True)
    print(f'[INFO] 已创建或确认 alters 文件夹存在: {alters_folder}')
    
    # 获取 batches 文件夹中的所有批次文件
    batch_files = sorted([f for f in os.listdir(batches_folder) if f.startswith('batch') and f.endswith('.txt')])
    total_batches = len(batch_files)
    print(f'[INFO] 找到 {total_batches} 个批次文件')
    
    # 生成 128x64 纯黑画面的十六进制数据
    prev_hex_data = [0] * (128 * 64 // 8)

    for batch_idx, batch_file in enumerate(tqdm.tqdm(batch_files, desc='比较批次进度', unit='batch', unit_scale=True, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]', leave=True), start=1):
        batch_path = os.path.join(batches_folder, batch_file)
        with open(batch_path, 'r') as f:
            try:
                batch_data = json.load(f)
            except json.JSONDecodeError:
                print(f'[WARNING] 警告: 文件 {batch_file} 格式错误，跳过处理。')
                continue

        # 初始化变更数据和批次编号
        alter_data = {} 

        for idx in sorted(batch_data.keys()):
            current_hex_data = batch_data[idx]

            # 初始化变更列表
            white_to_black = []
            black_to_white = []

            # 将十六进制数据转换为二进制字符串
            prev_binary = ''.join([format(x, '08b') for x in prev_hex_data])
            current_binary = ''.join([format(x, '08b') for x in current_hex_data])

            for i in range(len(prev_binary)):
                prev_bit = prev_binary[i]
                current_bit = current_binary[i]

                if prev_bit != current_bit:
                    # 计算 x, y 坐标
                    y = i // 128
                    x = i % 128

                    if prev_bit == '1' and current_bit == '0':
                        white_to_black.append([x, y])
                    elif prev_bit == '0' and current_bit == '1':
                        black_to_white.append([x, y])

            alter_data[idx] = [white_to_black, black_to_white]
            prev_hex_data = current_hex_data

        # 保存变更数据到新的批次文件
        alter_file = os.path.join(alters_folder, batch_file.replace('batch', 'alter'))
        with open(alter_file, 'w') as f:
            json.dump(alter_data, f)
            print(f'[INFO] 已保存变更批次到 {alter_file}')
    
    print('[INFO] 所有批次图片差异比较完成')


if __name__ == "__main__":
    batch_threshold=255   # 指定字典打包到TXT的每批次字典项目数量，修改以适应单片机存储和处理性能
    
    process_images_and_save_batches(batch_threshold)
    compare_batch_images_and_save_diffs()
    #print(image_to_hex_list("image-00056.jpg"))