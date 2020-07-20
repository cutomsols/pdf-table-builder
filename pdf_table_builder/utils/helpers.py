from pdf_table_builder.consts import TABLE_ROW_TYPE, TABLE_ROW_TYPE_REGULAR, TABLE_ROW_DATA, TABLE_COLUMN_CONTENT


def parse_obj_to_pdf_builder_data(obj, exclude_fields=None):
    if exclude_fields is None:
        exclude_fields = []
    data = []
    for field in obj._meta.fields:
        if field.name not in exclude_fields:
            field_value = getattr(obj, field.name)
            if field_value is None:
                field_value = '---'
            data.append({
                TABLE_ROW_TYPE: TABLE_ROW_TYPE_REGULAR,
                TABLE_ROW_DATA: [
                    {TABLE_COLUMN_CONTENT: field.verbose_name},
                    {TABLE_COLUMN_CONTENT: field_value},
                ]
            })
    return data
