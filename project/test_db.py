import os
import sys

db_path = os.path.join(os.path.dirname(__file__), 'branch.db')
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"[OK] Старая база данных удалена: {db_path}")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'kurs_final', 'programs'))
os.chdir(os.path.join(os.path.dirname(__file__), 'kurs_final', 'programs'))

print("\n[ТЕСТ] Запуск cart.py...")
try:
    from cart import ExchangeMap
    map_builder = ExchangeMap()
    map_builder.build()
    print("[OK] cart.py успешно завершен")
except Exception as e:
    print(f"[ОШИБКА] cart.py не выполнен: {e}")
    import traceback
    traceback.print_exc()
