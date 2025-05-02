from typing import Any

from src.core.schemas.template_schema import TemplateData


async def prepare_template(
        data:dict[str, Any], 
        additional_data:dict[str, Any] = None
        ):
    
    template_data = TemplateData(**data).model_dump(exclude_none=True)
    template_data.update(**additional_data)
    return template_data