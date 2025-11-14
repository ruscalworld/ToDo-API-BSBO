import asyncio

from sqlalchemy import text

from database import init_db, engine


async def test_connection():
    print(" Проверка подключения к PostgreSQL...")

    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(" Подключение успешно!")
            print(f" Результат тестового запроса: {result.scalar()}")

        print("\n Создание таблиц...")
        await init_db()

        print("\n ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print(" База данных готова к работе.")
    except Exception as e:
        print(f"\n ОШИБКА ПОДКЛЮЧЕНИЯ:")
        print(f" {e}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_connection())
