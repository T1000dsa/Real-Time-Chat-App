from pydantic import BaseModel, Field
from fastapi import Request
from typing import Optional, Dict, Any

class TemplateData(BaseModel):
    title: Optional[str] = Field(default=None, description="Page title")
    content: Optional[str] = Field(default=None, description="Main content")
    description: Optional[str] = Field(default=None, description="Additional description")
    menu: Optional[dict] = Field(default=None, description="Navigation menu data")
    data: Optional[dict] = Field(default=None, description="Additional dynamic data")
    form_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Form's data")
    template_action:Optional[str] = Field(default=None, description="Teplate's action (endpoint's url)")
    errors:Optional[str] = Field(default=None, description="Error's data")