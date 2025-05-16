from src.core.config.config import settings


prefix = settings.prefix.api_data.prefix
menu_items = [
    {'title':'Home', 'url':'/'},
    {'title':'Docs', 'url':'/docs'},
    {'title':'Registration',  'url': f'{prefix}/register'},
    {'title':'Login','url':f'{prefix}/login'},
    {'title':'Logout','url':f'{prefix}/logout'},
]

def get_menu():
    return [item for item in menu_items]


def choice_from_menu(name:str=None):
    if name:
        for i in menu_items:
            if name.lower() == i.get('title').lower() or name.lower() == i.get('url').lower():
                return i