from __future__ import annotations

from train_schedule_app.models.train_record import TrainRecord

#Сервис для постраничного разбаения списка записей и класс представляющий результат пагинации
class PaginationResult:
    def __init__(
        self,
        items: list[TrainRecord],
        page_number: int,
        page_size: int,
        total_items: int,
    ) -> None:
        self.items: list[TrainRecord] = items
        self.page_number: int = page_number
        self.page_size: int = page_size
        self.total_items: int = total_items

    @property
    def total_pages(self) -> int:
        if self.total_items == 0:
            return 1
        return (self.total_items + self.page_size - 1) // self.page_size


class PaginationService:
    def paginate(
        self,
        items: list[TrainRecord],
        page_number: int,
        page_size: int,
    ) -> PaginationResult:
        safe_page_size: int = max(1, page_size)
        total_items: int = len(items)
        total_pages: int = 1 if total_items == 0 else (total_items + safe_page_size - 1) // safe_page_size
        safe_page_number: int = min(max(1, page_number), total_pages)

        start_index: int = (safe_page_number - 1) * safe_page_size
        end_index: int = start_index + safe_page_size
        page_items: list[TrainRecord] = items[start_index:end_index]

        return PaginationResult(
            items=page_items,
            page_number=safe_page_number,
            page_size=safe_page_size,
            total_items=total_items,
        )
