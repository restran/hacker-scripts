# -*- coding: utf-8 -*-
# created by restran on 2016/12/30
from __future__ import unicode_literals, absolute_import

"""
识别相似图片
"""

from PIL import Image
from PIL import ImageFilter
from PIL import ImageOps
from os import walk
import os

# 当前目录所在路径
BASE_PATH = os.path.abspath(os.path.dirname(__file__))
# 临时文件所在目录
TMP_PATH = os.path.join(BASE_PATH, 'tmp')
TMP_DATA_PATH = os.path.join(BASE_PATH, 'tmp_data')


# This module can classify the image by Average Hash Method
# The Hash Method is too strict,so this module suitable for finding image by Thumbnail
#
class SimilarImageHash(object):
    @classmethod
    def get_code(cls, img, size):
        pixel = []
        for x in range(0, size[0]):
            for y in range(0, size[1]):
                pixel_value = img.getpixel((x, y))
                pixel.append(pixel_value)

        avg = sum(pixel) / len(pixel)

        cp = []

        for px in pixel:
            if px > avg:
                cp.append(1)
            else:
                cp.append(0)
        return cp

    @classmethod
    def compare_code(cls, code1, code2):
        num = 0
        for index in range(0, len(code1)):
            if code1[index] != code2[index]:
                num += 1
        return num

    @classmethod
    def classify_ahash(cls, image1, image2, size=(8, 8), exact=25):
        """ 'image1' and 'image2' is a Image Object.
        You can build it by 'Image.open(path)'.
        'Size' is parameter what the image will resize to it and then image will be compared by the algorithm.
        It's 8 * 8 when it default.
        'exact' is parameter for limiting the Hamming code between 'image1' and 'image2',it's 25 when it default.
        The result become strict when the exact become less.
        This function return the true when the 'image1'  and 'image2' are similar.
        """
        image1 = image1.resize(size).convert('L').filter(ImageFilter.BLUR)
        image1 = ImageOps.equalize(image1)
        code1 = cls.get_code(image1, size)
        image2 = image2.resize(size).convert('L').filter(ImageFilter.BLUR)
        image2 = ImageOps.equalize(image2)
        code2 = cls.get_code(image2, size)

        assert len(code1) == len(code2), "error"

        return cls.compare_code(code1, code2)


