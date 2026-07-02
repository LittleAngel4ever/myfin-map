from repo import DataRepo
from parser import Parser
from models_back import Link, Api_var
from datetime import date

USD = Link.USD
EUR = Link.EUR
RUB = Link.RUB
DAMP_FILE = "data_damp.txt"

def update_data(src: Link):
    data_repo = DataRepo()
    parser = Parser()
    bank_branches = parser.get_branch(src)
    for branch in bank_branches:
        data_repo.set_bank_branch(branch)
    return bank_branches

def date_check() -> bool:
    print('gg')
    try:
        with open(DAMP_FILE, "r", encoding="utf-8") as f:
            saved_date = f.read().strip()
        today = str(date.today())
        return saved_date == today
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"[WARNING] Ошибка чтения {DAMP_FILE}: {e}")
        return False

def set_update_date():
    try:
        with open(DAMP_FILE, "w", encoding="utf-8") as f:
            f.write(str(date.today()))
    except Exception as e:
        print(f"[WARNING] Не удалось записать дату в {DAMP_FILE}: {e}")

def get_data(type: Link):
    if date_check():
        repo = DataRepo()
        all_branches = repo.list_bank_branches()
        
        target_currency = type.name.lower().strip()
        has_currency_data = False
        
        for branch in all_branches:
            for rate in branch.exchange_rates:
                curr_from = rate.curr_from.value.strip().lower()
                curr_to = rate.curr_to.value.strip().lower()
                if curr_from == target_currency or curr_to == target_currency:
                    has_currency_data = True
                    break
            if has_currency_data:
                break
        
        if not has_currency_data:
            parser = Parser()
            new_branches = parser.get_branch(type)
            for branch in new_branches:
                repo.set_bank_branch(branch)
            all_branches = repo.list_bank_branches()
        
        return all_branches
    else:
        repo = DataRepo()
        repo.clear_database()
        parser = Parser()
        
        for currency in [Link.USD, Link.EUR, Link.RUB]:
            bank_branches = parser.get_branch(currency)
            for branch in bank_branches:
                repo.set_bank_branch(branch)
        
        set_update_date()
        return repo.list_bank_branches()

def get_card(type: Link):
    from cart import ExchangeMap
    map_builder = ExchangeMap(currency=type)
    map_builder.build()
    map_builder.save_and_open()

def get_best_locations(type: Link):
    branches = get_data(type)
    buy_rates = []
    sell_rates = []
    
    target_currency = type.name.lower().strip()
    
    for branch in branches:
        for rate in branch.exchange_rates:
            curr_from = rate.curr_from.value.strip()
            curr_to = rate.curr_to.value.strip()
            
            if curr_from == "byn" and curr_to == target_currency:
                buy_rates.append({"branch": branch, "rate": rate.rate})
            elif curr_from == target_currency and curr_to == "byn":
                sell_rates.append({"branch": branch, "rate": rate.rate})

    buy_rates.sort(key=lambda x: x["rate"])
    sell_rates.sort(key=lambda x: x["rate"], reverse=True)

    buy_top_5 = [item["branch"] for item in buy_rates[:5]]
    sell_top_5 = [item["branch"] for item in sell_rates[:5]]

    return {"buy": buy_top_5, "sell": sell_top_5}

def get_back(var: Api_var, type: Link):
    if var == Api_var.BOT:
        return get_best_locations(type)
    elif var == Api_var.CARD:
        return get_card(type)

def main():
    get_back(var=Api_var.CARD, type=Link.USD)

if __name__ == "__main__":
    main()