from __future__ import annotations

import re
import time
from typing import Any

from .incidents import STATE

PICKLEBALL_DOCS = {
    "mua": "Shop hỗ trợ thanh toán chuyển khoản, COD nội thành, và giao hàng toàn quốc.",
    "bán": "Chương trình thu cũ đổi mới áp dụng với vợt còn bảo hành và ngoại hình >= 80%.",
    "bảo hành": "Vợt được bảo hành 90 ngày cho lỗi kỹ thuật nhà sản xuất.",
    "đổi trả": "Đổi trả trong 7 ngày nếu chưa sử dụng và còn đủ tem nhãn.",
    "vận chuyển": "Miễn phí vận chuyển đơn từ 1.500.000 VND trong nội thành.",
}

PRODUCT_CATALOG: list[dict[str, Any]] = [
    {
        "sku": "PADDLE-J2K-14MM",
        "name": "J2K Carbon Paddle 14mm",
        "category": "vot",
        "price_vnd": 2590000,
        "stock": 12,
        "tags": ["j2k", "carbon", "14mm", "vot"],
    },
    {
        "sku": "PADDLE-HYPERION-C2",
        "name": "Hyperion C2 Elongated Paddle",
        "category": "vot",
        "price_vnd": 3390000,
        "stock": 7,
        "tags": ["hyperion", "elongated", "control", "vot"],
    },
    {
        "sku": "BALL-X40-3",
        "name": "Franklin X-40 Outdoor Ball (hop 3)",
        "category": "bong",
        "price_vnd": 149000,
        "stock": 45,
        "tags": ["x40", "outdoor", "bong"],
    },
    {
        "sku": "SHOE-COURTPRO-44",
        "name": "Court Pro Pickleball Shoes",
        "category": "giay",
        "price_vnd": 1890000,
        "stock": 16,
        "tags": ["giay", "court", "nam", "nu"],
    },
    {
        "sku": "BAG-TOUR-6",
        "name": "Tour Bag 6-Paddle",
        "category": "tui",
        "price_vnd": 890000,
        "stock": 20,
        "tags": ["tui", "bag", "phu kien"],
    },
]


def tool_search_price(query: str) -> list[dict[str, Any]]:
    lowered = query.lower()
    if STATE["tool_fail"]:
        raise RuntimeError("Công cụ tra giá tạm thời không khả dụng")

    tokens = set(re.findall(r"[a-z0-9\-]+", lowered))
    results: list[dict[str, Any]] = []
    for item in PRODUCT_CATALOG:
        haystack = {item["category"], item["sku"].lower(), *item["tags"], *item["name"].lower().split()}
        if tokens & haystack:
            results.append(item)

    if not results:
        # Trả về các sản phẩm phổ biến khi truy vấn quá chung chung.
        if any(keyword in lowered for keyword in ["giá", "gia", "price", "bao nhiêu", "bao nhieu", "pickleball", "vợt", "vot", "bóng", "bong"]):
            results = PRODUCT_CATALOG[:3]

    return results[:5]


def retrieve(message: str) -> list[str]:
    if STATE["rag_slow"]:
        time.sleep(2.5)

    lowered = message.lower()
    docs = [text for key, text in PICKLEBALL_DOCS.items() if key in lowered]

    if any(keyword in lowered for keyword in ["giá", "gia", "price", "bao nhiêu", "bao nhieu", "vợt", "vot", "bóng", "bong", "túi", "tui", "giày", "giay"]):
        price_hits = tool_search_price(message)
        if price_hits:
            formatted = []
            for item in price_hits:
                formatted.append(
                    f"{item['name']} ({item['sku']}): {item['price_vnd']:,} VND, tồn kho {item['stock']}"
                )
            docs.append("Bảng giá tìm được: " + " | ".join(formatted))

    if not docs:
        docs.append("Chưa tìm thấy tri thức đặc thù, hãy hỏi về giá, bảo hành, đổi trả hoặc vận chuyển.")

    return docs
