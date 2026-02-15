"""Обробники експорту"""
import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery

from keyboards import export_menu_kb
from reports import export_to_csv, export_to_excel

logger = logging.getLogger(__name__)
router = Router(name="export")


@router.callback_query(F.data == "export")
async def show_export(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "Експорт даних\n\nОберіть формат для експорту:",
        parse_mode="HTML",
        reply_markup=export_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "export_excel")
async def export_excel_handler(callback: CallbackQuery) -> None:
    await callback.answer("Генерую файл...")
    try:
        excel_file = await export_to_excel(callback.from_user.id)
        if excel_file:
            excel_file.seek(0)
            doc = BufferedInputFile(
                excel_file.read(),
                filename=f"finance_{datetime.now().strftime('%Y%m%d')}.xlsx",
            )
            await callback.message.answer_document(
                document=doc,
                caption="Ваші фінансові дані в форматі Excel",
                reply_markup=export_menu_kb(),
            )
        else:
            await callback.message.answer(
                "Немає даних для експорту.\nДодайте транзакції, щоб експортувати дані.",
                reply_markup=export_menu_kb(),
            )
    except Exception as e:
        logger.error("Помилка експорту в Excel: %s", e)
        await callback.message.answer(
            "Помилка експорту даних. Спробуйте пізніше.",
            reply_markup=export_menu_kb(),
        )


@router.callback_query(F.data == "export_csv")
async def export_csv_handler(callback: CallbackQuery) -> None:
    await callback.answer("Генерую файл...")
    try:
        csv_file = await export_to_csv(callback.from_user.id)
        if csv_file:
            csv_file.seek(0)
            doc = BufferedInputFile(
                csv_file.read(),
                filename=f"finance_{datetime.now().strftime('%Y%m%d')}.csv",
            )
            await callback.message.answer_document(
                document=doc,
                caption="Ваші фінансові дані в форматі CSV",
                reply_markup=export_menu_kb(),
            )
        else:
            await callback.message.answer(
                "Немає даних для експорту.\nДодайте транзакції, щоб експортувати дані.",
                reply_markup=export_menu_kb(),
            )
    except Exception as e:
        logger.error("Помилка експорту в CSV: %s", e)
        await callback.message.answer(
            "Помилка експорту даних. Спробуйте пізніше.",
            reply_markup=export_menu_kb(),
        )
