from django.contrib.admin.widgets import AdminFileWidget
from django.utils.html import mark_safe


class portraitImageWidget(AdminFileWidget):
    """自定义图片小部件，在文件输入框旁显示缩略图"""

    def render(self, name, value, attrs=None, renderer=None):
        output = []
        if value and getattr(value, "url", None):
            image_url = value.url
            output.append(
                f'<a href="{image_url}" target="_blank">'
                f'<img src="{image_url}" alt="{value}" width="30" style="object-fit: cover; margin-right: 10px;"/>'
                f'</a>'
            )
        # 调用父类的render方法，显示默认的文件选择和清除控件
        output.append(super().render(name, value, attrs, renderer))
        return mark_safe(''.join(output))


class mp3FileWidget(AdminFileWidget):
    def render(self, name, value, attrs=None, renderer=None):
        output = []
        if value and getattr(value, "url", None):
            mp3_url = value.url
            output.append(
                f'<a href="{mp3_url}" target="_blank">'
                f'<audio src="{mp3_url}" controls></audio>'
                f'</a>'
            )
        # 调用父类的render方法，显示默认的文件选择和清除控件
        output.append(super().render(name, value, attrs, renderer))
        return mark_safe(''.join(output))
