from typing import Any

from src.core.schemas.template_schema import TemplateData
from src.frontend.menu.urls import menu_items, choice_from_menu

async def prepare_template(
        data:dict[str, Any], 
        additional_data:dict[str, Any] = None
        ):
    
    template_data = TemplateData(**data).model_dump(exclude_none=True)
    template_data.update(**additional_data)
    template_data.update({'menu':menu_items, 'menu_data':choice_from_menu})
    return template_data