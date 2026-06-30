from pydantic import BaseModel
from typing import List, Optional


class TopProduct(BaseModel):
    product: str
    count: int


class ChannelActivity(BaseModel):
    date: str
    message_count: int


class MessageSearchResult(BaseModel):
    message_id: str
    channel_name: str
    message: str
    date: str


class VisualContentStats(BaseModel):
    channel_name: str
    total_images: int
    promotional: int
    product_display: int
    lifestyle: int
    other: int
