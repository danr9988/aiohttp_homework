import logging
import aiosqlite
from aiohttp import web
from datetime import datetime

logging.basicConfig(level=logging.INFO)

db: aiosqlite.Connection | None = None


async def init_db():
    global db
    db = await aiosqlite.connect('ads.db')
    db.row_factory = aiosqlite.Row

    await db.execute('''
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL,
            owner TEXT NOT NULL
        )
    ''')
    await db.commit()
    logging.info("База данных инициализирована")


async def get_ads(request: web.Request) -> web.Response:
    async with db.execute('SELECT * FROM ads') as cursor:
        ads = await cursor.fetchall()

    ads_list = [dict(ad) for ad in ads]
    return web.json_response(ads_list)


async def create_ad(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        return web.json_response(
            {"error": "Некорректный JSON"},
            status=400
        )

    required_fields = ['title', 'description', 'owner']
    for field in required_fields:
        if field not in data or not data[field]:
            return web.json_response(
                {"error": f"Необходимо указать поле: {field}"},
                status=400
            )

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor = await db.execute(
        'INSERT INTO ads (title, description, created_at, owner) VALUES (?, ?, ?, ?)',
        (data['title'], data['description'], created_at, data['owner'])
    )
    await db.commit()

    ad_id = cursor.lastrowid
    async with db.execute('SELECT * FROM ads WHERE id = ?', (ad_id,)) as cursor:
        new_ad = await cursor.fetchone()

    return web.json_response(dict(new_ad), status=201)


async def get_ad(request: web.Request) -> web.Response:
    ad_id = int(request.match_info['id'])

    async with db.execute('SELECT * FROM ads WHERE id = ?', (ad_id,)) as cursor:
        ad = await cursor.fetchone()

    if ad is None:
        return web.json_response(
            {"error": "Объявление не найдено"},
            status=404
        )

    return web.json_response(dict(ad))


async def update_ad(request: web.Request) -> web.Response:
    ad_id = int(request.match_info['id'])

    async with db.execute('SELECT * FROM ads WHERE id = ?', (ad_id,)) as cursor:
        ad = await cursor.fetchone()

    if ad is None:
        return web.json_response(
            {"error": "Объявление не найдено"},
            status=404
        )

    try:
        data = await request.json()
    except Exception:
        return web.json_response(
            {"error": "Некорректный JSON"},
            status=400
        )

    if 'title' not in data or not data['title']:
        return web.json_response(
            {"error": "Поле title обязательно для обновления"},
            status=400
        )

    if 'description' not in data or not data['description']:
        return web.json_response(
            {"error": "Поле description обязательно для обновления"},
            status=400
        )

    owner = data.get('owner', ad['owner'])

    await db.execute(
        'UPDATE ads SET title = ?, description = ?, owner = ? WHERE id = ?',
        (data['title'], data['description'], owner, ad_id)
    )
    await db.commit()

    async with db.execute('SELECT * FROM ads WHERE id = ?', (ad_id,)) as cursor:
        updated_ad = await cursor.fetchone()

    return web.json_response(dict(updated_ad))


async def delete_ad(request: web.Request) -> web.Response:
    ad_id = int(request.match_info['id'])

    async with db.execute('SELECT * FROM ads WHERE id = ?', (ad_id,)) as cursor:
        ad = await cursor.fetchone()

    if ad is None:
        return web.json_response(
            {"error": "Объявление не найдено"},
            status=404
        )

    await db.execute('DELETE FROM ads WHERE id = ?', (ad_id,))
    await db.commit()

    return web.json_response({"message": "Объявление успешно удалено"})


async def cleanup_app(app: web.Application):
    if db:
        await db.close()
        logging.info("Подключение к БД закрыто")


def init_app() -> web.Application:
    app = web.Application()

    app.router.add_get('/ads', get_ads)
    app.router.add_post('/ads', create_ad)
    app.router.add_get('/ads/{id}', get_ad)
    app.router.add_put('/ads/{id}', update_ad)
    app.router.add_delete('/ads/{id}', delete_ad)

    app.on_startup.append(lambda app: init_db())
    app.on_cleanup.append(cleanup_app)

    return app


if __name__ == '__main__':
    logging.info("Запуск сервера на http://127.0.0.1:8080")
    web.run_app(init_app(), host='127.0.0.1', port=8080)