from import_export import resources
from import_export.fields import Field
from datetime import timedelta

from .models import CtItem


class CtItemResource(resources.ModelResource):
    # lingyu = Field(attribute='lingyu__name', column_name='子领域')
    # index = Field(attribute='index', column_name='序号')
    chinese = Field(attribute='chinese', column_name='汉语')
    english = Field(attribute='english', column_name='英语')
    swahili = Field(attribute='swahili', column_name='斯语')
    xieyin = Field(attribute='xieyin', column_name='汉语谐音')

    # status = Field(attribute='get_status_display', column_name='状态')

    class Meta:
        model = CtItem
        # exclude = ('id',)
        # import_id_fields = ['index', 'swahili']
        import_id_fields = ['chinese', 'english', 'swahili']
        # import_id_fields = ['swahili']
        fields = [
            # 'index',
            'chinese', 'english', 'swahili', 'xieyin'
            # ,'status'
        ]
