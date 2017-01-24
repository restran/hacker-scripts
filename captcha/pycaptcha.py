# -*- coding: utf-8 -*-
# Created by restran on 2016/8/12
"""
验证码识别
"""

from __future__ import unicode_literals, absolute_import
from io import BytesIO
from PIL import Image
import re
import os
import pytesseract

# 二值化，采用阈值分割法，threshold为分割点
threshold = 140
binary_table = []
for i in range(256):
    if i < threshold:
        binary_table.append(0)
    else:
        binary_table.append(1)

# 由于都是数字
# 对于识别成字母的 采用该表进行修正
replace_table = {
    'O': '0',
    'I': '1',
    'L': '1',
    'Z': '2',
    'S': '8'
}


def image_data_to_tiff(img, is_png=False):
    if is_png:
        img.load()
        # Make your background RGB, not RGBA
        # 将PNG转成JPG，PNG背景透明通道会干扰识别
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
        cf = BytesIO()
        background.save(cf, 'JPEG', quality=80)
        img = Image.open(cf)
    # 转换为灰度图
    img = img.convert('L')
    # img = binary_image(img)

    # 二值化
    img = img.point(binary_table, '1')
    # img.save('1.jpg')

    return img


def image_to_text(img, only_digits=False):
    text = pytesseract.image_to_string(img)
    text = re.sub('[\W]', '', text)
    text = text.strip()
    if only_digits:
        text = text.upper()
        for r in replace_table:
            text = text.replace(r, replace_table[r])
    return text


def recognize(file_name=None, img=None, is_png=False, only_digits=False):
    if img is None:
        img = Image.open(file_name)
    return image_to_text(image_data_to_tiff(img, is_png), only_digits=only_digits)


def get_file_list(path):
    if path == "":
        return []
    return [x for x in os.listdir(path) if os.path.isfile(os.path.join(path, x))]


def test_im(base_path):
    file_list = get_file_list(base_path)
    data_list = []
    result = 0
    for f in file_list:
        p = os.path.join(base_path, f)
        r = recognize(p, is_png=True, only_digits=True)
        print('%s:%s' % (p, r))
        data_list.append(r)
        a = int(f.replace('.png', ''))
        b = int(r)
        result += a * b
        print(result)
    print(result)
    return data_list


if __name__ == '__main__':
    data = test_im('d://im')
    # result = recognize('d://im//10042.png')
    # print(result)
