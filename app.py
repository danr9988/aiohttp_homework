import logging
from aiohttp import web
from datetime import datetime

logging.basicConfig(level=logging.INFO)

ads_list: list[dict] = []
current_id: int = 1


async def get_ads(request: web.Request) -> web.Response:
    return web.json_response(ads_list)


async def create_ad(request: web.Request) -> web.Response:
    global current_id

    try:
        data = await request.json()
    except Exception:
        return web.json_response(
            {"error": "Некорректный JSON"},
            status=400
        )

    required_fields = ['title', 'description', 'owner']
    for field in required_fields:
        if field not in data:
            return web.json_response(
                {"error": f"Необходимо указать поле: {field}"},
                status=400
            )

    new_ad = {
        "id": current_id,
        "title": data['title'],
        "description": data['description'],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "owner": data['owner']
    }

    ads_list.append(new_ad)
    current_id += 1

    return web.json_response(new_ad, status=201)


async def get_ad(request: web.Request) -> web.Response:
    ad_id = int(request.match_info['id'])

    ad = next((item for item in ads_list if item["id"] == ad_id), None)

    if ad is None:
        return web.json_response(
            {"error": "Объявление не найдено"},
            status=404
        )

    return web.json_response(ad)


async def update_ad(request: web.Request) -> web.Response:
    ad_id = int(request.match_info['id'])

    ad = next((item for item in ads_list if item["id"] == ad_id), None)

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

    if 'title' in data:
        ad['title'] = data['title']
    if 'description' in data:
        ad['description'] = data['description']
    if 'owner' in data:
        ad['owner'] = data['owner']

    return web.json_response(ad)


async def delete_ad(request: web.Request) -> web.Response:
    global ads_list

    ad_id = int(request.match_info['id'])

    ad = next((item for item in ads_list if item["id"] == ad_id), None)
    if ad is None:
        return web.json_response(
            {"error": "Объявление не найдено"},
            status=404
        )

    ads_list = [item for item in ads_list if item["id"] != ad_id]

    return web.json_response({"message": "Объявление успешно удалено"})


def init_app() -> web.Application:
    app = web.Application()

    app.router.add_get('/ads', get_ads)
    app.router.add_post('/ads', create_ad)
    app.router.add_get('/ads/{id}', get_ad)
    app.router.add_put('/ads/{id}', update_ad)
    app.router.add_delete('/ads/{id}', delete_ad)

    return app


if __name__ == '__main__':
    logging.info("Запуск сервера на http://127.0.0.1:8080")
    web.run_app(init_app(), host='127.0.0.1', port=8080)