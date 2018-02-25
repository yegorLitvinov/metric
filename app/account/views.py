from sanic.response import json
from sanic import Blueprint

from app.conf import settings
from app.models import DoesNotExist

from . import session
from .models import User, encrypt_password

blueprint = Blueprint('account', url_prefix='/api/account')


def auth_required(coroutine):
    async def inner(request):
        user = await session.get_user(request)
        if not user:
            return json({}, 401)
        request['user'] = user
        return await coroutine(request)
    return inner


@blueprint.route('/login/', methods=['POST'])
async def login(request):
    if not request.json:
        return json({}, 400)
    email = request.json.get('email')
    password = request.json.get('password')
    if not (email and password):
        return json({}, 400)
    try:
        user = await User.get(
            is_active=True,
            email=email,
            password=encrypt_password(password),
        )
    except DoesNotExist:
        return json({}, 404)

    response = json({})
    if request.cookies.get(settings.SESSION_COOKIE_NAME):
        await session.delete_user(request, response)
    await session.set_user(user, response)

    return response


@blueprint.route('/check-auth/', methods=['POST'])
@auth_required
async def check_auth(request):
    return json({})


@blueprint.route('/logout/', methods=['POST'])
@auth_required
async def logout(request):
    response = json({}, 204)
    await session.delete_user(request, response)
    return response
