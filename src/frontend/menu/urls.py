from src.core.config.config import main_prefix


prefix = main_prefix
menu_items = [
    {'title':'Home', 'url':'/'},
    {'title':'Docs', 'url':'/docs'},
    {'title':'Registration',  'url': f'{prefix}/register'},
    {'title':'Login','url':f'{prefix}/login'},
    {'title':'Logout','url':f'{prefix}/logout'},
    {'title':'Chat Rooms', 'url':f'/rooms'},
    {'title':'Profile','url':f'{prefix}/profile'},
]

def get_menu():
    return [item for item in menu_items]


def choice_from_menu(name:str=None):
    if name:
        for i in menu_items:
            if name.lower() == i.get('title').lower() or name.lower() == i.get('url').lower():
                return i