class SimilarImage(object):
    """
    用平均哈希法，并把图片分隔成16个小块，然后分别比较，最后综合比较结果，从而提高比较的准确率。
    """

    @classmethod
    def calculate(cls, image1, image2):
        g = image1.histogram()
        s = image2.histogram()
        assert len(g) == len(s), "error"

        data = []

        for index in range(0, len(g)):
            if g[index] != s[index]:
                data.append(1 - abs(g[index] - s[index]) / max(g[index], s[index]))
            else:
                data.append(1)

        return sum(data) / len(g)

    @classmethod
    def split_image(cls, image, part_size):
        print('分割样本图片')
        pw, ph = part_size
        w, h = image.size

        sub_image_list = []

        assert w % pw == h % ph == 0, "error"

        for i in range(0, w, pw):
            for j in range(0, h, ph):
                sub_image = image.crop((i, j, i + pw, j + ph)).copy()
                sub_image_list.append(sub_image)

        return sub_image_list

    @classmethod
    def do_merge_image(cls, merge_size, image_list):
        print('开始合并图片')
        w, h, pw, ph = merge_size

        assert w % pw == h % ph == 0, "error"
        image = Image.new("RGB", (w, h), (0, 0, 0))

        index = 0
        for i in range(0, w, pw):
            for j in range(0, h, ph):
                f_name = os.path.join(TMP_PATH, image_list[index][1])
                region = Image.open(f_name)
                image.paste(region, (i, j, i + pw, j + ph))
                index += 1

        image.save('out.jpg', 'JPEG')

    @classmethod
    def classify_histogram_with_split(cls, image1, image2, size=(256, 256), part_size=(64, 64)):
        """
        'image1' and 'image2' is a Image Object.
        You can build it by 'Image.open(path)'.
        'Size' is parameter what the image will resize to it.It's 256 * 256 when it default.
        'part_size' is size of piece what the image will be divided.It's 64*64 when it default.
        This function return the similarity rate between 'image1' and 'image2'
        """
        image1 = image1.resize(size).convert("RGB")
        sub_image1 = cls.split_image(image1, part_size)

        image2 = image2.resize(size).convert("RGB")
        sub_image2 = cls.split_image(image2, part_size)

        sub_data = 0
        for im1, im2 in zip(sub_image1, sub_image2):
            sub_data += cls.calculate(im1, im2)

        x = size[0] / part_size[0]
        y = size[1] / part_size[1]

        pre = round((sub_data / (x * y)), 3)
        return pre

    @classmethod
    def load_data_images(cls):
        image_list = []
        for root, dirs, files in walk(TMP_DATA_PATH):
            for f in files:
                if not root.endswith('/'):
                    f_name = root + '/' + f
                else:
                    f_name = root + f

                try:
                    image = Image.open(f_name)
                    image_list.append([image, f])
                except Exception as e:
                    pass
        return image_list

    @classmethod
    def find_similar_image(cls, image, data_images):
        result = [[SimilarImageHash.classify_ahash(image, t[0]), t[1]] for t in data_images]
        max_value = result[0]
        max_i = 0
        for i, t in enumerate(result):
            if t[0] > max_value[0]:
                max_value = t
                max_i = i

        data_images.pop(max_i)
        return max_value

    @classmethod
    def merge_image(cls, image, part_size):
        sub_images = cls.split_image(image, part_size)
        image_list = []
        data_images = cls.load_data_images()
        for t in sub_images:
            image_list.append(cls.find_similar_image(t, data_images))

        merge_size = (X_WIDTH * X_SIZE, Y_HEIGHT * Y_SIZE, X_WIDTH, Y_HEIGHT)
        cls.do_merge_image(merge_size, image_list)

    @classmethod
    def small_data_image(cls, dir_name, part_size):
        if not os.path.exists(TMP_PATH):
            os.makedirs(TMP_PATH)
        if not os.path.exists(TMP_DATA_PATH):
            os.makedirs(TMP_DATA_PATH)
        x, y = part_size
        size = (X_WIDTH, X_WIDTH / x * y)
        for root, dirs, files in walk(dir_name):
            for f in files:
                output_file1 = os.path.join(TMP_DATA_PATH, f)
                output_file2 = os.path.join(TMP_PATH, f)
                if not root.endswith('/'):
                    f_name = root + '/' + f
                else:
                    f_name = root + f

                try:
                    image = Image.open(f_name)
                    image1, image2 = cls.scale_image(image, part_size, size)

                    image1.save(output_file1, 'JPEG')
                    image2.save(output_file2, 'JPEG')
                except Exception as e:
                    pass

        return

    @classmethod
    def scale_image(cls, image, part_size, size):
        """
        等比例缩放并裁剪图片
        :param part_size:
        :param image:
        :param size:
        :return:
        """
        width, height = image.size
        x = width
        y = x * part_size[1] / part_size[0]

        if y > height:
            y = height
            x = y * part_size[0] / part_size[1]

        # 先按size的比例进行裁剪
        box = (
            (width - x) / 2,
            (height - y) / 2,
            x + (width - x) / 2,
            y + (height - y) / 2)
        # 然后缩放图片
        crop_image = image.crop(box)
        image1 = crop_image.resize(part_size, resample=Image.BILINEAR)
        image2 = crop_image.resize(size, resample=Image.BILINEAR)
        return image1, image2


# x 方向要用多少个
X_SIZE = 25
X_WIDTH = 300

Y_SIZE = None
Y_HEIGHT = None

# 所选择拼接的图片，x和y的比例
size_ratio = (1, 1)

input_file = 'img.jpg'

to_find_image_dir = '/Users/restran/Desktop/data'


def main():
    image = Image.open(input_file)
    width, height = image.size

    x = width / X_SIZE
    y = x * size_ratio[1] / size_ratio[0]

    y_size = height / y
    global Y_SIZE
    global Y_HEIGHT
    Y_SIZE = y_size
    Y_HEIGHT = X_WIDTH / x * y

    crop_width = x * X_SIZE
    crop_height = y * y_size
    box = ((width - crop_width) / 2,
           (height - crop_height) / 2,
           crop_width + (width - crop_width) / 2,
           crop_height + (height - crop_height) / 2)
    # 缩放图片
    region = image.crop(box)
    part_size = (x, y)

    SimilarImage.small_data_image(to_find_image_dir, part_size)
    SimilarImage.merge_image(region, part_size)
    print('完成')
    # image.resize()


if __name__ == '__main__':
    main()
