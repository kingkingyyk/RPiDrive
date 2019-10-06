from django import template

register = template.Library()


file_ext_icon_dict = {
    'is_picture': 'photo',
    'is_music': 'music_note',
    'is_movie': 'movie',
    'is_code': 'code',
    'is_compressed': 'archive',
    'is_executable': 'apps',
    'is_library': 'library_books',
    'is_book': 'book'
}


def file_ext_to_icon(file):
    attr = next((x for x in file_ext_icon_dict.keys() if getattr(file, x)), None)
    return file_ext_icon_dict.get(attr, 'insert_drive_file')


register.filter('file_ext_to_icon', file_ext_to_icon)