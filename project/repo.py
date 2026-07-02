import os
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from models_back import (
    Currency, Coords, BankOrg, BankBranch, ExchangeRate
)

Base = declarative_base()

class DBBankBranch(Base):
    __tablename__ = 'bank_branches'
    id = Column(Integer, primary_key=True)
    bank_org = Column(String, nullable=False)
    address = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    rates = relationship("DBExchangeRate", back_populates="branch", cascade="all, delete-orphan")

class DBExchangeRate(Base):
    __tablename__ = 'exchange_rates'
    id = Column(Integer, primary_key=True, autoincrement=True)
    branch_id = Column(Integer, ForeignKey('bank_branches.id'), nullable=False)
    curr_from = Column(String, nullable=False)
    curr_to = Column(String, nullable=False)
    rate = Column(Float, nullable=False)
    branch = relationship("DBBankBranch", back_populates="rates")

class DataRepo:
    def __init__(self, db_name: str = "branch.db"):
        self.db_name = db_name
        
        # Формируем путь к БД строго в папку instance/
        base_dir = os.path.abspath(os.path.dirname(__file__))
        instance_dir = os.path.join(base_dir, 'instance')
        os.makedirs(instance_dir, exist_ok=True)
        
        db_path = os.path.join(instance_dir, db_name).replace(os.sep, '/')
        self.db_url = f"sqlite:///{db_path}"

        self._init_db()
        self.Session = sessionmaker(bind=self.engine)

    def _init_db(self):
        self.engine = create_engine(self.db_url, echo=False)
        Base.metadata.create_all(self.engine)

    def _to_domain_model(self, db_branch: DBBankBranch) -> BankBranch:
        exchange_rates = [
            ExchangeRate(
                curr_from=Currency(r.curr_from),
                curr_to=Currency(r.curr_to),
                rate=r.rate
            )
            for r in db_branch.rates
        ]
        return BankBranch(
            bank_org=BankOrg(db_branch.bank_org),
            address=db_branch.address,
            coords=Coords(lon=db_branch.lon, lat=db_branch.lat),
            exchange_rates=exchange_rates
        )

    def set_bank_branch(self, bank_branch: BankBranch) -> BankBranch:
        with self.Session() as session:
            existing = session.query(DBBankBranch).filter_by(id=bank_branch.id).first()
            if existing:
                return self.update_bank_branche_rates(bank_branch.id, bank_branch.exchange_rates)

            new_branch = DBBankBranch(
                id=bank_branch.id,
                bank_org=bank_branch.bank_org.value if hasattr(bank_branch.bank_org, 'value') else bank_branch.bank_org.name,
                address=bank_branch.address,
                lat=bank_branch.coords.lat,
                lon=bank_branch.coords.lon
            )
            for r in bank_branch.exchange_rates:
                new_rate = DBExchangeRate(
                    curr_from=r.curr_from.value,
                    curr_to=r.curr_to.value,
                    rate=r.rate
                )
                new_branch.rates.append(new_rate)

            session.add(new_branch)
            session.commit()
        return bank_branch

    def get_bank_branch(self, id: int) -> BankBranch | None:
        with self.Session() as session:
            db_branch = session.query(DBBankBranch).filter_by(id=id).first()
            if not db_branch:
                return None
            return self._to_domain_model(db_branch)

    def list_bank_branches(self, curr_from: Currency | None = None, curr_to: Currency | None = None) -> list[BankBranch]:
        with self.Session() as session:
            query = session.query(DBBankBranch)
            if curr_from:
                query = query.filter(DBBankBranch.rates.any(curr_from=curr_from.value))
            if curr_to:
                query = query.filter(DBBankBranch.rates.any(curr_to=curr_to.value))
            db_branches = query.all()
            return [self._to_domain_model(b) for b in db_branches]

    def update_bank_branche_rates(self, id: int, rates: list[ExchangeRate]) -> BankBranch:
        with self.Session() as session:
            db_branch = session.query(DBBankBranch).filter_by(id=id).first()
            if not db_branch:
                raise ValueError(f"BankBranch with id={id} not found")
            
            # Проходим по новым курсам, которые пришли из парсера
            for r in rates:
                # Ищем, есть ли уже такой курс в этом отделении
                existing_rate = next((old_r for old_r in db_branch.rates 
                                      if old_r.curr_from == r.curr_from.value 
                                      and old_r.curr_to == r.curr_to.value), None)
                if existing_rate:
                    # Если есть - просто обновляем значение
                    existing_rate.rate = r.rate
                else:
                    # Если нет - добавляем новый курс, не трогая другие валюты
                    db_branch.rates.append(
                        DBExchangeRate(curr_from=r.curr_from.value, curr_to=r.curr_to.value, rate=r.rate)
                    )
                    
            session.commit()
            session.refresh(db_branch)
            return self._to_domain_model(db_branch)


    def delete_bank_branch(self, id: int) -> bool:
        with self.Session() as session:
            db_branch = session.query(DBBankBranch).filter_by(id=id).first()
            if not db_branch:
                return False
            session.delete(db_branch)
            session.commit()
            return True

    def clear_database(self):
        with self.Session() as session:
            try:
                session.query(DBBankBranch).delete()
                session.query(DBExchangeRate).delete()
                session.commit()
                print("База данных успешно очищена (структура сохранена).")
            except Exception as e:
                session.rollback()
                print(f"Ошибка при очистке базы данных: {e}")
                raise e

if __name__ == '__main__':
    repo = DataRepo(db_name="branch.db")
    ans = repo.list_bank_branches()
    for i in ans:
        print(i)