"""Простой тест для проверки загрузки базы данных"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'kurs_final', 'programs'))
os.chdir(os.path.join(os.path.dirname(__file__), 'kurs_final', 'programs'))

print("=" * 60)
print("ТЕСТ: Загрузка базы данных и данных")
print("=" * 60)

db_path = 'branch.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"✓ Старая база данных удалена")

print("\n[1] Тестирование DataRepo...")
from repo import DataRepo
repo = DataRepo(db_name="branch.db")
print("✓ DataRepo инициализирован")

print("\n[2] Тестирование моделей...")
from project.models_front import BankBranch, BankOrg, Coords, ExchangeRate, Currency
branch = BankBranch(
    bank_org=BankOrg(name="Test Bank"),
    address="Test Address",
    coords=Coords(lon=27.56, lat=53.90),
    exchange_rates=[
        ExchangeRate(curr_from=Currency.USD, curr_to=Currency.BYN, rate=3.5),
        ExchangeRate(curr_from=Currency.BYN, curr_to=Currency.USD, rate=0.28)
    ]
)
print("✓ Модели работают правильно")

print("\n[3] Тестирование set_bank_branch...")
repo.set_bank_branch(branch)
print("✓ Отделение сохранено в базу данных")

print("\n[4] Тестирование list_bank_branches...")
branches = repo.list_bank_branches()
print(f"✓ Получено {len(branches)} отделений")

print("\n[5] Тестирование get_branches_as_dataframe...")
df = repo.get_branches_as_dataframe()
print(f"✓ Экспортировано {len(df)} строк в DataFrame")
print(df)

print("\n" + "=" * 60)
print("ALL TESTS PASSED ✓")
print("=" * 60)
